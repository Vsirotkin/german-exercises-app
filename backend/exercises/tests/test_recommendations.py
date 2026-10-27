from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from exercises.models import Exercise, ExerciseResult, Student, Topic
from exercises.services.recommendations import (
    build_automatic_recommendations,
)


class AutomaticRecommendationServiceTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username="recommendation-student",
            password="testpassword123",
        )
        self.student = Student.objects.create(
            user=user,
            first_name="Test",
            last_name="Student",
            email="recommendation-student@example.com",
            level="A2",
        )

        self.topic = Topic.objects.create(
            name="Krankenhaus",
            description="Hospital",
        )
        self.other_topic = Topic.objects.create(
            name="Alltag",
            description="Everyday life",
        )

        self.exercise_1 = self.make_exercise(
            "Exercise 1",
            order=1,
            topics=[self.topic],
        )
        self.exercise_2 = self.make_exercise(
            "Exercise 2",
            order=2,
            topics=[self.topic],
        )
        self.exercise_3 = self.make_exercise(
            "Exercise 3",
            order=3,
            topics=[self.topic],
        )

    def make_exercise(
        self,
        title,
        order,
        topics=None,
        level="A1",
        active=True,
    ):
        exercise = Exercise.objects.create(
            title=title,
            exercise_type="vocabulary_drill",
            language="german",
            level=level,
            is_active=active,
            order=order,
        )
        if topics:
            exercise.topics.set(topics)
        return exercise

    def add_result(self, exercise, percentage, days_ago=0):
        result = ExerciseResult.objects.create(
            student=self.student,
            exercise=exercise,
            score=percentage,
            max_score=100,
            percentage=percentage,
            details={},
        )

        if days_ago:
            ExerciseResult.objects.filter(pk=result.pk).update(
                completed_at=timezone.now() - timedelta(days=days_ago),
            )
            result.refresh_from_db()

        return result

    def test_no_history_recommends_first_suitable_active_exercise(self):
        self.make_exercise(
            "Advanced exercise",
            order=0,
            level="B1",
        )
        self.make_exercise(
            "Inactive exercise",
            order=0,
            active=False,
        )

        recommendations = build_automatic_recommendations(self.student)

        self.assertEqual(len(recommendations), 1)
        recommendation = recommendations[0]
        self.assertEqual(recommendation["kind"], "start_learning")
        self.assertEqual(recommendation["priority"], "low")
        self.assertEqual(
            recommendation["exercise"]["id"],
            self.exercise_1.id,
        )

    def test_just_below_50_recommends_review(self):
        self.add_result(self.exercise_1, 49.99)

        recommendations = build_automatic_recommendations(self.student)

        self.assertEqual(recommendations[0]["kind"], "review_exercise")
        self.assertEqual(recommendations[0]["priority"], "high")

    def test_exactly_50_recommends_topic_practice(self):
        self.add_result(self.exercise_1, 50)

        recommendations = build_automatic_recommendations(self.student)

        self.assertEqual(recommendations[0]["kind"], "practice_topic")
        self.assertEqual(recommendations[0]["priority"], "normal")

    def test_just_below_80_recommends_topic_practice(self):
        self.add_result(self.exercise_1, 79.99)

        recommendations = build_automatic_recommendations(self.student)

        self.assertEqual(recommendations[0]["kind"], "practice_topic")
        self.assertEqual(recommendations[0]["priority"], "normal")

    def test_exactly_80_recommends_continuing_learning(self):
        self.add_result(self.exercise_1, 80)

        recommendations = build_automatic_recommendations(self.student)

        self.assertEqual(recommendations[0]["kind"], "continue_learning")
        self.assertEqual(recommendations[0]["priority"], "low")

    def test_result_below_50_recommends_repeating_same_exercise(self):
        self.add_result(self.exercise_1, 40)

        recommendations = build_automatic_recommendations(self.student)

        self.assertEqual(recommendations[0]["kind"], "review_exercise")
        self.assertEqual(recommendations[0]["priority"], "high")
        self.assertEqual(
            recommendations[0]["exercise"]["id"],
            self.exercise_1.id,
        )
        self.assertEqual(
            recommendations[0]["topic"]["id"],
            self.topic.id,
        )

    def test_result_from_50_to_79_recommends_another_same_topic_exercise(self):
        self.add_result(self.exercise_1, 65)

        recommendations = build_automatic_recommendations(self.student)

        self.assertEqual(recommendations[0]["kind"], "practice_topic")
        self.assertEqual(recommendations[0]["priority"], "normal")
        self.assertNotEqual(
            recommendations[0]["exercise"]["id"],
            self.exercise_1.id,
        )
        self.assertEqual(
            recommendations[0]["topic"]["id"],
            self.topic.id,
        )

    def test_practice_prefers_unattempted_candidate(self):
        self.add_result(self.exercise_1, 60)
        self.add_result(self.exercise_2, 70)

        recommendations = build_automatic_recommendations(self.student)

        self.assertTrue(recommendations)
        self.assertEqual(
            recommendations[0]["exercise"]["id"],
            self.exercise_3.id,
        )

    def test_practice_returns_nothing_without_another_shared_topic_exercise(self):
        self.exercise_2.topics.clear()
        self.exercise_3.topics.clear()
        self.add_result(self.exercise_1, 65)

        recommendations = build_automatic_recommendations(self.student)

        self.assertEqual(recommendations, [])


    def test_completed_practice_recommendation_is_not_repeated(self):
        self.exercise_3.delete()

        self.add_result(self.exercise_1, 60)
        first_feed = build_automatic_recommendations(self.student)

        self.assertEqual(len(first_feed), 1)
        self.assertEqual(
            first_feed[0]["exercise"]["id"],
            self.exercise_2.id,
        )

        self.add_result(self.exercise_2, 100)
        updated_feed = build_automatic_recommendations(self.student)

        self.assertEqual(updated_feed, [])


    def test_result_at_least_80_recommends_next_unattempted_exercise(self):
        self.add_result(self.exercise_1, 100)

        recommendations = build_automatic_recommendations(self.student)

        self.assertEqual(recommendations[0]["kind"], "continue_learning")
        self.assertEqual(recommendations[0]["priority"], "low")
        self.assertEqual(
            recommendations[0]["exercise"]["id"],
            self.exercise_2.id,
        )

    def test_latest_result_for_an_exercise_is_used(self):
        self.add_result(self.exercise_1, 30, days_ago=2)
        self.add_result(self.exercise_1, 90, days_ago=1)

        recommendations = build_automatic_recommendations(self.student)

        self.assertTrue(recommendations)
        self.assertEqual(
            recommendations[0]["kind"],
            "continue_learning",
        )
        self.assertEqual(
            recommendations[0]["exercise"]["id"],
            self.exercise_2.id,
        )

    def test_does_not_recommend_exercises_above_student_level(self):
        advanced = self.make_exercise(
            "Advanced exercise",
            order=0,
            topics=[self.topic],
            level="B1",
        )
        self.add_result(self.exercise_1, 100)

        recommendations = build_automatic_recommendations(self.student)

        self.assertTrue(recommendations)
        self.assertNotEqual(
            recommendations[0]["exercise"]["id"],
            advanced.id,
        )
        self.assertEqual(
            recommendations[0]["exercise"]["id"],
            self.exercise_2.id,
        )

    def test_returns_no_recommendation_when_no_suitable_next_step_exists(self):
        self.add_result(self.exercise_1, 100)
        self.add_result(self.exercise_2, 100)
        self.add_result(self.exercise_3, 100)

        recommendations = build_automatic_recommendations(self.student)

        self.assertEqual(recommendations, [])

    def test_limit_is_applied_and_capped_at_ten(self):
        self.add_result(self.exercise_1, 30)
        self.add_result(self.exercise_2, 35)
        self.add_result(self.exercise_3, 45)

        recommendations = build_automatic_recommendations(
            self.student,
            limit=2,
        )

        self.assertEqual(len(recommendations), 2)
        self.assertEqual(
            [item["priority"] for item in recommendations],
            ["high", "high"],
        )
