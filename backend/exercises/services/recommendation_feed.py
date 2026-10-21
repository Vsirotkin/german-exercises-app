"""Combined feed of teacher-created and automatic recommendations."""

from exercises.models import TeacherRecommendation
from exercises.services.recommendations import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    build_automatic_recommendations,
)


PRIORITY_ORDER = {
    "high": 0,
    "normal": 1,
    "low": 2,
}


def _topic_data(topic):
    if topic is None:
        return None

    return {
        "id": topic.id,
        "name": topic.name,
    }


def _exercise_data(exercise):
    if exercise is None:
        return None

    return {
        "id": exercise.id,
        "title": exercise.title,
        "exercise_type": exercise.exercise_type,
        "level": exercise.level,
    }


def _serialize_teacher_recommendation(recommendation):
    return {
        "id": f"admin:{recommendation.id}",
        "source": "admin",
        "kind": "teacher_advice",
        "title": recommendation.title,
        "message": recommendation.message,
        "reason": recommendation.reason,
        "priority": recommendation.priority,
        "topic": _topic_data(recommendation.topic),
        "exercise": _exercise_data(recommendation.exercise),
        "created_at": recommendation.created_at,
    }


def build_recommendation_feed(student, limit=DEFAULT_LIMIT):
    """Return teacher-created recommendations before automatic ones."""
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT

    limit = min(max(limit, 1), MAX_LIMIT)

    if student is None:
        return []

    teacher_recommendations = list(
        TeacherRecommendation.objects.filter(
            student=student,
            is_active=True,
        )
        .select_related("topic", "exercise")
        .order_by("-created_at", "-id")
    )

    teacher_recommendations.sort(
        key=lambda recommendation: (
            PRIORITY_ORDER.get(recommendation.priority, 99),
            -recommendation.created_at.timestamp(),
            -recommendation.id,
        )
    )

    teacher_data = [
        _serialize_teacher_recommendation(recommendation)
        for recommendation in teacher_recommendations
    ]

    automatic_data = build_automatic_recommendations(
        student,
        limit=MAX_LIMIT,
    )

    automatic_data.sort(
        key=lambda recommendation: (
            PRIORITY_ORDER.get(recommendation["priority"], 99),
        )
    )

    return (teacher_data + automatic_data)[:limit]
