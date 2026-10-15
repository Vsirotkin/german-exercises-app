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
from exercises.serializers import (
    DropdownItemSerializer,
    GapFillItemSerializer,
    MultipleChoiceItemSerializer,
    SentenceBuilderItemSerializer,
    VocabularyItemSerializer,
)
from exercises.services.evaluator import evaluate_exercise


class ExerciseEvaluatorTestCase(TestCase):
    """Contract tests for backend evaluation of all five exercise types."""

    def setUp(self):
        self.topic = Topic.objects.create(name="Evaluator tests")

    def create_exercise(self, exercise_type):
        exercise = Exercise.objects.create(
            title=f"Test {exercise_type}",
            exercise_type=exercise_type,
            language="german",
            level="A1",
            is_active=True,
        )
        exercise.topics.add(self.topic)
        return exercise

    def assert_evaluation(self, result, score, max_score, percentage):
        self.assertEqual(result["score"], score)
        self.assertEqual(result["max_score"], max_score)
        self.assertAlmostEqual(result["percentage"], percentage)

    def assert_safe_result_items(self, result):
        """Canonical answer keys must never appear in evaluation results."""
        forbidden_keys = {
            "correct_answer",
            "correct_answers",
            "is_correct_option",
            "correct_option_id",
            "correct_option_ids",
            "correct_values",
            "answer_key",
        }

        for item_result in result["results"]:
            self.assertIn("item_id", item_result)
            self.assertIn("is_correct", item_result)
            self.assertIn("score", item_result)
            self.assertIn("max_score", item_result)
            self.assertIn("feedback", item_result)

            self.assertIsInstance(item_result["is_correct"], bool)
            self.assertIsInstance(item_result["feedback"], str)

            self.assertFalse(
                forbidden_keys.intersection(item_result.keys()),
                msg=f"Canonical answer data leaked: {item_result}",
            )

    def test_vocabulary_drill_accepts_correct_stable_option_id(self):
        exercise = self.create_exercise("vocabulary_drill")
        item = VocabularyItem.objects.create(
            exercise=exercise,
            prompt="der Arzt",
            correct_answer="врач",
            distractor_1="аптекарь",
            distractor_2="пациент",
            distractor_3="медсестра",
        )

        serialized = VocabularyItemSerializer(item).data
        serialized_again = VocabularyItemSerializer(item).data

        ids_by_text = {
            option["text"]: option["id"]
            for option in serialized["options"]
        }
        ids_by_text_again = {
            option["text"]: option["id"]
            for option in serialized_again["options"]
        }

        self.assertEqual(ids_by_text, ids_by_text_again)

        correct_option_id = ids_by_text[item.correct_answer]
        result = evaluate_exercise(
            exercise,
            [{"item_id": item.id, "answer": correct_option_id}],
        )

        self.assert_evaluation(result, 1, 1, 100)
        self.assert_safe_result_items(result)
        self.assertTrue(result["results"][0]["is_correct"])

    def test_vocabulary_drill_rejects_wrong_stable_option_id(self):
        exercise = self.create_exercise("vocabulary_drill")
        item = VocabularyItem.objects.create(
            exercise=exercise,
            prompt="der Arzt",
            correct_answer="врач",
            distractor_1="аптекарь",
            distractor_2="пациент",
            distractor_3="медсестра",
        )

        serialized = VocabularyItemSerializer(item).data
        wrong_option = next(
            option
            for option in serialized["options"]
            if option["text"] == item.distractor_1
        )

        result = evaluate_exercise(
            exercise,
            [{"item_id": item.id, "answer": wrong_option["id"]}],
        )

        self.assert_evaluation(result, 0, 1, 0)
        self.assertFalse(result["results"][0]["is_correct"])
        self.assert_safe_result_items(result)

    def test_vocabulary_drill_does_not_accept_option_letter_as_id(self):
        exercise = self.create_exercise("vocabulary_drill")
        item = VocabularyItem.objects.create(
            exercise=exercise,
            prompt="der Arzt",
            correct_answer="врач",
            distractor_1="аптекарь",
            distractor_2="пациент",
            distractor_3="медсестра",
        )

        result = evaluate_exercise(
            exercise,
            [{"item_id": item.id, "answer": "a"}],
        )

        self.assert_evaluation(result, 0, 1, 0)

    def test_multiple_choice_single_selection(self):
        exercise = self.create_exercise("multiple_choice")
        item = MultipleChoiceItem.objects.create(
            exercise=exercise,
            question="Wie sagt man 'house' auf Deutsch?",
            selection_mode="single",
        )
        correct = MultipleChoiceOption.objects.create(
            item=item,
            text="das Haus",
            is_correct=True,
        )
        MultipleChoiceOption.objects.create(
            item=item,
            text="der Baum",
            is_correct=False,
        )

        result = evaluate_exercise(
            exercise,
            [{"item_id": item.id, "answer": correct.id}],
        )

        self.assert_evaluation(result, 1, 1, 100)
        self.assert_safe_result_items(result)

    def test_multiple_choice_multiple_selection_requires_exact_set(self):
        exercise = self.create_exercise("multiple_choice")
        item = MultipleChoiceItem.objects.create(
            exercise=exercise,
            question="Select the correct forms",
            selection_mode="multiple",
        )
        correct_1 = MultipleChoiceOption.objects.create(
            item=item,
            text="Option 1",
            is_correct=True,
        )
        correct_2 = MultipleChoiceOption.objects.create(
            item=item,
            text="Option 2",
            is_correct=True,
        )
        wrong = MultipleChoiceOption.objects.create(
            item=item,
            text="Option 3",
            is_correct=False,
        )

        partial_or_wrong_result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": [correct_1.id, wrong.id],
            }],
        )
        self.assert_evaluation(partial_or_wrong_result, 0, 1, 0)

        exact_result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": [correct_1.id, correct_2.id],
            }],
        )
        self.assert_evaluation(exact_result, 1, 1, 100)
        self.assert_safe_result_items(exact_result)

    def test_multiple_choice_rejects_duplicate_selected_ids(self):
        exercise = self.create_exercise("multiple_choice")
        item = MultipleChoiceItem.objects.create(
            exercise=exercise,
            question="Select the correct forms",
            selection_mode="multiple",
        )
        correct_1 = MultipleChoiceOption.objects.create(
            item=item,
            text="Option 1",
            is_correct=True,
        )
        MultipleChoiceOption.objects.create(
            item=item,
            text="Option 2",
            is_correct=True,
        )

        result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": [correct_1.id, correct_1.id],
            }],
        )

        self.assert_evaluation(result, 0, 1, 0)

    def test_dropdown_scores_each_select_part_independently(self):
        exercise = self.create_exercise("dropdown")
        item = DropdownItem.objects.create(exercise=exercise)

        part_1 = DropdownPart.objects.create(
            item=item,
            part_type="select",
            text="",
        )
        correct_1 = DropdownOption.objects.create(
            part=part_1,
            text="bin",
            is_correct=True,
        )
        DropdownOption.objects.create(
            part=part_1,
            text="bist",
            is_correct=False,
        )

        part_2 = DropdownPart.objects.create(
            item=item,
            part_type="select",
            text="",
        )
        DropdownOption.objects.create(
            part=part_2,
            text="ist",
            is_correct=False,
        )
        correct_2 = DropdownOption.objects.create(
            part=part_2,
            text="sind",
            is_correct=True,
        )

        result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": {
                    str(part_1.id): correct_1.id,
                    str(part_2.id): "invalid-option-id",
                },
            }],
        )

        self.assert_evaluation(result, 1, 2, 50)
        self.assert_safe_result_items(result)

    def test_dropdown_ignores_non_select_parts_for_scoring(self):
        exercise = self.create_exercise("dropdown")
        item = DropdownItem.objects.create(exercise=exercise)

        DropdownPart.objects.create(
            item=item,
            part_type="text",
            text="Ich",
        )
        select_part = DropdownPart.objects.create(
            item=item,
            part_type="select",
            text="",
        )
        correct_option = DropdownOption.objects.create(
            part=select_part,
            text="bin",
            is_correct=True,
        )

        result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": {str(select_part.id): correct_option.id},
            }],
        )

        self.assert_evaluation(result, 1, 1, 100)

    def test_gap_fill_ignores_surrounding_whitespace_but_not_case(self):
        exercise = self.create_exercise("gap_fill")
        item = GapFillItem.objects.create(
            exercise=exercise,
            text="Ich ___ müde.",
        )
        gap = GapFillGap.objects.create(
            item=item,
            placeholder="gap_1",
            correct_answer="bin",
        )

        correct_result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": {str(gap.id): "  bin  "},
            }],
        )
        self.assert_evaluation(correct_result, 1, 1, 100)

        wrong_case_result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": {str(gap.id): "BIN"},
            }],
        )
        self.assert_evaluation(wrong_case_result, 0, 1, 0)

    def test_gap_fill_supports_partial_score(self):
        exercise = self.create_exercise("gap_fill")
        item = GapFillItem.objects.create(
            exercise=exercise,
            text="Ich ___ und du ___.",
        )
        gap_1 = GapFillGap.objects.create(
            item=item,
            placeholder="gap_1",
            correct_answer="lerne",
        )
        gap_2 = GapFillGap.objects.create(
            item=item,
            placeholder="gap_2",
            correct_answer="lernst",
        )

        result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": {
                    str(gap_1.id): "lerne",
                    str(gap_2.id): "lernt",
                },
            }],
        )

        self.assert_evaluation(result, 1, 2, 50)
        self.assert_safe_result_items(result)

    def test_sentence_builder_requires_exact_token_order(self):
        exercise = self.create_exercise("sentence_builder")
        item = SentenceBuilderItem.objects.create(exercise=exercise)

        token_1 = SentenceBuilderToken.objects.create(
            item=item,
            text="Ich",
            correct_position=1,
            order=1,
        )
        token_2 = SentenceBuilderToken.objects.create(
            item=item,
            text="lerne",
            correct_position=2,
            order=2,
        )
        token_3 = SentenceBuilderToken.objects.create(
            item=item,
            text="Deutsch.",
            correct_position=3,
            order=3,
        )

        correct_result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": [
                    f"t{token_1.id}",
                    f"t{token_2.id}",
                    f"t{token_3.id}",
                ],
            }],
        )
        self.assert_evaluation(correct_result, 1, 1, 100)

        wrong_result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": [
                    f"t{token_2.id}",
                    f"t{token_1.id}",
                    f"t{token_3.id}",
                ],
            }],
        )
        self.assert_evaluation(wrong_result, 0, 1, 0)
        self.assert_safe_result_items(correct_result)

    def test_missing_answer_scores_zero_but_keeps_max_score(self):
        exercise = self.create_exercise("gap_fill")
        item = GapFillItem.objects.create(
            exercise=exercise,
            text="Ich ___ müde.",
        )
        GapFillGap.objects.create(
            item=item,
            placeholder="gap_1",
            correct_answer="bin",
        )

        result = evaluate_exercise(exercise, [])

        self.assert_evaluation(result, 0, 1, 0)

    def test_percentage_is_rounded_to_two_decimal_places(self):
        exercise = self.create_exercise("gap_fill")
        item = GapFillItem.objects.create(
            exercise=exercise,
            text="Ich ___, du ___, er ___.",
        )
        gaps = [
            GapFillGap.objects.create(
                item=item,
                placeholder=f"gap_{index}",
                correct_answer=answer,
            )
            for index, answer in enumerate(
                ["lerne", "lernst", "lernt"],
                start=1,
            )
        ]

        result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": {
                    str(gaps[0].id): "lerne",
                    str(gaps[1].id): "lernst",
                    str(gaps[2].id): "wrong",
                },
            }],
        )

        self.assert_evaluation(result, 2, 3, 66.67)

    def test_unknown_item_id_does_not_increase_score(self):
        exercise = self.create_exercise("gap_fill")
        item = GapFillItem.objects.create(
            exercise=exercise,
            text="Ich ___ müde.",
        )
        gap = GapFillGap.objects.create(
            item=item,
            placeholder="gap_1",
            correct_answer="bin",
        )

        result = evaluate_exercise(
            exercise,
            [{
                "item_id": 999999,
                "answer": {str(gap.id): "bin"},
            }],
        )

        self.assert_evaluation(result, 0, 1, 0)

    def test_answer_for_item_from_another_exercise_is_not_accepted(self):
        exercise = self.create_exercise("gap_fill")
        other_exercise = self.create_exercise("gap_fill")

        item = GapFillItem.objects.create(
            exercise=other_exercise,
            text="Ich ___ müde.",
        )
        gap = GapFillGap.objects.create(
            item=item,
            placeholder="gap_1",
            correct_answer="bin",
        )

        result = evaluate_exercise(
            exercise,
            [{
                "item_id": item.id,
                "answer": {str(gap.id): "bin"},
            }],
        )

        self.assert_evaluation(result, 0, 0, 0)

    def test_empty_exercise_has_zero_score_and_percentage(self):
        exercise = self.create_exercise("gap_fill")

        result = evaluate_exercise(exercise, [])

        self.assert_evaluation(result, 0, 0, 0)
