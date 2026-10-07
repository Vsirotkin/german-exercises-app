from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.serializers import Serializer

from exercises.models import (
    Exercise,
    ExerciseResult,
    GapFillGap,
    GapFillItem,
    MultipleChoiceItem,
    MultipleChoiceOption,
    SentenceBuilderItem,
    SentenceBuilderToken,
    Student,
    Topic,
    VocabularyItem,
)
from exercises.serializers import (
    ExerciseListSerializer,
    ExerciseSerializer,
)


class BaseSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
            email="test@example.com",
        )

        self.student = Student.objects.create(
            user=self.user,
            first_name="Test",
            last_name="Student",
            email="test@example.com",
            level="A2",
        )

        self.topic = Topic.objects.create(
            name="Krankenhaus",
            description="Hospital",
        )

        self.exercise_1 = Exercise.objects.create(
            title="Exercise 1",
            exercise_type="vocabulary_drill",
            language="german",
            level="A1",
            is_active=True,
            order=1,
        )
        self.exercise_1.topics.add(self.topic)

        self.exercise_2 = Exercise.objects.create(
            title="Exercise 2",
            exercise_type="vocabulary_drill",
            language="german",
            level="A1",
            is_active=True,
            order=2,
        )
        self.exercise_2.topics.add(self.topic)

        VocabularyItem.objects.create(
            exercise=self.exercise_1,
            prompt="der Arzt",
            correct_answer="врач",
            distractor_1="аптекарь",
            distractor_2="пациент",
            distractor_3="медсестра",
            order=0,
        )

    def request_context(self):
        class MockRequest:
            user = self.user
            is_authenticated = True

        return {"request": MockRequest()}


class ExerciseProgressSerializerTest(BaseSerializerTestCase):
    def test_exercise_without_result_is_not_started(self):
        serializer = ExerciseListSerializer(
            self.exercise_1,
            context=self.request_context(),
        )

        self.assertIsNone(serializer.data["score"])
        self.assertEqual(serializer.data["status"], "not_started")
        self.assertFalse(serializer.data["is_locked"])

    def test_score_is_returned_from_last_result(self):
        ExerciseResult.objects.create(
            student=self.student,
            exercise=self.exercise_1,
            score=4,
            max_score=5,
            percentage=80,
            details={"answers": []},
        )

        serializer = ExerciseListSerializer(
            self.exercise_1,
            context=self.request_context(),
        )

        self.assertEqual(serializer.data["score"], 80)
        self.assertEqual(serializer.data["status"], "completed")
        self.assertFalse(serializer.data["is_locked"])

    def test_status_boundaries(self):
        test_cases = [
            (100, "mastered"),
            (99, "completed"),
            (80, "completed"),
            (79, "review_recommended"),
            (50, "review_recommended"),
            (49, "needs_review"),
            (0, "needs_review"),
        ]

        for percentage, expected_status in test_cases:
            with self.subTest(percentage=percentage):
                ExerciseResult.objects.all().delete()

                ExerciseResult.objects.create(
                    student=self.student,
                    exercise=self.exercise_1,
                    score=percentage,
                    max_score=100,
                    percentage=percentage,
                    details={"answers": []},
                )

                serializer = ExerciseListSerializer(
                    self.exercise_1,
                    context=self.request_context(),
                )

                self.assertEqual(
                    serializer.data["status"],
                    expected_status,
                )

    def test_previous_failed_exercise_locks_next_exercise(self):
        ExerciseResult.objects.create(
            student=self.student,
            exercise=self.exercise_1,
            score=2,
            max_score=5,
            percentage=40,
            details={"answers": []},
        )

        serializer = ExerciseListSerializer(
            self.exercise_2,
            context=self.request_context(),
        )

        self.assertTrue(serializer.data["is_locked"])

    def test_previous_exercise_at_50_percent_does_not_lock_next(self):
        ExerciseResult.objects.create(
            student=self.student,
            exercise=self.exercise_1,
            score=2.5,
            max_score=5,
            percentage=50,
            details={"answers": []},
        )

        serializer = ExerciseListSerializer(
            self.exercise_2,
            context=self.request_context(),
        )

        self.assertFalse(serializer.data["is_locked"])

    def test_previous_exercise_without_result_does_not_lock_next(self):
        serializer = ExerciseListSerializer(
            self.exercise_2,
            context=self.request_context(),
        )

        self.assertFalse(serializer.data["is_locked"])

    def test_first_exercise_is_not_locked(self):
        serializer = ExerciseListSerializer(
            self.exercise_1,
            context=self.request_context(),
        )

        self.assertFalse(serializer.data["is_locked"])

    def test_list_serializer_contains_learning_state(self):
        ExerciseResult.objects.create(
            student=self.student,
            exercise=self.exercise_1,
            score=4,
            max_score=5,
            percentage=80,
            details={"answers": []},
        )

        serializer = ExerciseListSerializer(
            self.exercise_1,
            context=self.request_context(),
        )

        self.assertEqual(serializer.data["score"], 80)
        self.assertEqual(serializer.data["status"], "completed")
        self.assertFalse(serializer.data["is_locked"])
        self.assertEqual(serializer.data["topics"], ["Krankenhaus"])

    def test_list_serializer_does_not_include_full_content(self):
        serializer = ExerciseListSerializer(
            self.exercise_1,
            context=self.request_context(),
        )

        self.assertNotIn("vocabulary_items", serializer.data)
        self.assertNotIn("multiple_choice_items", serializer.data)
        self.assertNotIn("dropdown_items", serializer.data)
        self.assertNotIn("gap_fill_items", serializer.data)
        self.assertNotIn("sentence_builder_items", serializer.data)


