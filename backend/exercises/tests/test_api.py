from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from exercises.models import (
    Exercise,
    ExerciseResult,
    Student,
    Topic,
    VocabularyItem,
)


class BaseAPITestCase(TestCase):
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

        self.client = APIClient()

    def authenticate(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "testpassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")


class ExerciseListAPITest(BaseAPITestCase):
    def test_get_exercises_list_authenticated(self):
        self.authenticate()

        response = self.client.get("/api/exercises/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(len(response.data), 2)

        exercise = response.data[0]

        self.assertEqual(
            exercise["title"],
            "Exercise 1",
        )
        self.assertEqual(
            exercise["topics"],
            ["Krankenhaus"],
        )

        self.assertIn("score", exercise)
        self.assertIn("status", exercise)
        self.assertIn("is_locked", exercise)

        self.assertNotIn("vocabulary_items", exercise)
        self.assertNotIn("multiple_choice_items", exercise)
        self.assertNotIn("dropdown_items", exercise)
        self.assertNotIn("gap_fill_items", exercise)
        self.assertNotIn("sentence_builder_items", exercise)

    def test_get_exercises_list_unauthenticated(self):
        response = self.client.get("/api/exercises/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class ExerciseDetailAPITest(BaseAPITestCase):
    def test_get_full_exercise_unauthenticated(self):
        response = self.client.get(f"/api/exercises/{self.exercise_1.id}/full/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["title"],
            "Exercise 1",
        )

        self.assertEqual(
            len(response.data["vocabulary_items"]),
            1,
        )

        self.assertNotIn(
            "correct_answer",
            response.data["vocabulary_items"][0],
        )

    def test_get_nonexistent_exercise_returns_404(self):
        response = self.client.get("/api/exercises/999999/full/")

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_inactive_exercise_is_not_publicly_available(self):
        self.exercise_1.is_active = False
        self.exercise_1.save(update_fields=["is_active"])

        response = self.client.get(f"/api/exercises/{self.exercise_1.id}/full/")

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class ExerciseResultAPITest(BaseAPITestCase):
    def test_result_requires_authentication(self):
        response = self.client.post(
            "/api/results/",
            {
                "exercise_id": self.exercise_1.id,
                "answers": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_result_requires_exercise_id(self):
        self.authenticate()

        response = self.client.post(
            "/api/results/",
            {
                "answers": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "INVALID_EXERCISE_ID",
        )

    def test_result_requires_answers_array(self):
        self.authenticate()

        response = self.client.post(
            "/api/results/",
            {
                "exercise_id": self.exercise_1.id,
                "answers": {},
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "INVALID_ANSWERS",
        )

    def test_result_endpoint_currently_returns_not_implemented(self):
        self.authenticate()

        response = self.client.post(
            "/api/results/",
            {
                "exercise_id": self.exercise_1.id,
                "answers": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_501_NOT_IMPLEMENTED,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "EVALUATOR_NOT_IMPLEMENTED",
        )

        self.assertEqual(
            ExerciseResult.objects.count(),
            0,
        )


class ExerciseImportAPITest(BaseAPITestCase):
    def test_import_requires_authentication(self):
        response = self.client.post(
            "/api/admin/exercises/import/",
            {
                "title": "Test Import",
                "exercise_type": "vocabulary_drill",
                "topics": ["Test"],
                "language": "german",
                "level": "A1",
                "is_active": True,
                "order": 10,
                "vocabulary_items": [
                    {
                        "prompt": "Haus",
                        "correct_answer": "дом",
                        "distractor_1": "машина",
                        "distractor_2": "стол",
                        "distractor_3": "книга",
                        "order": 0,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_create_exercise_via_current_api(self):
        self.authenticate()

        payload = {
            "title": "API Import Test",
            "exercise_type": "vocabulary_drill",
            "topics": ["API Test"],
            "language": "german",
            "level": "A1",
            "is_active": True,
            "order": 10,
            "vocabulary_items": [
                {
                    "prompt": "Haus",
                    "correct_answer": "дом",
                    "distractor_1": "машина",
                    "distractor_2": "стол",
                    "distractor_3": "книга",
                    "order": 0,
                }
            ],
        }

        response = self.client.post(
            "/api/admin/exercises/import/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        exercise = Exercise.objects.get(title="API Import Test")

        self.assertEqual(
            exercise.exercise_type,
            "vocabulary_drill",
        )

        self.assertEqual(
            exercise.topics.count(),
            1,
        )

        self.assertEqual(
            exercise.vocabulary_items.count(),
            1,
        )
