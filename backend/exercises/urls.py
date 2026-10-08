from django.urls import path

from .views import (
    CurrentUserView,
    ExerciseDetailView,
    ExerciseImportView,
    ExerciseListView,
    ExerciseResultView,
    StudentHistoryView,
    StudentProgressView,
    StudentRecommendationsView,
    ExerciseImportValidateView,
)

urlpatterns = [
    # --------------------------------------------------------
    # Current user
    # --------------------------------------------------------
    path(
        "me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),
    # --------------------------------------------------------
    # Exercises
    # --------------------------------------------------------
    path(
        "exercises/",
        ExerciseListView.as_view(),
        name="exercise-list",
    ),
    path(
        "exercises/<int:pk>/full/",
        ExerciseDetailView.as_view(),
        name="exercise-detail-full",
    ),
    # --------------------------------------------------------
    # Exercise import / administration
    # --------------------------------------------------------
    path(
        "admin/exercises/import/",
        ExerciseImportView.as_view(),
        name="exercise-import",
    ),
    # --------------------------------------------------------
    # Exercise import / validation
    # --------------------------------------------------------
    path(
        "admin/exercises/import/validate/",
        ExerciseImportValidateView.as_view(),
        name="exercise-import-validate",
    ),
    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------
    path(
        "recommendations/student/topics/",
        StudentRecommendationsView.as_view(),
        name="student-recommendations",
    ),
    # --------------------------------------------------------
    # Student progress / history
    # --------------------------------------------------------
    path(
        "results/student/<int:student_id>/progress/",
        StudentProgressView.as_view(),
        name="student-progress",
    ),
    path(
        "results/student/<int:student_id>/",
        StudentHistoryView.as_view(),
        name="student-history",
    ),
    # --------------------------------------------------------
    # Submit exercise result
    # --------------------------------------------------------
    path(
        "results/",
        ExerciseResultView.as_view(),
        name="exercise-result-create",
    ),
]
