from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from exercises.models import (
    Exercise,
    Student,
    TeacherRecommendation,
    Topic,
)
from exercises.services.recommendation_feed import (
    build_recommendation_feed,
)


class RecommendationFeedTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username="feed-student",
            password="test-password-123",
        )
        self.student = Student.objects.create(
            user=user,
            first_name="Feed",
            last_name="Student",
            email="feed-student@example.com",
            level="A2",
        )

        other_user = User.objects.create_user(
            username="other-feed-student",
            password="test-password-123",
        )
        self.other_student = Student.objects.create(
            user=other_user,
            first_name="Other",
            last_name="Student",
            email="other-feed-student@example.com",
            level="A2",
        )

        self.topic = Topic.objects.create(name="Feed topic")
        self.exercise = Exercise.objects.create(
            title="Feed exercise",
            exercise_type="vocabulary_drill",
            language="german",
            level="A1",
            is_active=True,
            order=1,
        )
        self.exercise.topics.add(self.topic)

    def make_recommendation(self, **kwargs):
        fields = {
            "student": self.student,
            "title": "Teacher recommendation",
            "message": "Practise this topic.",
        }
        fields.update(kwargs)
        return TeacherRecommendation.objects.create(**fields)

    def test_teacher_recommendation_matches_api_contract(self):
        recommendation = self.make_recommendation(
            reason="The student needs more practice.",
            topic=self.topic,
            exercise=self.exercise,
            priority="high",
        )

        with patch(
            "exercises.services.recommendation_feed."
            "build_automatic_recommendations",
            return_value=[],
        ):
            feed = build_recommendation_feed(self.student)

        self.assertEqual(len(feed), 1)
        item = feed[0]
        self.assertEqual(item["id"], f"admin:{recommendation.id}")
        self.assertEqual(item["source"], "admin")
        self.assertEqual(item["kind"], "teacher_advice")
        self.assertEqual(item["title"], recommendation.title)
        self.assertEqual(item["message"], recommendation.message)
        self.assertEqual(item["reason"], recommendation.reason)
        self.assertEqual(item["priority"], "high")
        self.assertEqual(
            item["topic"],
            {"id": self.topic.id, "name": self.topic.name},
        )
        self.assertEqual(
            item["exercise"],
            {
                "id": self.exercise.id,
                "title": self.exercise.title,
                "exercise_type": self.exercise.exercise_type,
                "level": self.exercise.level,
            },
        )
        self.assertEqual(item["created_at"], recommendation.created_at)

    def test_teacher_recommendations_sort_by_priority_then_newest(self):
        low = self.make_recommendation(
            title="Low priority",
            priority="low",
        )
        normal_old = self.make_recommendation(
            title="Normal old",
            priority="normal",
        )
        high = self.make_recommendation(
            title="High priority",
            priority="high",
        )
        normal_new = self.make_recommendation(
            title="Normal new",
            priority="normal",
        )

        base_time = timezone.now() - timedelta(days=1)
        TeacherRecommendation.objects.filter(pk=low.pk).update(
            created_at=base_time + timedelta(minutes=1)
        )
        TeacherRecommendation.objects.filter(pk=normal_old.pk).update(
            created_at=base_time + timedelta(minutes=2)
        )
        TeacherRecommendation.objects.filter(pk=high.pk).update(
            created_at=base_time + timedelta(minutes=3)
        )
        TeacherRecommendation.objects.filter(pk=normal_new.pk).update(
            created_at=base_time + timedelta(minutes=4)
        )

        with patch(
            "exercises.services.recommendation_feed."
            "build_automatic_recommendations",
            return_value=[],
        ):
            feed = build_recommendation_feed(self.student)

        self.assertEqual(
            [item["title"] for item in feed],
            ["High priority", "Normal new", "Normal old", "Low priority"],
        )

    def test_inactive_and_other_student_recommendations_are_excluded(self):
        active = self.make_recommendation(title="Active")
        self.make_recommendation(title="Inactive", is_active=False)
        self.make_recommendation(
            title="Other student",
            student=self.other_student,
        )

        with patch(
            "exercises.services.recommendation_feed."
            "build_automatic_recommendations",
            return_value=[],
        ):
            feed = build_recommendation_feed(self.student)

        self.assertEqual(
            [item["id"] for item in feed],
            [f"admin:{active.id}"],
        )

    def test_teacher_recommendations_precede_automatic_recommendations(self):
        teacher = self.make_recommendation(
            title="Teacher low",
            priority="low",
        )
        automatic = [
            {
                "id": "system:high",
                "source": "system",
                "kind": "review_exercise",
                "title": "System high",
                "message": "Repeat exercise.",
                "reason": None,
                "priority": "high",
                "topic": None,
                "exercise": None,
                "created_at": None,
            },
            {
                "id": "system:normal",
                "source": "system",
                "kind": "practice_topic",
                "title": "System normal",
                "message": "Practise more.",
                "reason": None,
                "priority": "normal",
                "topic": None,
                "exercise": None,
                "created_at": None,
            },
        ]

        with patch(
            "exercises.services.recommendation_feed."
            "build_automatic_recommendations",
            return_value=automatic,
        ):
            feed = build_recommendation_feed(self.student)

        self.assertEqual(
            [item["id"] for item in feed],
            [
                f"admin:{teacher.id}",
                "system:high",
                "system:normal",
            ],
        )

    def test_limit_applies_after_combining_sources(self):
        for index in range(3):
            self.make_recommendation(
                title=f"Teacher {index}",
                priority="normal",
            )

        automatic = [
            {
                "id": f"system:{index}",
                "source": "system",
                "kind": "continue_learning",
                "title": f"System {index}",
                "message": "Continue.",
                "reason": None,
                "priority": "low",
                "topic": None,
                "exercise": None,
                "created_at": None,
            }
            for index in range(5)
        ]

        with patch(
            "exercises.services.recommendation_feed."
            "build_automatic_recommendations",
            return_value=automatic,
        ) as automatic_builder:
            feed = build_recommendation_feed(self.student, limit=4)

        self.assertEqual(len(feed), 4)
        self.assertEqual(
            [item["source"] for item in feed],
            ["admin", "admin", "admin", "system"],
        )
        automatic_builder.assert_called_once_with(
            self.student,
            limit=10,
        )

    def test_missing_topic_and_exercise_are_serialized_as_none(self):
        self.make_recommendation(
            topic=None,
            exercise=None,
        )

        with patch(
            "exercises.services.recommendation_feed."
            "build_automatic_recommendations",
            return_value=[],
        ):
            feed = build_recommendation_feed(self.student)

        self.assertIsNone(feed[0]["topic"])
        self.assertIsNone(feed[0]["exercise"])

    def test_none_student_returns_empty_feed(self):
        with patch(
            "exercises.services.recommendation_feed."
            "build_automatic_recommendations",
        ) as automatic_builder:
            feed = build_recommendation_feed(None)

        self.assertEqual(feed, [])
        automatic_builder.assert_not_called()
