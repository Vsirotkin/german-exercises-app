from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from exercises.models import (
    Exercise,
    ExerciseResult,
    Student,
    StudentTopicProgress,
    TeacherRecommendation,
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

    def test_result_endpoint_saves_empty_exercise_result(self):
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
            status.HTTP_201_CREATED,
        )
        self.assertEqual(response.data["exercise_id"], self.exercise_1.id)
        self.assertEqual(response.data["score"], 0)
        self.assertEqual(response.data["max_score"], 1)
        self.assertEqual(response.data["percentage"], 0.0)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertFalse(response.data["results"][0]["is_correct"])

        self.assertEqual(ExerciseResult.objects.count(), 1)

        result = ExerciseResult.objects.get()
        self.assertEqual(result.exercise, self.exercise_1)
        self.assertEqual(result.score, 0)
        self.assertEqual(result.max_score, 1)
        self.assertEqual(result.percentage, 0.0)


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

class StudentAnalyticsPermissionsAPITest(BaseAPITestCase):
    """
    Access control tests for student progress, history and admin analytics.
    """

    def create_other_student_with_result(self):
        # Preserve an unlinked profile: the admin list must include it.
        Student.objects.create(
            user=None,
            first_name="Unlinked",
            last_name="Profile",
            email="unlinked@example.com",
            level="A1",
        )

        other_user = User.objects.create_user(
            username="otherstudent",
            password="otherpassword123",
            email="other@example.com",
        )

        # User and Student IDs come from independent sequences.
        # If they coincide, delete the candidate and consume the next
        # Student ID, while keeping the total number of profiles stable.
        while True:
            other_student = Student.objects.create(
                user=other_user,
                first_name="Other",
                last_name="Student",
                email="other@example.com",
                level="B1",
            )
            if other_student.id != other_user.id:
                break
            other_student.delete()

        ExerciseResult.objects.create(
            student=other_student,
            exercise=self.exercise_2,
            score=1,
            max_score=2,
            percentage=50.0,
        )

        self.assertNotEqual(other_student.id, other_user.id)
        return other_student

    def test_current_user_returns_student_profile_id(self):
        self.authenticate()

        response = self.client.get("/api/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "student")
        self.assertEqual(response.data["student_id"], self.student.id)

    def test_unauthenticated_requests_are_rejected(self):
        progress_response = self.client.get(
            f"/api/results/student/{self.student.id}/progress/",
        )
        history_response = self.client.get(
            f"/api/results/student/{self.student.id}/",
        )
        list_response = self.client.get("/api/admin/students/")

        self.assertEqual(
            progress_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            history_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            list_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_student_can_read_own_progress_and_history(self):
        ExerciseResult.objects.create(
            student=self.student,
            exercise=self.exercise_1,
            score=1,
            max_score=1,
            percentage=100.0,
        )
        self.authenticate()

        progress_response = self.client.get(
            f"/api/results/student/{self.student.id}/progress/",
        )
        history_response = self.client.get(
            f"/api/results/student/{self.student.id}/",
        )

        self.assertEqual(
            progress_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(progress_response.data["total_exercises"], 1)
        self.assertEqual(progress_response.data["average_score"], 100.0)
        self.assertEqual(progress_response.data["best_score"], 100.0)

        self.assertEqual(
            history_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(history_response.data), 1)
        self.assertEqual(
            history_response.data[0]["exercise_title"],
            self.exercise_1.title,
        )

    def test_student_cannot_read_another_students_progress_or_history(self):
        other_student = self.create_other_student_with_result()
        self.authenticate()

        progress_response = self.client.get(
            f"/api/results/student/{other_student.id}/progress/",
        )
        history_response = self.client.get(
            f"/api/results/student/{other_student.id}/",
        )

        self.assertEqual(
            progress_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            history_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(progress_response.data, {"detail": "Not found."})
        self.assertEqual(history_response.data, {"detail": "Not found."})

    def test_student_cannot_access_admin_student_list(self):
        self.authenticate()

        response = self.client.get("/api/admin/students/")

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_read_any_students_progress_history_and_list(self):
        other_student = self.create_other_student_with_result()

        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.authenticate()

        progress_response = self.client.get(
            f"/api/results/student/{other_student.id}/progress/",
        )
        history_response = self.client.get(
            f"/api/results/student/{other_student.id}/",
        )
        list_response = self.client.get("/api/admin/students/")

        self.assertEqual(
            progress_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(progress_response.data["total_exercises"], 1)
        self.assertEqual(progress_response.data["average_score"], 50.0)
        self.assertEqual(progress_response.data["best_score"], 50.0)

        self.assertEqual(
            history_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(history_response.data), 1)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        students = list_response.data
        self.assertEqual(len(students), 3)

        other_row = next(
            student
            for student in students
            if student["id"] == other_student.id
        )
        self.assertEqual(other_row["total_exercises"], 1)
        self.assertEqual(other_row["average_score"], 50.0)
        self.assertEqual(other_row["best_score"], 50.0)

    def test_superuser_can_access_admin_list_without_staff_flag(self):
        self.user.is_staff = False
        self.user.is_superuser = True
        self.user.save(update_fields=["is_staff", "is_superuser"])
        self.authenticate()

        response = self.client.get("/api/admin/students/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AutomaticRecommendationsAPITest(BaseAPITestCase):
    endpoint = "/api/recommendations/"

    def create_result(self, exercise, percentage):
        return ExerciseResult.objects.create(
            student=self.student,
            exercise=exercise,
            score=percentage,
            max_score=100,
            percentage=percentage,
            details={},
        )

    def test_endpoint_requires_authentication(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_no_history_returns_recommendation_contract(self):
        self.authenticate()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("generated_at", response.data)
        self.assertIn("recommendations", response.data)
        self.assertEqual(len(response.data["recommendations"]), 1)

        recommendation = response.data["recommendations"][0]
        self.assertEqual(recommendation["source"], "system")
        self.assertEqual(recommendation["kind"], "start_learning")
        self.assertEqual(recommendation["priority"], "low")
        self.assertEqual(
            recommendation["exercise"]["id"],
            self.exercise_1.id,
        )
        self.assertEqual(
            recommendation["topic"]["id"],
            self.topic.id,
        )
        self.assertIsNone(recommendation["created_at"])

    def test_low_result_recommends_repeating_same_exercise(self):
        self.create_result(self.exercise_1, 40)
        self.authenticate()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recommendation = response.data["recommendations"][0]
        self.assertEqual(recommendation["kind"], "review_exercise")
        self.assertEqual(recommendation["priority"], "high")
        self.assertEqual(
            recommendation["exercise"]["id"],
            self.exercise_1.id,
        )

    def test_medium_result_recommends_another_exercise_on_same_topic(self):
        self.create_result(self.exercise_1, 65)
        self.authenticate()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recommendation = response.data["recommendations"][0]
        self.assertEqual(recommendation["kind"], "practice_topic")
        self.assertEqual(recommendation["priority"], "normal")
        self.assertEqual(
            recommendation["exercise"]["id"],
            self.exercise_2.id,
        )
        self.assertEqual(
            recommendation["topic"]["id"],
            self.topic.id,
        )

    def test_high_result_recommends_next_unattempted_exercise(self):
        self.create_result(self.exercise_1, 100)
        self.authenticate()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recommendation = response.data["recommendations"][0]
        self.assertEqual(recommendation["kind"], "continue_learning")
        self.assertEqual(recommendation["priority"], "low")
        self.assertEqual(
            recommendation["exercise"]["id"],
            self.exercise_2.id,
        )

    def test_invalid_limit_returns_controlled_error(self):
        self.authenticate()

        response = self.client.get(self.endpoint, {"limit": "abc"})

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(response.data["error"]["code"], "INVALID_LIMIT")

    def test_zero_limit_returns_controlled_error(self):
        self.authenticate()

        response = self.client.get(self.endpoint, {"limit": 0})

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(response.data["error"]["code"], "INVALID_LIMIT")

    def test_limit_is_capped_at_ten(self):
        exercises = [self.exercise_1, self.exercise_2]
        for order in range(3, 12):
            exercise = Exercise.objects.create(
                title=f"Extra exercise {order}",
                exercise_type="vocabulary_drill",
                language="german",
                level="A1",
                is_active=True,
                order=order,
            )
            exercise.topics.add(self.topic)
            exercises.append(exercise)

        for exercise in exercises:
            self.create_result(exercise, 20)

        self.authenticate()
        response = self.client.get(self.endpoint, {"limit": 20})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["recommendations"]), 10)

    def test_missing_student_profile_returns_controlled_error(self):
        user = User.objects.create_user(
            username="no-student-profile",
            password="testpassword123",
        )
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": user.username,
                "password": "testpassword123",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.data["error"]["code"],
            "STUDENT_PROFILE_NOT_FOUND",
        )

    def test_supplied_student_id_does_not_change_recommendation_owner(self):
        other_user = User.objects.create_user(
            username="other-recommendation-student",
            password="testpassword123",
        )
        other_student = Student.objects.create(
            user=other_user,
            first_name="Other",
            last_name="Student",
            email="other-recommendation-student@example.com",
            level="A2",
        )
        ExerciseResult.objects.create(
            student=other_student,
            exercise=self.exercise_2,
            score=10,
            max_score=100,
            percentage=10,
            details={},
        )
        self.authenticate()

        response = self.client.get(
            self.endpoint,
            {"student_id": other_student.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recommendation = response.data["recommendations"][0]
        self.assertEqual(recommendation["kind"], "start_learning")
        self.assertEqual(
            recommendation["exercise"]["id"],
            self.exercise_1.id,
        )

    def test_manual_recommendation_matches_api_contract(self):
        manual = TeacherRecommendation.objects.create(
            student=self.student,
            title="Repeat reflexive pronouns",
            message="Practise the topic again.",
            reason="Your last result was below the target.",
            priority="normal",
            topic=self.topic,
            exercise=self.exercise_1,
        )
        self.authenticate()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recommendation = next(
            item
            for item in response.data["recommendations"]
            if item["id"] == f"admin:{manual.id}"
        )

        self.assertEqual(recommendation["source"], "admin")
        self.assertEqual(recommendation["kind"], "teacher_advice")
        self.assertEqual(recommendation["title"], manual.title)
        self.assertEqual(recommendation["message"], manual.message)
        self.assertEqual(recommendation["reason"], manual.reason)
        self.assertEqual(recommendation["priority"], "normal")
        self.assertEqual(
            recommendation["topic"],
            {"id": self.topic.id, "name": self.topic.name},
        )
        self.assertEqual(
            recommendation["exercise"],
            {
                "id": self.exercise_1.id,
                "title": self.exercise_1.title,
                "exercise_type": self.exercise_1.exercise_type,
                "level": self.exercise_1.level,
            },
        )
        self.assertIsNotNone(recommendation["created_at"])

    def test_manual_recommendations_precede_automatic_ones(self):
        TeacherRecommendation.objects.create(
            student=self.student,
            title="Teacher advice",
            message="Review this topic.",
            priority="low",
        )
        self.authenticate()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recommendations = response.data["recommendations"]

        self.assertEqual(
            [item["source"] for item in recommendations],
            ["admin", "system"],
        )
        self.assertEqual(
            recommendations[0]["kind"],
            "teacher_advice",
        )
        self.assertEqual(
            recommendations[1]["kind"],
            "start_learning",
        )

    def test_inactive_manual_recommendations_are_excluded(self):
        TeacherRecommendation.objects.create(
            student=self.student,
            title="Inactive advice",
            message="This recommendation should not appear.",
            is_active=False,
        )
        self.authenticate()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recommendations = response.data["recommendations"]

        self.assertTrue(recommendations)
        self.assertTrue(
            all(item["source"] == "system" for item in recommendations)
        )
        self.assertNotIn(
            "Inactive advice",
            [item["title"] for item in recommendations],
        )

    def test_limit_applies_to_combined_recommendation_feed(self):
        TeacherRecommendation.objects.create(
            student=self.student,
            title="Teacher advice one",
            message="First recommendation.",
            priority="normal",
        )
        TeacherRecommendation.objects.create(
            student=self.student,
            title="Teacher advice two",
            message="Second recommendation.",
            priority="high",
        )
        self.authenticate()

        response = self.client.get(self.endpoint, {"limit": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recommendations = response.data["recommendations"]

        self.assertEqual(len(recommendations), 2)
        self.assertTrue(
            all(item["source"] == "admin" for item in recommendations)
        )

    def test_legacy_topics_endpoint_remains_available(self):
        self.authenticate()

        response = self.client.get(
            "/api/recommendations/student/topics/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("recommendations", response.data)
        self.assertEqual(
            response.data["recommendations"][0]["name"],
            self.topic.name,
        )


class StudentTopicProgressAPITest(BaseAPITestCase):
    def post_result_with_percentage(self, exercise, percentage):
        self.authenticate()
        evaluation = {
            "score": percentage / 100,
            "max_score": 1,
            "percentage": float(percentage),
            "results": [],
        }
        with patch(
            "exercises.views._evaluate_answers",
            return_value=evaluation,
        ):
            return self.client.post(
                "/api/results/",
                {"exercise_id": exercise.id, "answers": []},
                format="json",
            )

    def test_repeated_attempt_counts_exercise_once_and_keeps_best_score(self):
        first = self.post_result_with_percentage(self.exercise_1, 40)
        second = self.post_result_with_percentage(self.exercise_1, 80)

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

        progress = StudentTopicProgress.objects.get(
            student=self.student, topic=self.topic
        )
        self.assertEqual(progress.exercises_completed, 1)
        self.assertAlmostEqual(progress.mastery_level, 0.8)

    def test_mastery_averages_best_scores_for_unique_exercises(self):
        self.post_result_with_percentage(self.exercise_1, 40)
        self.post_result_with_percentage(self.exercise_1, 80)
        response = self.post_result_with_percentage(self.exercise_2, 0)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        progress = StudentTopicProgress.objects.get(
            student=self.student, topic=self.topic
        )
        self.assertEqual(progress.exercises_completed, 2)
        self.assertAlmostEqual(progress.mastery_level, 0.4)

    def test_result_updates_progress_for_every_exercise_topic(self):
        second_topic = Topic.objects.create(
            name="Arbeit",
            description="Work",
        )
        self.exercise_1.topics.add(second_topic)

        response = self.post_result_with_percentage(self.exercise_1, 80)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            StudentTopicProgress.objects.filter(student=self.student).count(),
            2,
        )
        for topic in (self.topic, second_topic):
            progress = StudentTopicProgress.objects.get(
                student=self.student, topic=topic
            )
            self.assertEqual(progress.exercises_completed, 1)
            self.assertAlmostEqual(progress.mastery_level, 0.8)
