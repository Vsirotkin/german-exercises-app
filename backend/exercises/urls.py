# exercises/urls.py

from django.urls import path
from .views import (
    ExerciseDetailView,
    ExerciseImportView,
    StudentRecommendationsView,
    CurrentUserView,
    ExerciseListView,
    StudentProgressView,
    StudentHistoryView,
    ExerciseResultView,
)

urlpatterns = [
    # Me
    path("me/", CurrentUserView.as_view(), name="current-user"),
    
    # Exercises
    path("exercises/", ExerciseListView.as_view(), name="exercise-list"),
    path("exercises/<int:pk>/full/", ExerciseDetailView.as_view(), name="exercise-detail-full"),
    
    # Admin
    path("admin/exercises/import/", ExerciseImportView.as_view(), name="exercise-import"),
    
    # Recommendations
    path("recommendations/student/topics/", StudentRecommendationsView.as_view(), name="student-recommendations"),
    
    # ✅ RESULTS (Исправленный порядок: специфичные → общие)
    
    # 1. Сначала специфичные маршруты с параметрами
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
    
    # 2. Потом общий маршрут для создания (POST)
    path(
        "results/",
        ExerciseResultView.as_view(),
        name="exercise-result-create",
    ),
]