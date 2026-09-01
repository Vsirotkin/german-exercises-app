from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from .models import Topic, Exercise, VocabularyCard, Student, ExerciseResult
from .serializers import ExerciseSerializer


class BaseTestCase(TestCase):
    """Базовый класс для настройки общих данных тестов"""
    
    def setUp(self):
        # 1. Создаем пользователя и студента
        self.user = User.objects.create_user(
            username="testuser", 
            password="testpassword123",
            email="test@example.com"
        )
        self.student = Student.objects.create(
            user=self.user,
            first_name="Test",
            last_name="Student",
            email="test@example.com",
            level="A2"
        )
        
        # 2. Создаем темы
        self.topic = Topic.objects.create(name="Krankenhaus", description="Hospital")
        
        # 3. Создаем два упражнения для проверки логики блокировки (order важен!)
        self.exercise_1 = Exercise.objects.create(
            title="Exercise 1 (Base)",
            exercise_type="vocabulary_drill",
            language="german",
            is_active=True,
            order=1
        )
        self.exercise_1.topics.add(self.topic)
        
        self.exercise_2 = Exercise.objects.create(
            title="Exercise 2 (Should be locked if Ex 1 fails)",
            exercise_type="vocabulary_drill",
            language="german",
            is_active=True,
            order=2
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
            order=1
        )


class ExerciseSerializerLogicTest(BaseTestCase):
    """Тесты бизнес-логики сериализатора (score, status, is_locked)"""

    def test_is_locked_when_previous_exercise_failed(self):
        """Если предыдущее упражнение набрало < 50%, следующее должно быть заблокировано"""
        # Создаем результат для Exercise 1 с оценкой 40% (2 из 5)
        ExerciseResult.objects.create(
            student=self.student,
            exercise=self.exercise_1,
            score=2,
            total_questions=5,
            details={"answers": []}
        )
        
        # Сериализуем Exercise 2 от лица студента
        class MockRequest:
            user = self.user
            is_authenticated = True
            
        serializer_ex2 = ExerciseSerializer(self.exercise_2, context={'request': MockRequest()})
        serializer_ex1 = ExerciseSerializer(self.exercise_1, context={'request': MockRequest()})
        
        # Проверяем is_locked для Exercise 2 (должен быть заблокирован)
        self.assertTrue(serializer_ex2.data['is_locked'], "Упражнение 2 должно быть заблокировано")
        # Проверяем status для Exercise 1 (должен быть needs_review)
        self.assertEqual(serializer_ex1.data['status'], "needs_review")

    def test_is_unlocked_when_previous_exercise_passed(self):
        """Если предыдущее упражнение набрало >= 50%, следующее доступно"""
        # Создаем результат для Exercise 1 с оценкой 80% (4 из 5)
        ExerciseResult.objects.create(
            student=self.student,
            exercise=self.exercise_1,
            score=4,
            total_questions=5,
            details={"answers": []}
        )
        
        class MockRequest:
            user = self.user
            is_authenticated = True
            
        serializer_ex2 = ExerciseSerializer(self.exercise_2, context={'request': MockRequest()})
        serializer_ex1 = ExerciseSerializer(self.exercise_1, context={'request': MockRequest()})
        
        # Проверяем is_locked для Exercise 2 (должен быть доступен)
        self.assertFalse(serializer_ex2.data['is_locked'], "Упражнение 2 должно быть доступно")
        # Проверяем status для Exercise 1 (должен быть completed)
        self.assertEqual(serializer_ex1.data['status'], "completed")


class ExerciseAPITest(BaseTestCase):
    """Тесты HTTP-эндпоинтов"""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        # Получаем JWT токен для аутентифицированных запросов
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpassword123'
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_get_exercise_full_unauthenticated(self):
        """Публичный эндпоинт должен работать без токена"""
        self.client.credentials() # Сбрасываем авторизацию
        url = f"/api/exercises/{self.exercise_1.id}/full/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Exercise 1 (Base)")
        self.assertEqual(len(response.data['vocabulary_cards']), 1)

    def test_post_exercise_result_authenticated(self):
        """Аутентифицированный пользователь может сохранить результат"""
        url = "/api/results/"
        payload = {
            "exercise": self.exercise_1.id,
            "score": 5,
            "total_questions": 5,
            "details": {"correct": ["der Arzt"]}
        }
        
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExerciseResult.objects.count(), 1)
        # Проверяем, что студент привязался автоматически из токена
        self.assertEqual(ExerciseResult.objects.first().student, self.student)

    def test_import_exercise_requires_auth(self):
        """Импорт упражнений должен требовать авторизации"""
        self.client.credentials() # Сбрасываем авторизацию
        url = "/api/admin/exercises/import/"
        payload = {
            "title": "Test Import",
            "exercise_type": "gap_fill",
            "topics": ["Test"],
            "sentences": []
        }
        
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
