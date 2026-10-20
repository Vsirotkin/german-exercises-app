from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from exercises.models import (
    Exercise,
    Student,
    TeacherRecommendation,
    Topic,
)


class TeacherRecommendationModelAdminTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="recommendation-admin",
            password="test-password-123",
        )
        self.second_author = User.objects.create_user(
            username="recommendation-admin-2",
            password="test-password-123",
        )
        student_user = User.objects.create_user(
            username="recommendation-student",
            password="test-password-123",
        )
        self.student = Student.objects.create(
            user=student_user,
            first_name="Test",
            last_name="Student",
            email="recommendation-student@example.com",
            level="A2",
        )
        self.topic = Topic.objects.create(
            name="Manual recommendation topic",
        )
        self.exercise = Exercise.objects.create(
            title="Manual recommendation exercise",
            exercise_type="vocabulary_drill",
            language="german",
            level="A1",
            is_active=True,
            order=1,
        )
        self.exercise.topics.set([self.topic])
        self.model_admin = admin.site._registry[TeacherRecommendation]

    def make_recommendation(self, **kwargs):
        fields = {
            "student": self.student,
            "title": "Repeat the topic",
            "message": "Complete one more exercise.",
        }
        fields.update(kwargs)
        return TeacherRecommendation.objects.create(**fields)

    def test_reason_is_optional(self):
        recommendation = self.make_recommendation()

        self.assertIsNone(recommendation.reason)

    def test_topic_and_exercise_are_optional(self):
        recommendation = self.make_recommendation()

        self.assertIsNone(recommendation.topic)
        self.assertIsNone(recommendation.exercise)

    def test_default_priority_and_active_status(self):
        recommendation = self.make_recommendation()

        self.assertEqual(recommendation.priority, "normal")
        self.assertTrue(recommendation.is_active)

    def test_admin_assigns_creator_when_creating_recommendation(self):
        recommendation = TeacherRecommendation(
            student=self.student,
            title="Created in admin",
            message="Practice again.",
        )
        request = RequestFactory().post("/admin/")
        request.user = self.author

        self.model_admin.save_model(
            request,
            recommendation,
            form=None,
            change=False,
        )

        recommendation.refresh_from_db()
        self.assertEqual(recommendation.created_by, self.author)

    def test_admin_does_not_replace_creator_when_editing(self):
        recommendation = self.make_recommendation(created_by=self.author)
        request = RequestFactory().post("/admin/")
        request.user = self.second_author

        self.model_admin.save_model(
            request,
            recommendation,
            form=None,
            change=True,
        )

        recommendation.refresh_from_db()
        self.assertEqual(recommendation.created_by, self.author)

    def test_admin_registration_and_readonly_fields(self):
        self.assertIn("created_by", self.model_admin.readonly_fields)
        self.assertIn("created_at", self.model_admin.readonly_fields)
        self.assertIn("updated_at", self.model_admin.readonly_fields)
        self.assertIn("title", self.model_admin.list_display)
        self.assertIn("priority", self.model_admin.list_filter)

    def test_deleting_topic_and_exercise_preserves_recommendation(self):
        recommendation = self.make_recommendation(
            topic=self.topic,
            exercise=self.exercise,
        )

        self.topic.delete()
        self.exercise.delete()

        recommendation.refresh_from_db()
        self.assertIsNone(recommendation.topic)
        self.assertIsNone(recommendation.exercise)

    def test_deleting_student_deletes_recommendation(self):
        recommendation = self.make_recommendation()
        recommendation_id = recommendation.pk

        self.student.delete()

        self.assertFalse(
            TeacherRecommendation.objects.filter(
                pk=recommendation_id,
            ).exists()
        )
