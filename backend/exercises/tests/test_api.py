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


class ExerciseImportPermissionAPITest(BaseAPITestCase):
    def test_import_rejects_unauthenticated_user(self):
        response = self.client.post(
            "/api/admin/exercises/import/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_import_rejects_authenticated_non_staff_user(self):
        self.authenticate()

        response = self.client.post(
            "/api/admin/exercises/import/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_import_allows_staff_user(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])

        self.authenticate()

        response = self.client.post(
            "/api/admin/exercises/import/",
            {},
            format="json",
        )

        self.assertNotEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_import_allows_superuser(self):
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save(
            update_fields=["is_staff", "is_superuser"],
        )

        self.authenticate()

        response = self.client.post(
            "/api/admin/exercises/import/",
            {},
            format="json",
        )

        self.assertNotEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class ExerciseImportAPITest(BaseAPITestCase):
    def get_import_payload(self):
        return {
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

    def test_import_requires_authentication(self):
        response = self.client.post(
            "/api/admin/exercises/import/",
            self.get_import_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_non_staff_user_cannot_create_exercise(self):
        self.authenticate()

        response = self.client.post(
            "/api/admin/exercises/import/",
            self.get_import_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            Exercise.objects.filter(title="API Import Test").exists(),
        )

    def test_staff_user_can_create_exercise_via_current_api(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])

        self.authenticate()

        response = self.client.post(
            "/api/admin/exercises/import/",
            self.get_import_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        exercise = Exercise.objects.get(
            title="API Import Test",
        )

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


class ExerciseImportValidateAPITest(BaseAPITestCase):
    def get_valid_import_payload(self):
        return {
            "version": 1,
            "language": "german",
            "exercises": [
                {
                    "title": "Validation Test",
                    "type": "vocabulary_drill",
                    "level": "A1",
                    "topics": ["Validation"],
                    "active": True,
                    "order": 1,
                    "data": {
                        "items": [
                            {
                                "word": "das Haus",
                                "correct": "дом",
                                "distractors": [
                                    "машина",
                                    "школа",
                                    "магазин",
                                ],
                            }
                        ]
                    },
                }
            ],
        }

    def authenticate_as_staff(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.authenticate()

    def test_validate_requires_authentication(self):
        response = self.client.post(
            "/api/admin/exercises/import/validate/",
            self.get_valid_import_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_validate_rejects_authenticated_non_staff_user(self):
        self.authenticate()

        response = self.client.post(
            "/api/admin/exercises/import/validate/",
            self.get_valid_import_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_validate_accepts_valid_payload_for_staff_user(self):
        self.authenticate_as_staff()

        exercise_count_before = Exercise.objects.count()
        topic_count_before = Topic.objects.count()

        response = self.client.post(
            "/api/admin/exercises/import/validate/",
            self.get_valid_import_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(response.data["valid"])
        self.assertEqual(response.data["errors"], [])
        self.assertEqual(
            response.data["summary"]["exercise_count"],
            1,
        )
        self.assertEqual(
            response.data["summary"]["language"],
            "german",
        )
        self.assertEqual(
            response.data["summary"]["version"],
            1,
        )

        self.assertEqual(
            Exercise.objects.count(),
            exercise_count_before,
        )
        self.assertEqual(
            Topic.objects.count(),
            topic_count_before,
        )

    def test_validate_returns_errors_for_invalid_business_rules(self):
        self.authenticate_as_staff()

        payload = self.get_valid_import_payload()
        payload["exercises"][0]["data"]["items"][0]["distractors"] = [
            "машина",
            "машина",
            "магазин",
        ]

        response = self.client.post(
            "/api/admin/exercises/import/validate/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertFalse(response.data["valid"])
        self.assertTrue(response.data["errors"])

        self.assertEqual(
            Exercise.objects.count(),
            2,
        )

    def test_validate_does_not_create_exercises(self):
        self.authenticate_as_staff()

        payload = self.get_valid_import_payload()

        exercise_count_before = Exercise.objects.count()

        response = self.client.post(
            "/api/admin/exercises/import/validate/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(response.data["valid"])

        self.assertEqual(
            Exercise.objects.count(),
            exercise_count_before,
        )


    def test_validate_rejects_malformed_json(self):
        self.authenticate_as_staff()

        response = self.client.post(
            "/api/admin/exercises/import/validate/",
            '{"version": 1, "language": "german", "exercises": [}',
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
