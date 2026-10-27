"""Rule-based automatic recommendations derived from exercise results."""

from exercises.models import Exercise, ExerciseResult


LEVEL_ORDER = {
    "A1": 1,
    "A2": 2,
    "B1": 3,
    "B2": 4,
    "C1": 5,
    "C2": 6,
}

DEFAULT_LIMIT = 5
MAX_LIMIT = 10


def _normalise_limit(limit):
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT

    return min(max(limit, 1), MAX_LIMIT)


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


def _make_recommendation(
    *,
    recommendation_id,
    kind,
    title,
    message,
    reason,
    priority,
    topic,
    exercise,
):
    return {
        "id": recommendation_id,
        "source": "system",
        "kind": kind,
        "title": title,
        "message": message,
        "reason": reason,
        "priority": priority,
        "topic": _topic_data(topic),
        "exercise": _exercise_data(exercise),
        "created_at": None,
    }


def _format_percentage(value):
    return f"{float(value):g}%"


def build_automatic_recommendations(student, limit=DEFAULT_LIMIT):
    """
    Build deterministic recommendations for one Student.

    Rules use the latest result for each active exercise within the
    student's level. No recommendation records are persisted.
    """
    limit = _normalise_limit(limit)

    if student is None:
        return []

    student_level = LEVEL_ORDER.get(student.level, 1)
    suitable_levels = [
        level
        for level, rank in LEVEL_ORDER.items()
        if rank <= student_level
    ]

    exercises = list(
        Exercise.objects.filter(
            is_active=True,
            level__in=suitable_levels,
        )
        .prefetch_related("topics")
        .order_by("order", "title", "id")
    )

    if not exercises:
        return []

    exercise_by_id = {exercise.id: exercise for exercise in exercises}
    exercise_position = {
        exercise.id: position
        for position, exercise in enumerate(exercises)
    }

    topics_by_exercise = {}
    for exercise in exercises:
        topics = list(exercise.topics.all())
        topics.sort(key=lambda topic: (topic.name.casefold(), topic.id))
        topics_by_exercise[exercise.id] = topics

    all_results_exist = ExerciseResult.objects.filter(
        student=student,
    ).exists()

    if not all_results_exist:
        first_exercise = exercises[0]
        first_topic = (
            topics_by_exercise[first_exercise.id][0]
            if topics_by_exercise[first_exercise.id]
            else None
        )

        return [
            _make_recommendation(
                recommendation_id=(
                    f"system:start-exercise:{first_exercise.id}"
                ),
                kind="start_learning",
                title="Beginne mit der ersten Übung",
                message="Starte mit dieser Übung und baue deine Kenntnisse auf.",
                reason="Für dein Profil liegen noch keine Übungsergebnisse vor.",
                priority="low",
                topic=first_topic,
                exercise=first_exercise,
            )
        ][:limit]

    result_queryset = (
        ExerciseResult.objects.filter(
            student=student,
            exercise__is_active=True,
            exercise__level__in=suitable_levels,
        )
        .select_related("exercise")
        .order_by("-completed_at", "-id")
    )

    # Keep only the most recent result for each exercise.
    latest_results_by_exercise = {}
    for result in result_queryset:
        latest_results_by_exercise.setdefault(result.exercise_id, result)

    if not latest_results_by_exercise:
        return []

    latest_results = list(latest_results_by_exercise.values())
    attempted_exercise_ids = set(latest_results_by_exercise)
    selected_exercise_ids = set()
    recommendations = []

    weak_results = [
        result for result in latest_results if result.percentage < 50
    ]
    practice_results = [
        result
        for result in latest_results
        if 50 <= result.percentage < 80
    ]
    strong_results = [
        result for result in latest_results if result.percentage >= 80
    ]

    # High-priority recommendations: repeat exercises with results below 50%.
    for result in weak_results:
        exercise = exercise_by_id.get(result.exercise_id)
        if exercise is None or exercise.id in selected_exercise_ids:
            continue

        topics = topics_by_exercise[exercise.id]
        topic = topics[0] if topics else None
        percentage = _format_percentage(result.percentage)

        recommendations.append(
            _make_recommendation(
                recommendation_id=f"system:review-exercise:{exercise.id}",
                kind="review_exercise",
                title="Übung wiederholen",
                message="Wiederhole diese Übung, um das Thema besser zu festigen.",
                reason=(
                    f"Dein letztes Ergebnis für „{exercise.title}“: "
                    f"{percentage}."
                ),
                priority="high",
                topic=topic,
                exercise=exercise,
            )
        )
        selected_exercise_ids.add(exercise.id)

    # Normal-priority recommendations: practise the same topic in another exercise.
    for result in practice_results:
        source_exercise = exercise_by_id.get(result.exercise_id)
        if source_exercise is None:
            continue

        source_topics = topics_by_exercise[source_exercise.id]
        source_topic_ids = {topic.id for topic in source_topics}
        if not source_topic_ids:
            continue

        candidates = []
        for candidate in exercises:
            if candidate.id == source_exercise.id:
                continue

            matching_topics = [
                topic
                for topic in topics_by_exercise[candidate.id]
                if topic.id in source_topic_ids
            ]
            if matching_topics:
                candidates.append((candidate, matching_topics))

        # Prefer exercises without a previous result, then catalog order.
        candidates.sort(
            key=lambda pair: (
                pair[0].id in attempted_exercise_ids,
                pair[0].order,
                pair[0].title.casefold(),
                pair[0].id,
            )
        )

        chosen = next(
            (
                (candidate, matching_topics)
                for candidate, matching_topics in candidates
                if candidate.id not in attempted_exercise_ids
                and candidate.id not in selected_exercise_ids
            ),
            None,
        )
        if chosen is None:
            continue

        exercise, matching_topics = chosen
        topic = matching_topics[0]
        percentage = _format_percentage(result.percentage)

        recommendations.append(
            _make_recommendation(
                recommendation_id=(
                    f"system:practice-topic:{topic.id}:{exercise.id}"
                ),
                kind="practice_topic",
                title="Weiter zum Thema üben",
                message=(
                    "Bearbeite eine weitere Übung zu diesem Thema."
                ),
                reason=(
                    f"Dein letztes Ergebnis für „{source_exercise.title}“: "
                    f"{percentage}."
                ),
                priority="normal",
                topic=topic,
                exercise=exercise,
            )
        )
        selected_exercise_ids.add(exercise.id)

    # Low-priority recommendations: continue with the next suitable,
    # active exercise that has not yet been attempted.
    for result in strong_results:
        source_exercise = exercise_by_id.get(result.exercise_id)
        if source_exercise is None:
            continue

        position = exercise_position[source_exercise.id]
        next_exercise = next(
            (
                candidate
                for candidate in exercises[position + 1:]
                if candidate.id not in attempted_exercise_ids
                and candidate.id not in selected_exercise_ids
            ),
            None,
        )
        if next_exercise is None:
            continue

        topics = topics_by_exercise[next_exercise.id]
        topic = topics[0] if topics else None
        percentage = _format_percentage(result.percentage)

        recommendations.append(
            _make_recommendation(
                recommendation_id=(
                    f"system:continue-exercise:{next_exercise.id}"
                ),
                kind="continue_learning",
                title="Mit der nächsten Übung fortfahren",
                message=(
                    "Du hast dieses Ergebnis erreicht. "
                    "Fahre mit der nächsten passenden Übung fort."
                ),
                reason=(
                    f"Dein letztes Ergebnis für „{source_exercise.title}“: "
                    f"{percentage}."
                ),
                priority="low",
                topic=topic,
                exercise=next_exercise,
            )
        )
        selected_exercise_ids.add(next_exercise.id)

    return recommendations[:limit]
