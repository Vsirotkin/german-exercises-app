from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import transaction

from django.db.models import Avg, Max, Count

from .models import Exercise, Topic, VocabularyCard, Sentence, GapOption, ExerciseResult, Student
from .serializers import ExerciseSerializer, ExerciseCreateSerializer, ExerciseResultSerializer


# --- 1. Получение полного упражнения ---
class ExerciseDetailView(APIView):
    """
    GET /exercises/{id}/full/
    Возвращает полное упражнение со всеми вложенными данными (карточки или предложения).
    Доступно всем (или только авторизованным, если нужно).
    """

    permission_classes = [AllowAny]  # Пока откроем для всех, потом можно закрыть

    def get(self, request, pk):
        exercise = get_object_or_404(Exercise, pk=pk, is_active=True)
        # 👇 Передаём request в контекст для расчёта статуса студента
        serializer = ExerciseSerializer(exercise, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- 2. Импорт упражнений (Admin only) ---
class ExerciseImportView(APIView):
    """
    POST /admin/exercises/import/
    Принимает JSON структуру (как в примере migration_summary) и создает упражнение.
    Требует аутентификации.
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = ExerciseCreateSerializer(data=request.data)

        if serializer.is_valid():
            exercise = serializer.save()
            # Возвращаем созданное упражнение в том же формате
            # 👇 Передаём request в контекст
            response_serializer = ExerciseSerializer(exercise, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- 3. Рекомендации (Заглушка для примера) ---
class StudentRecommendationsView(APIView):
    """
    GET /recommendations/student/topics/
    Возвращает темы для студента на основе прогресса.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Здесь будет логика выбора тем на основе StudentTopicProgress
        # Пока вернем пустой список или все активные темы для теста
        topics = Topic.objects.all()
        data = [{"id": t.id, "name": t.name} for t in topics]
        return Response({"recommendations": data}, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    """
    GET /api/me/
    Возвращает профиль текущего пользователя на основе JWT токена.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name
                or user.username,  # Если имени нет, берем логин
                "last_name": user.last_name,
                "email": user.email,
                "is_staff": user.is_staff,  # Это флаг админки Django
                "is_superuser": user.is_superuser,
                # Определяем роль для фронта: если staff или superuser -> admin, иначе student
                "role": "admin" if (user.is_staff or user.is_superuser) else "student",
            }
        )


class ExerciseListView(ListAPIView):
    """
    GET /api/exercises/
    Возвращает список всех активных упражнений (краткая информация).
    """

    queryset = (
        Exercise.objects.filter(is_active=True)
        .prefetch_related("topics")
        .order_by("order")  # 👇 Сортируем по порядку
    )
    serializer_class = ExerciseSerializer

    # 👇 Передаём request в контекст сериализатора
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class StudentProgressView(APIView):
    """
    GET /api/results/student/<id>/progress/
    Возвращает агрегированную статистику студента.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        # Конвертируем user_id → student_id
        try:
            student = Student.objects.get(user_id=student_id)
        except Student.DoesNotExist:
            return Response({
                "total_exercises": 0,
                "average_score": 0,
                "best_score": 0,
                "last_activity": None,
            })

        # 👇 Получаем все результаты студента
        results = ExerciseResult.objects.filter(
            student=student, 
            total_questions__gt=0  # Исключаем деление на ноль
        )

        if not results.exists():
            return Response({
                "total_exercises": 0,
                "average_score": 0,
                "best_score": 0,
                "last_activity": None,
            })

        # 👇 Рассчитываем проценты для каждого результата
        percentages = [
            (r.score / r.total_questions) * 100 
            for r in results
        ]

        # 👇 Считаем среднее и максимум из процентов
        average_score = sum(percentages) / len(percentages)
        best_score = max(percentages)

        return Response({
            "total_exercises": results.count(),
            "average_score": round(average_score, 1),  # 👈 Округляем до 1 знака
            "best_score": round(best_score, 1),
            "last_activity": results.order_by('-completed_at').first().completed_at,
        })


class StudentHistoryView(APIView):
    """
    GET /api/results/student/<id>/
    Возвращает список последних результатов (история).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        # Конвертируем user_id → student_id
        try:
            student = Student.objects.get(user_id=student_id)
        except Student.DoesNotExist:
            return Response([])

        results = (
            ExerciseResult.objects.filter(student=student)
            .select_related("exercise")
            .order_by("-completed_at")[:20]
        )

        data = []
        for res in results:
            # Рассчитываем процент, если есть вопросы
            score_percent = None
            if res.total_questions and res.total_questions > 0:
                score_percent = (res.score / res.total_questions) * 100

            data.append({
                "id": res.id,
                "exercise": res.exercise.id if res.exercise else None,
                "exercise_title": res.exercise.title if res.exercise else "Unknown",
                "score": round(score_percent, 1) if score_percent is not None else None,  # ✅ Процент 0-100
                "total_questions": res.total_questions,
                "completed_at": res.completed_at,
            })

        return Response(data)


# === 8. Сохранение результата упражнения ===
class ExerciseResultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Передаём request в контекст сериализатора
        serializer = ExerciseResultSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
