from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg, Count, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Exercise,
    ExerciseResult,
    MultipleChoiceItem,
    Student,
    Topic,
)
from .serializers import (
    ExerciseListSerializer,
    ExerciseSerializer,
    ExerciseCreateSerializer,
    ExerciseResultSerializer,
)
from .services.exercise_import import (
    ExerciseImportService,
    ExerciseImportValidationError,
)

from .services.evaluator import (
    EvaluationError,
    evaluate_answers,
)

from .services.recommendations import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
)
from .services.recommendation_feed import build_recommendation_feed

# ============================================================
# 1. Получение полного упражнения
# ============================================================


class ExerciseDetailView(APIView):
    """
    GET /api/exercises/<id>/full/

    Возвращает полное упражнение в безопасном формате.

    ВАЖНО:
    Правильные ответы и другие данные, позволяющие определить
    правильное решение, не должны попадать во frontend.
    """

    permission_classes = [AllowAny]

    def get(self, request, pk):
        exercise = get_object_or_404(
            Exercise.objects.prefetch_related("topics"),
            pk=pk,
            is_active=True,
        )

        serializer = ExerciseSerializer(
            exercise,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# 2. Импорт упражнения
# ============================================================


class ExerciseImportView(APIView):
    """
    POST /api/admin/exercises/import/

    Создание упражнения через API.

    Полная структура создания будет определяться
    новым ExerciseCreateSerializer.

    Доступ только для staff/admin пользователей.
    """

    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request):
        serializer = ExerciseCreateSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            exercise = serializer.save()

            response_serializer = ExerciseSerializer(
                exercise,
                context={"request": request},
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class ExerciseImportValidateView(APIView):
    """
    POST /api/admin/exercises/import/validate/

    Проверяет JSON упражнения без записи в базу данных.

    Доступ только для staff/admin пользователей.

    Возвращает:

        {
            "valid": true/false,
            "errors": [...],
            "summary": {...}
        }

    ВАЖНО:
    Валидация выполняется через ExerciseImportService.
    View не содержит собственной бизнес-логики валидации.
    """

    permission_classes = [IsAdminUser]

    def post(self, request):
        service = ExerciseImportService()

        preview = service.preview(request.data)

        return Response(
            preview,
            status=status.HTTP_200_OK,
        )


class ExerciseBatchImportView(APIView):
    """
    POST /api/admin/exercises/import/batch/

    Пакетный импорт JSON-документа упражнений через ExerciseImportService.
    Доступ только для staff/admin пользователей.

    Возвращает:
        Успех: 201 {"imported_count": N}
        Ошибка валидации: 400 {"errors": [...]}
    """

    permission_classes = [IsAdminUser]

    def post(self, request):
        service = ExerciseImportService()
        try:
            count = service.import_exercises(request.data)
        except ExerciseImportValidationError as exc:
            return Response(
                {"errors": exc.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"imported_count": count},
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# 3. Рекомендации студента
# ============================================================


class StudentRecommendationsView(APIView):
    """
    GET /api/recommendations/student/topics/

    Пока возвращает список доступных тем.

    Алгоритм рекомендаций подключим позже на основе:
    - StudentTopicProgress
    - истории ExerciseResult
    - mastery_level
    - уровня студента
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        topics = Topic.objects.all().order_by("name")

        data = [
            {
                "id": topic.id,
                "name": topic.name,
                "description": topic.description,
            }
            for topic in topics
        ]

        return Response(
            {"recommendations": data},
            status=status.HTTP_200_OK,
        )



class RecommendationsView(APIView):
    """
    GET /api/recommendations/

    Returns automatic recommendations for the authenticated student's
    own profile. Teacher-created recommendations will be merged here
    in a later implementation step.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        raw_limit = request.query_params.get("limit")
        limit = DEFAULT_LIMIT

        if raw_limit is not None:
            try:
                limit = int(raw_limit)
            except (TypeError, ValueError):
                return Response(
                    {
                        "error": {
                            "code": "INVALID_LIMIT",
                            "message": "limit must be a positive integer.",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if limit < 1:
                return Response(
                    {
                        "error": {
                            "code": "INVALID_LIMIT",
                            "message": "limit must be at least 1.",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            limit = min(limit, MAX_LIMIT)

        student = get_student_for_user(request.user)
        if student is None:
            return Response(
                {
                    "error": {
                        "code": "STUDENT_PROFILE_NOT_FOUND",
                        "message": (
                            "Student profile was not found "
                            "for the current user."
                        ),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "generated_at": timezone.now(),
                "recommendations": build_recommendation_feed(
                    student,
                    limit=limit,
                ),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# 4. Текущий пользователь
# ============================================================


def is_admin_user(user):
    """Проверяет административные права в соответствии с /api/me/."""
    return bool(
        user
        and user.is_authenticated
        and (user.is_staff or user.is_superuser)
    )


def get_accessible_student(user, student_id):
    """
    Возвращает профиль по Student.id, если пользователь имеет право
    просматривать его статистику.

    Ученику доступен только профиль, связанный с его Django User.
    Администратору доступны все профили, включая ещё не привязанные
    к учётной записи.
    """
    student = Student.objects.filter(pk=student_id).first()

    if student is None:
        return None

    if is_admin_user(user) or student.user_id == user.id:
        return student

    return None


class CurrentUserView(APIView):
    """
    GET /api/me/

    Возвращает текущего Django-пользователя и ID его профиля Student.
    student_id равен null, если профиль не связан с пользователем.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        student_id = Student.objects.filter(user=user).values_list(
            "id",
            flat=True,
        ).first()

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name or user.username,
                "last_name": user.last_name,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "role": (
                    "admin"
                    if is_admin_user(user)
                    else "student"
                ),
                "student_id": student_id,
            },
            status=status.HTTP_200_OK,
        )

# ============================================================
# 5. Список упражнений
# ============================================================


class ExerciseListView(ListAPIView):
    """
    GET /api/exercises/

    Возвращает активные упражнения в кратком формате.
    """

    queryset = (
        Exercise.objects.filter(is_active=True)
        .prefetch_related("topics")
        .order_by("order")
    )

    serializer_class = ExerciseListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# ============================================================
# 6. Вспомогательная функция поиска Student
# ============================================================


def get_student_for_user(user):
    """
    Возвращает Student, связанного с Django User.

    Если профиль Student ещё не существует, возвращает None.

    Мы сознательно не создаём Student автоматически здесь:
    создание/синхронизация профиля будет отдельным процессом.
    """

    try:
        return Student.objects.get(user=user)
    except Student.DoesNotExist:
        return None



# ============================================================
# 7. Прогресс ученика
# ============================================================


class StudentProgressView(APIView):
    """
    GET /api/results/student/<student_id>/progress/

    student_id здесь означает Student.id, а не Django User.id.

    Администратор может просматривать статистику любого профиля.
    Ученик может просматривать только собственную статистику.
    Для отсутствующего и недоступного профиля возвращается одинаковый 404.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        student = get_accessible_student(request.user, student_id)

        if student is None:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        results = ExerciseResult.objects.filter(student=student)
        statistics = results.aggregate(
            average_score=Avg("percentage"),
            best_score=Max("percentage"),
        )
        last_result = results.order_by("-completed_at").first()

        return Response(
            {
                "total_exercises": results.count(),
                "average_score": round(
                    statistics["average_score"] or 0,
                    1,
                ),
                "best_score": round(
                    statistics["best_score"] or 0,
                    1,
                ),
                "last_activity": (
                    last_result.completed_at
                    if last_result
                    else None
                ),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# 8. История ученика
# ============================================================


class StudentHistoryView(APIView):
    """
    GET /api/results/student/<student_id>/

    student_id означает Student.id.

    Администратор имеет доступ к истории любого профиля.
    Ученик имеет доступ только к собственной истории.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        student = get_accessible_student(request.user, student_id)

        if student is None:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        results = (
            ExerciseResult.objects.filter(student=student)
            .select_related("exercise")
            .order_by("-completed_at")[:20]
        )

        data = [
            {
                "id": result.id,
                "exercise": (
                    result.exercise.id
                    if result.exercise
                    else None
                ),
                "exercise_title": (
                    result.exercise.title
                    if result.exercise
                    else "Unknown"
                ),
                "score": result.score,
                "max_score": result.max_score,
                "percentage": result.percentage,
                "completed_at": result.completed_at,
            }
            for result in results
        ]

        return Response(data, status=status.HTTP_200_OK)


# ============================================================
# 9. Административный список учеников и сводная статистика
# ============================================================


class AdminStudentListView(APIView):
    """
    GET /api/admin/students/

    Только администратор может получить список профилей Student.

    id в каждой записи — это Student.id, используемый в endpoints
    прогресса и истории. Профили без выполненных упражнений тоже
    возвращаются с нулевыми показателями.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin_user(request.user):
            return Response(
                {
                    "detail": (
                        "You do not have permission to view this resource."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        students = (
            Student.objects.annotate(
                total_exercises=Count("results"),
                average_score=Avg("results__percentage"),
                best_score=Max("results__percentage"),
                last_activity=Max("results__completed_at"),
            )
            .order_by("last_name", "first_name", "id")
        )

        data = [
            {
                "id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "email": student.email,
                "level": student.level,
                "created_at": student.created_at,
                "total_exercises": student.total_exercises,
                "average_score": round(
                    student.average_score or 0,
                    1,
                ),
                "best_score": round(
                    student.best_score or 0,
                    1,
                ),
                "last_activity": student.last_activity,
            }
            for student in students
        ]

        return Response(data, status=status.HTTP_200_OK)

# ============================================================
# 9. Проверка ответов
# ============================================================


def _evaluate_answers(exercise, answers):
    """Delegate answer evaluation to the dedicated service."""
    return evaluate_answers(exercise, answers)


# ============================================================
# 10. Сохранение результата упражнения
# ============================================================


class ExerciseAnswerCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        exercise_id = request.data.get("exercise_id")
        item_id = request.data.get("item_id")
        if not exercise_id or not item_id or "answer" not in request.data:
            return Response({"error": {"code": "INVALID_ANSWER_CHECK",
                "message": "exercise_id, item_id and answer are required."}},
                status=status.HTTP_400_BAD_REQUEST)

        exercise = get_object_or_404(
            Exercise, pk=exercise_id, is_active=True,
            exercise_type="multiple_choice")
        item = get_object_or_404(
            MultipleChoiceItem, pk=item_id, exercise=exercise)

        if item.selection_mode != "single":
            return Response({"error": {"code": "UNSUPPORTED_SELECTION_MODE",
                "message": "Only single-choice cards are supported."}},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            evaluation = _evaluate_answers(exercise, [
                {"item_id": item.pk, "answer": request.data["answer"]}
            ])
        except EvaluationError as exc:
            return Response({"error": {"code": "INVALID_ANSWER",
                "message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        checked = next(r for r in evaluation["results"]
                       if r["item_id"] == item.pk)
        data = {"exercise_id": exercise.pk, "item_id": item.pk,
                "is_correct": checked["is_correct"]}
        if not checked["is_correct"]:
            data["correct_answer"] = item.options.filter(
                is_correct=True).values_list("text", flat=True).first()
        return Response(data, status=status.HTTP_200_OK)


class ExerciseResultView(APIView):
    """
    POST /api/results/

    Принимает ответы пользователя:

    {
        "exercise_id": 1,
        "answers": [
            {
                "item_id": 1,
                "answer": "a"
            }
        ]
    }

    Backend самостоятельно проверяет ответы.

    Frontend НЕ передаёт score/max_score/percentage.
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        exercise_id = request.data.get("exercise_id")
        answers = request.data.get("answers")

        if not exercise_id:
            return Response(
                {
                    "error": {
                        "code": "INVALID_EXERCISE_ID",
                        "message": "exercise_id is required.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(answers, list):
            return Response(
                {
                    "error": {
                        "code": "INVALID_ANSWERS",
                        "message": "answers must be an array.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        exercise = get_object_or_404(
            Exercise,
            pk=exercise_id,
            is_active=True,
        )

        student = get_student_for_user(request.user)

        if student is None:
            return Response(
                {
                    "error": {
                        "code": "STUDENT_PROFILE_NOT_FOUND",
                        "message": (
                            "Student profile was not found " "for the current user."
                        ),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Evaluation
        # ----------------------------------------------------

        try:
            evaluation = _evaluate_answers(
                exercise=exercise,
                answers=answers,
            )

        except EvaluationError as exc:
            return Response(
                {
                    "error": {
                        "code": "INVALID_ANSWERS",
                        "message": str(exc),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Save result
        # ----------------------------------------------------

        result = ExerciseResult.objects.create(
            student=student,
            exercise=exercise,
            score=evaluation["score"],
            max_score=evaluation["max_score"],
            percentage=evaluation["percentage"],
            details={
                "answers": answers,
                "results": evaluation.get("results", []),
            },
        )

        return Response(
            {
                "exercise_id": exercise.id,
                "score": result.score,
                "max_score": result.max_score,
                "percentage": result.percentage,
                "results": evaluation.get("results", []),
            },
            status=status.HTTP_201_CREATED,
        )