class ExerciseFullSerializerTest(BaseSerializerTestCase):
    def test_full_serializer_contains_vocabulary_items(self):
        serializer = ExerciseSerializer(
            self.exercise_1,
            context=self.request_context(),
        )

        data = serializer.data

        self.assertIn("vocabulary_items", data)
        self.assertEqual(len(data["vocabulary_items"]), 1)

        item = data["vocabulary_items"][0]

        self.assertEqual(item["prompt"], "der Arzt")
        self.assertIn("options", item)
        self.assertEqual(len(item["options"]), 4)

    def test_full_serializer_does_not_expose_vocabulary_correct_answer_field(self):
        serializer = ExerciseSerializer(
            self.exercise_1,
            context=self.request_context(),
        )

        item = serializer.data["vocabulary_items"][0]

        self.assertNotIn("correct_answer", item)

        for option in item["options"]:
            self.assertIn("id", option)
            self.assertIn("text", option)

    def test_full_serializer_hides_multiple_choice_correct_flags(self):
        exercise = Exercise.objects.create(
            title="Multiple Choice",
            exercise_type="multiple_choice",
            language="german",
            level="A1",
            order=3,
        )
        exercise.topics.add(self.topic)

        item = MultipleChoiceItem.objects.create(
            exercise=exercise,
            question="Was ist richtig?",
            selection_mode="single",
            order=0,
        )

        MultipleChoiceOption.objects.create(
            item=item,
            text="Richtig",
            is_correct=True,
            order=0,
        )

        MultipleChoiceOption.objects.create(
            item=item,
            text="Falsch",
            is_correct=False,
            order=1,
        )

        serializer = ExerciseSerializer(
            exercise,
            context=self.request_context(),
        )

        options = serializer.data["multiple_choice_items"][0]["options"]

        self.assertEqual(len(options), 2)

        for option in options:
            self.assertNotIn("is_correct", option)
            self.assertIn("id", option)
            self.assertIn("text", option)

    def test_full_serializer_hides_gap_fill_correct_answers(self):
        exercise = Exercise.objects.create(
            title="Gap Fill",
            exercise_type="gap_fill",
            language="german",
            level="A1",
            order=3,
        )
        exercise.topics.add(self.topic)

        item = GapFillItem.objects.create(
            exercise=exercise,
            text="Ich __ morgen.",
            order=0,
        )

        GapFillGap.objects.create(
            item=item,
            placeholder="__",
            correct_answer="komme",
            order=0,
        )

        serializer = ExerciseSerializer(
            exercise,
            context=self.request_context(),
        )

        gap = serializer.data["gap_fill_items"][0]["gaps"][0]

        self.assertEqual(gap["placeholder"], "__")
        self.assertNotIn("correct_answer", gap)

    def test_full_serializer_hides_sentence_builder_positions(self):
        exercise = Exercise.objects.create(
            title="Sentence Builder",
            exercise_type="sentence_builder",
            language="german",
            level="A1",
            order=3,
        )
        exercise.topics.add(self.topic)

        item = SentenceBuilderItem.objects.create(
            exercise=exercise,
            order=0,
        )

        SentenceBuilderToken.objects.create(
            item=item,
            text="Ich",
            correct_position=0,
            order=0,
        )

        serializer = ExerciseSerializer(
            exercise,
            context=self.request_context(),
        )

        token = serializer.data["sentence_builder_items"][0]["tokens"][0]

        self.assertEqual(token["text"], "Ich")
        self.assertTrue(token["id"].startswith("t"))
        self.assertNotIn("correct_position", token)
