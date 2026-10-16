from rest_framework import status

from exercises.models import Exercise, ExerciseResult, MultipleChoiceItem, MultipleChoiceOption
from exercises.tests.test_api import BaseAPITestCase


class RotatingCardAPITest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.exercise = Exercise.objects.create(
            title="Rotating cards",
            exercise_type="multiple_choice",
            language="german",
            level="A1",
            is_active=True,
        )
        self.item = MultipleChoiceItem.objects.create(
            exercise=self.exercise,
            question="Was bedeutet Haus?",
            selection_mode="single",
        )
        self.correct = MultipleChoiceOption.objects.create(
            item=self.item, text="дом", is_correct=True
        )
        self.wrong = MultipleChoiceOption.objects.create(
            item=self.item, text="машина", is_correct=False
        )
        self.authenticate()

    def check(self, answer):
        return self.client.post(
            "/api/results/check-answer/",
            {
                "exercise_id": self.exercise.id,
                "item_id": self.item.id,
                "answer": str(answer),
            },
            format="json",
        )

    def test_correct_answer_is_checked_without_saving_result(self):
        response = self.check(self.correct.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_correct"])
        self.assertNotIn("correct_answer", response.data)
        self.assertEqual(ExerciseResult.objects.count(), 0)

    def test_wrong_answer_returns_correct_text(self):
        response = self.check(self.wrong.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_correct"])
        self.assertEqual(response.data["correct_answer"], "дом")
        self.assertEqual(ExerciseResult.objects.count(), 0)

    def test_missing_fields_are_rejected(self):
        response = self.client.post(
            "/api/results/check-answer/",
            {"exercise_id": self.exercise.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
