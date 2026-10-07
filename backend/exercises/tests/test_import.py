import copy
import json
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from exercises.models import (
    DropdownItem,
    DropdownOption,
    DropdownPart,
    Exercise,
    GapFillGap,
    GapFillItem,
    MultipleChoiceItem,
    MultipleChoiceOption,
    SentenceBuilderItem,
    SentenceBuilderToken,
    Topic,
    VocabularyItem,
)
from exercises.services.exercise_import import (
    ExerciseImportService,
    ExerciseImportValidationError,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent / "schemas" / "test_exercises.json"
)


class ExerciseImportServiceTest(TestCase):
    def setUp(self):
        self.service = ExerciseImportService()

        with FIXTURE_PATH.open("r", encoding="utf-8") as file:
            self.data = json.load(file)

    # ------------------------------------------------------------------
    # JSON loading
    # ------------------------------------------------------------------

    def test_load_json_from_path(self):
        data = self.service.load_json(FIXTURE_PATH)

        self.assertEqual(data["version"], 1)
        self.assertEqual(data["language"], "german")
        self.assertEqual(len(data["exercises"]), 5)

    def test_load_json_from_file_like_object(self):
        import io

        source = io.StringIO(json.dumps(self.data, ensure_ascii=False))

        data = self.service.load_json(source)

        self.assertEqual(data, self.data)

    def test_load_json_rejects_invalid_json(self):
        with self.assertRaises(ExerciseImportValidationError) as context:
            self.service.load_json("{ invalid json")

        self.assertEqual(len(context.exception.errors), 1)
        self.assertEqual(context.exception.errors[0]["path"], "file")
        self.assertIn("Некорректный JSON", context.exception.errors[0]["message"])

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    def test_valid_fixture_passes_schema_validation(self):
        errors = self.service.validate_schema(self.data)

        self.assertEqual(errors, [])

    def test_valid_fixture_passes_full_validation(self):
        errors = self.service.validate(self.data)

        self.assertEqual(errors, [])

    def test_preview_of_valid_fixture(self):
        preview = self.service.preview(self.data)

        self.assertTrue(preview["valid"])
        self.assertEqual(preview["errors"], [])

        summary = preview["summary"]

        self.assertEqual(summary["version"], 1)
        self.assertEqual(summary["language"], "german")
        self.assertEqual(summary["exercise_count"], 5)

        self.assertEqual(
            summary["by_type"],
            {
                "vocabulary_drill": 1,
                "multiple_choice": 1,
                "dropdown": 1,
                "gap_fill": 1,
                "sentence_builder": 1,
            },
        )

        self.assertEqual(
            summary["topics"],
            [
                "Alltag",
                "Essen und Trinken",
                "Grammatik",
                "Präsens",
                "Satzbau",
            ],
        )

    def test_schema_validation_rejects_missing_required_field(self):
        invalid_data = copy.deepcopy(self.data)
        del invalid_data["exercises"][0]["title"]

        errors = self.service.validate_schema(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                error["path"] == "exercises[0]" and "title" in error["message"]
                for error in errors
            )
        )

    def test_schema_validation_rejects_unknown_exercise_type(self):
        invalid_data = copy.deepcopy(self.data)
        invalid_data["exercises"][0]["type"] = "unknown_type"

        errors = self.service.validate_schema(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(any(error["path"] == "exercises[0].type" for error in errors))

    def test_preview_reports_validation_errors(self):
        invalid_data = copy.deepcopy(self.data)
        invalid_data["exercises"][0]["title"] = ""

        preview = self.service.preview(invalid_data)

        self.assertFalse(preview["valid"])
        self.assertTrue(preview["errors"])
        self.assertEqual(preview["summary"]["exercise_count"], 0)
        self.assertEqual(preview["summary"]["by_type"], {})
        self.assertEqual(preview["summary"]["topics"], [])

    # ------------------------------------------------------------------
    # Business validation
    # ------------------------------------------------------------------

    def test_business_validation_rejects_duplicate_exercise(self):
        invalid_data = copy.deepcopy(self.data)
        duplicate = copy.deepcopy(invalid_data["exercises"][0])
        invalid_data["exercises"].append(duplicate)

        errors = self.service.validate_business_rules(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                error["path"] == "exercises[5]"
                and "Дублирующееся упражнение" in error["message"]
                for error in errors
            )
        )

    def test_business_validation_rejects_duplicate_vocabulary_word(self):
        invalid_data = copy.deepcopy(self.data)

        items = invalid_data["exercises"][0]["data"]["items"]
        items[1]["word"] = items[0]["word"]

        errors = self.service.validate_business_rules(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                error["path"] == "exercises[0].data.items[1].word"
                and "уже используется" in error["message"]
                for error in errors
            )
        )

    def test_business_validation_rejects_duplicate_vocabulary_answer(self):
        invalid_data = copy.deepcopy(self.data)

        item = invalid_data["exercises"][0]["data"]["items"][0]
        item["distractors"][0] = item["correct"]

        errors = self.service.validate_business_rules(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                error["path"] == "exercises[0].data.items[0].distractors"
                and "должны быть уникальными" in error["message"]
                for error in errors
            )
        )

    def test_business_validation_rejects_invalid_multiple_choice(self):
        invalid_data = copy.deepcopy(self.data)

        item = invalid_data["exercises"][1]["data"]["items"][0]

        for option in item["options"]:
            option["correct"] = False

        errors = self.service.validate_business_rules(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                error["path"] == "exercises[1].data.items[0].options"
                and "ровно один" in error["message"]
                for error in errors
            )
        )

    def test_business_validation_rejects_duplicate_multiple_choice_option(self):
        invalid_data = copy.deepcopy(self.data)

        options = invalid_data["exercises"][1]["data"]["items"][0]["options"]
        options[1]["text"] = options[0]["text"]

        errors = self.service.validate_business_rules(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                error["path"] == "exercises[1].data.items[0].options"
                and "не должны повторяться" in error["message"]
                for error in errors
            )
        )

    def test_business_validation_rejects_invalid_dropdown(self):
        invalid_data = copy.deepcopy(self.data)

        select_part = next(
            part
            for part in invalid_data["exercises"][2]["data"]["items"][0]["parts"]
            if part["type"] == "select"
        )

        for option in select_part["options"]:
            option["correct"] = False

        errors = self.service.validate_business_rules(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any("ровно один правильный вариант" in error["message"] for error in errors)
        )

    def test_business_validation_rejects_duplicate_dropdown_option(self):
        invalid_data = copy.deepcopy(self.data)

        select_part = next(
            part
            for part in invalid_data["exercises"][2]["data"]["items"][0]["parts"]
            if part["type"] == "select"
        )

        select_part["options"][1]["text"] = select_part["options"][0]["text"]

        errors = self.service.validate_business_rules(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                "Варианты dropdown не должны повторяться" in error["message"]
                for error in errors
            )
        )

    def test_business_validation_rejects_duplicate_gap_placeholder(self):
        invalid_data = copy.deepcopy(self.data)

        item = invalid_data["exercises"][3]["data"]["items"][0]

        item["text"] = "Ich {{gap1}} {{gap2}} Deutsch."

        item["gaps"].append(
            {
                "placeholder": "{{gap1}}",
                "correct": "lerne",
            }
        )

        errors = self.service.validate_business_rules(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                error["path"] == "exercises[3].data.items[0].gaps"
                and "уникальным" in error["message"]
                for error in errors
            )
        )

    def test_business_validation_rejects_missing_gap_placeholder(self):
        invalid_data = copy.deepcopy(self.data)

        gap = invalid_data["exercises"][3]["data"]["items"][0]["gaps"][0]
        gap["placeholder"] = "__missing__"

        errors = self.service.validate_business_rules(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                "__missing__" in error["message"] and "не найден" in error["message"]
                for error in errors
            )
        )

    def test_business_validation_rejects_invalid_sentence_positions(self):
        invalid_data = copy.deepcopy(self.data)

        tokens = invalid_data["exercises"][4]["data"]["items"][0]["tokens"]
        tokens[0]["position"] = tokens[1]["position"]

        errors = self.service.validate_business_rules(invalid_data)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                error["path"] == "exercises[4].data.items[0].tokens"
                and "последовательность" in error["message"]
                for error in errors
            )
        )

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def test_valid_fixture_imports_all_five_exercise_types(self):
        result = self.service.import_exercises(self.data)

        self.assertEqual(result["created_count"], 5)
        self.assertEqual(len(result["exercise_ids"]), 5)

        self.assertEqual(Exercise.objects.count(), 5)

        self.assertEqual(
            set(Exercise.objects.values_list("exercise_type", flat=True)),
            {
                "vocabulary_drill",
                "multiple_choice",
                "dropdown",
                "gap_fill",
                "sentence_builder",
            },
        )

    def test_import_creates_expected_topic_count(self):
        self.service.import_exercises(self.data)

        self.assertEqual(Topic.objects.count(), 5)

        self.assertEqual(
            set(Topic.objects.values_list("name", flat=True)),
            {
                "Alltag",
                "Grammatik",
                "Essen und Trinken",
                "Präsens",
                "Satzbau",
            },
        )

    def test_import_maps_vocabulary_fields_correctly(self):
        result = self.service.import_exercises(self.data)

        exercise = Exercise.objects.get(id=result["exercise_ids"][0])

        self.assertEqual(exercise.exercise_type, "vocabulary_drill")
        self.assertEqual(exercise.title, "Alltag – Wörter")
        self.assertEqual(exercise.language, "german")
        self.assertEqual(exercise.level, "A1")
        self.assertTrue(exercise.is_active)
        self.assertEqual(exercise.order, 1)

        items = list(VocabularyItem.objects.filter(exercise=exercise).order_by("order"))

        self.assertEqual(len(items), 3)

        source_item = self.data["exercises"][0]["data"]["items"][0]

        self.assertEqual(items[0].prompt, source_item["word"])
        self.assertEqual(items[0].correct_answer, source_item["correct"])
        self.assertEqual(
            items[0].distractor_1,
            source_item["distractors"][0],
        )
        self.assertEqual(
            items[0].distractor_2,
            source_item["distractors"][1],
        )
        self.assertEqual(
            items[0].distractor_3,
            source_item["distractors"][2],
        )

    def test_import_maps_multiple_choice_fields_correctly(self):
        result = self.service.import_exercises(self.data)

        exercise = Exercise.objects.get(id=result["exercise_ids"][1])

        self.assertEqual(
            MultipleChoiceItem.objects.filter(exercise=exercise).count(),
            2,
        )

        first_item = MultipleChoiceItem.objects.get(
            exercise=exercise,
            order=0,
        )

        source_item = self.data["exercises"][1]["data"]["items"][0]

        self.assertEqual(first_item.question, source_item["question"])
        self.assertEqual(
            first_item.selection_mode,
            source_item["selection_mode"],
        )

        options = list(
            first_item.options.order_by("order").values(
                "text",
                "is_correct",
                "order",
            )
        )

        expected_options = [
            {
                "text": option["text"],
                "is_correct": option["correct"],
                "order": index,
            }
            for index, option in enumerate(source_item["options"])
        ]

        self.assertEqual(options, expected_options)

    def test_import_maps_dropdown_fields_correctly(self):
        result = self.service.import_exercises(self.data)

        exercise = Exercise.objects.get(id=result["exercise_ids"][2])

        dropdown_item = DropdownItem.objects.get(
            exercise=exercise,
            order=0,
        )

        parts = list(dropdown_item.parts.order_by("order"))

        self.assertEqual(len(parts), 5)

        source_parts = self.data["exercises"][2]["data"]["items"][0]["parts"]

        for actual, expected in zip(parts, source_parts):
            self.assertEqual(actual.part_type, expected["type"])
            self.assertEqual(actual.text, expected.get("text", ""))

            if expected["type"] == "select":
                actual_options = list(
                    actual.options.order_by("order").values(
                        "text",
                        "is_correct",
                        "order",
                    )
                )

                expected_options = [
                    {
                        "text": option["text"],
                        "is_correct": option["correct"],
                        "order": index,
                    }
                    for index, option in enumerate(expected["options"])
                ]

                self.assertEqual(actual_options, expected_options)
            else:
                self.assertEqual(actual.options.count(), 0)

    def test_import_maps_gap_fill_fields_correctly(self):
        result = self.service.import_exercises(self.data)

        exercise = Exercise.objects.get(id=result["exercise_ids"][3])

        items = list(GapFillItem.objects.filter(exercise=exercise).order_by("order"))

        self.assertEqual(len(items), 2)

        source_items = self.data["exercises"][3]["data"]["items"]

        for actual_item, expected_item in zip(items, source_items):
            self.assertEqual(actual_item.text, expected_item["text"])

            actual_gaps = list(
                actual_item.gaps.order_by("order").values(
                    "placeholder",
                    "correct_answer",
                    "order",
                )
            )

            expected_gaps = [
                {
                    "placeholder": gap["placeholder"],
                    "correct_answer": gap["correct"],
                    "order": index,
                }
                for index, gap in enumerate(expected_item["gaps"])
            ]

            self.assertEqual(actual_gaps, expected_gaps)

    def test_import_maps_sentence_builder_fields_correctly(self):
        result = self.service.import_exercises(self.data)

        exercise = Exercise.objects.get(id=result["exercise_ids"][4])

        items = list(
            SentenceBuilderItem.objects.filter(exercise=exercise).order_by("order")
        )

        self.assertEqual(len(items), 2)

        source_items = self.data["exercises"][4]["data"]["items"]

        for actual_item, expected_item in zip(items, source_items):
            actual_tokens = list(
                actual_item.tokens.order_by("order").values(
                    "text",
                    "correct_position",
                    "order",
                )
            )

            expected_tokens = [
                {
                    "text": token["text"],
                    "correct_position": token["position"],
                    "order": index,
                }
                for index, token in enumerate(expected_item["tokens"])
            ]

            self.assertEqual(actual_tokens, expected_tokens)

    def test_import_assigns_topics_to_exercises(self):
        result = self.service.import_exercises(self.data)

        exercise = Exercise.objects.get(id=result["exercise_ids"][3])

        self.assertEqual(
            set(exercise.topics.values_list("name", flat=True)),
            {"Grammatik", "Präsens"},
        )

    def test_import_respects_explicit_order(self):
        self.service.import_exercises(self.data)

        orders = list(
            Exercise.objects.order_by("order").values_list(
                "title",
                "order",
            )
        )

        self.assertEqual(
            orders,
            [
                ("Alltag – Wörter", 1),
                ("Sein oder haben?", 2),
                ("Im Café", 3),
                ("Lückentext – Präsens", 4),
                ("Satz bilden", 5),
            ],
        )

    # ------------------------------------------------------------------
    # Error handling and atomicity
    # ------------------------------------------------------------------

    def test_failed_validation_never_writes_to_database(self):
        invalid_data = copy.deepcopy(self.data)

        invalid_data["exercises"][0]["data"]["items"][1]["word"] = invalid_data[
            "exercises"
        ][0]["data"]["items"][0]["word"]

        with self.assertRaises(ExerciseImportValidationError):
            self.service.import_exercises(invalid_data)

        self.assertEqual(Exercise.objects.count(), 0)
        self.assertEqual(Topic.objects.count(), 0)

    def test_import_is_atomic_when_database_write_fails(self):
        original_create = Exercise.objects.create
        call_count = 0

        def failing_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 2:
                raise RuntimeError("Simulated database failure")

            return original_create(*args, **kwargs)

        with patch.object(
            Exercise.objects,
            "create",
            side_effect=failing_create,
        ):
            with self.assertRaises(RuntimeError):
                self.service.import_exercises(self.data)

        self.assertEqual(Exercise.objects.count(), 0)
        self.assertEqual(Topic.objects.count(), 0)
        self.assertEqual(VocabularyItem.objects.count(), 0)
        self.assertEqual(MultipleChoiceItem.objects.count(), 0)
        self.assertEqual(MultipleChoiceOption.objects.count(), 0)
        self.assertEqual(DropdownItem.objects.count(), 0)
        self.assertEqual(DropdownPart.objects.count(), 0)
        self.assertEqual(DropdownOption.objects.count(), 0)
        self.assertEqual(GapFillItem.objects.count(), 0)
        self.assertEqual(GapFillGap.objects.count(), 0)
        self.assertEqual(SentenceBuilderItem.objects.count(), 0)
        self.assertEqual(SentenceBuilderToken.objects.count(), 0)

    def test_import_is_append_only(self):
        first_result = self.service.import_exercises(self.data)
        second_result = self.service.import_exercises(self.data)

        self.assertEqual(first_result["created_count"], 5)
        self.assertEqual(second_result["created_count"], 5)

        self.assertEqual(Exercise.objects.count(), 10)
        self.assertEqual(Topic.objects.count(), 5)
        self.assertEqual(VocabularyItem.objects.count(), 6)
        self.assertEqual(MultipleChoiceItem.objects.count(), 4)
        self.assertEqual(MultipleChoiceOption.objects.count(), 16)
        self.assertEqual(DropdownItem.objects.count(), 2)
        self.assertEqual(DropdownPart.objects.count(), 10)
        self.assertEqual(DropdownOption.objects.count(), 12)
        self.assertEqual(GapFillItem.objects.count(), 4)
        self.assertEqual(GapFillGap.objects.count(), 4)
        self.assertEqual(SentenceBuilderItem.objects.count(), 4)
        self.assertEqual(SentenceBuilderToken.objects.count(), 16)
