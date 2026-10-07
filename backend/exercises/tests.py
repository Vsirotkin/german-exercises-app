from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from .models import Topic, Exercise, VocabularyCard, Student, ExerciseResult
from .serializers import ExerciseSerializer, ExerciseListSerializer


class BaseTestCase(TestCase):
    """Базовый класс для настройки общих данных тестов."""

    def setUp(self):
        # 1. Создаем пользователя и студента
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
            email="test@example.com",
        )
        self.student = Student.objects.create(
            user=self.user,
            first_name="Test",
            last_name="Student",
            email="test@example.com",
            level="A2",
        )

        # 2. Создаем темы
        self.topic = Topic.objects.create(
            name="Krankenhaus",
            description="Hospital",
        )

        # 3. Создаем два упражнения для проверки логики блокировки
        # (order важен!)
        self.exercise_1 = Exercise.objects.create(
            title="Exercise 1 (Base)",
            exercise_type="vocabulary_drill",
            language="german",
            is_active=True,
            order=1,
        )
        self.exercise_1.topics.add(self.topic)

        self.exercise_2 = Exercise.objects.create(
            title="Exercise 2 (Should be locked if Ex 1 fails)",
            exercise_type="vocabulary_drill",
            language="german",
            is_active=True,
            order=2,
        )
        self.exercise_2.topics.add(self.topic)

        # 4. Создаем карточки для первого упражнения
        VocabularyCard.objects.create(
            exercise=self.exercise_1,
            word="der Arzt",
            correct_translation="врач",
            distractor_1="аптекарь",
            distractor_2="пациент",
            distractor_3="медсестра",
            order=1,
        )


class ExerciseSerializerLogicTest(BaseTestCase):
    """Тесты бизнес-логики сериализатора."""

    def test_is_locked_when_previous_exercise_failed(self):
        """Если предыдущее упражнение набрало < 50%, следующее заблокировано."""
        ExerciseResult.objects.create(
            student=self.student,
            exercise=self.exercise_1,
            score=2,
            total_questions=5,
            details={"answers": []},
        )

        class MockRequest:
            user = self.user
            is_authenticated = True

        serializer_ex2 = ExerciseSerializer(
            self.exercise_2,
            context={"request": MockRequest()},
        )
        serializer_ex1 = ExerciseSerializer(
            self.exercise_1,
            context={"request": MockRequest()},
        )

        self.assertTrue(
            serializer_ex2.data["is_locked"],
            "Упражнение 2 должно быть заблокировано",
        )
        self.assertEqual(
            serializer_ex1.data["status"],
            "needs_review",
        )

    def test_is_unlocked_when_previous_exercise_passed(self):
        """Если предыдущее упражнение набрало >= 50%, следующее доступно."""
        ExerciseResult.objects.create(
            student=self.student,
            exercise=self.exercise_1,
            score=4,
            total_questions=5,
            details={"answers": []},
        )

        class MockRequest:
            user = self.user
            is_authenticated = True

        serializer_ex2 = ExerciseSerializer(
            self.exercise_2,
            context={"request": MockRequest()},
        )
        serializer_ex1 = ExerciseSerializer(
            self.exercise_1,
            context={"request": MockRequest()},
        )

        self.assertFalse(
            serializer_ex2.data["is_locked"],
            "Упражнение 2 должно быть доступно",
        )
        self.assertEqual(
            serializer_ex1.data["status"],
            "completed",
        )

    def test_list_serializer_contains_learning_state(self):
        """List serializer должен отдавать состояние обучения студента."""
        ExerciseResult.objects.create(
            student=self.student,
            exercise=self.exercise_1,
            score=4,
            total_questions=5,
            details={"answers": []},
        )

        class MockRequest:
            user = self.user
            is_authenticated = True

        serializer = ExerciseListSerializer(
            self.exercise_1,
            context={"request": MockRequest()},
        )

        self.assertEqual(serializer.data["score"], 80)
        self.assertEqual(serializer.data["status"], "completed")
        self.assertFalse(serializer.data["is_locked"])
        self.assertEqual(serializer.data["topics"], ["Krankenhaus"])

    def test_list_serializer_does_not_include_full_exercise_content(self):
        """List serializer не должен содержать полное содержимое упражнения."""

        class MockRequest:
            user = self.user
            is_authenticated = True

        serializer = ExerciseListSerializer(
            self.exercise_1,
            context={"request": MockRequest()},
        )

        self.assertNotIn("vocabulary_cards", serializer.data)
        self.assertNotIn("sentences", serializer.data)


class ExerciseAPITest(BaseTestCase):
    """Тесты HTTP-эндпоинтов."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Получаем JWT токен для аутентифицированных запросов
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "testpassword123",
            },
            format="json",
        )

        self.token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_get_exercises_list_authenticated(self):
        """Аутентифицированный пользователь получает краткий список упражнений."""
        url = "/api/exercises/"
        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(len(response.data), 2)

        exercise = response.data[0]

        self.assertEqual(
            exercise["title"],
            "Exercise 1 (Base)",
        )
        self.assertEqual(
            exercise["topics"],
            ["Krankenhaus"],
        )
        self.assertIn("score", exercise)
        self.assertIn("status", exercise)
        self.assertIn("is_locked", exercise)

        self.assertNotIn("vocabulary_cards", exercise)
        self.assertNotIn("sentences", exercise)

    def test_get_exercises_list_unauthenticated(self):
        """Список упражнений требует авторизации."""
        self.client.credentials()

        url = "/api/exercises/"
        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_get_exercise_full_unauthenticated(self):
        """Публичный эндпоинт должен работать без токена."""
        self.client.credentials()

        url = f"/api/exercises/{self.exercise_1.id}/full/"
        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["title"],
            "Exercise 1 (Base)",
        )
        self.assertEqual(
            len(response.data["vocabulary_cards"]),
            1,
        )

    def test_post_exercise_result_authenticated(self):
        """Аутентифицированный пользователь может сохранить результат."""
        url = "/api/results/"
        payload = {
            "exercise": self.exercise_1.id,
            "score": 5,
            "total_questions": 5,
            "details": {"correct": ["der Arzt"]},
        }

        response = self.client.post(
            url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            ExerciseResult.objects.count(),
            1,
        )

        # Проверяем, что студент привязался автоматически из токена
        self.assertEqual(
            ExerciseResult.objects.first().student,
            self.student,
        )

    def test_import_exercise_requires_auth(self):
        """Импорт упражнений должен требовать авторизацию."""
        self.client.credentials()

        url = "/api/admin/exercises/import/"
        payload = {
            "title": "Test Import",
            "exercise_type": "gap_fill",
            "topics": ["Test"],
            "sentences": [],
        }

        response = self.client.post(
            url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
