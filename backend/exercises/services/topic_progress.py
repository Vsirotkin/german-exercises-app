from django.db.models import Max

from exercises.models import ExerciseResult, StudentTopicProgress


def update_student_topic_progress(student, exercise):
    """
    Recalculate progress for every topic associated with an exercise.

    Each exercise counts once per topic. Mastery is the average of the
    best percentage achieved on each distinct exercise in that topic.
    """
    for topic in exercise.topics.all():
        best_results = (
            ExerciseResult.objects.filter(
                student=student,
                exercise__topics=topic,
            )
            .values("exercise_id")
            .annotate(best_percentage=Max("percentage"))
        )

        best_percentages = [
            float(row["best_percentage"] or 0)
            for row in best_results
        ]

        if not best_percentages:
            continue

        completed_count = len(best_percentages)
        mastery_level = (
            sum(best_percentages) / completed_count / 100
        )

        StudentTopicProgress.objects.update_or_create(
            student=student,
            topic=topic,
            defaults={
                "exercises_completed": completed_count,
                "mastery_level": mastery_level,
            },
        )
