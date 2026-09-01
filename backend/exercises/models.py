from django.db import models
from django.contrib.auth.models import (
    User,
)  # Используем встроенную модель пользователя Django как базу для Student или связываем через ForeignKey


# 1. Темы (например, "Krankenhaus", "Uhrzeit")
class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название темы")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Темы"
        ordering = ["name"]


# 2. Ученики (Можно расширить встроенного User или сделать отдельную модель)
# В вашем summary была модель Student. Сделаем отдельную для гибкости, связанную с User (опционально)
class Student(models.Model):
    # Если ученик имеет доступ к системе, можно связать с User (one-to-one), иначе просто профиль
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    email = models.EmailField(unique=True, verbose_name="Email")
    level = models.CharField(
        max_length=10,
        default="A1",
        choices=[("A1", "A1"), ("A2", "A2"), ("B1", "B1"), ("B2", "B2")],
        verbose_name="Уровень",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"


# 3. Упражнения (Основная сущность)
class Exercise(models.Model):
    EXERCISE_TYPES = [
        ("vocabulary_drill", "Vocabulary Drill"),
        ("gap_fill", "Gap Fill"),
    ]

    title = models.CharField(max_length=200, verbose_name="Название упражнения")
    exercise_type = models.CharField(
        max_length=50, choices=EXERCISE_TYPES, verbose_name="Тип"
    )
    topics = models.ManyToManyField(
        Topic, related_name="exercises", verbose_name="Темы"
    )
    language = models.CharField(max_length=20, default="german", verbose_name="Язык")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    
    # 👇 НОВОЕ ПОЛЕ
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name="Порядок",
        help_text="Определяет последовательность упражнений"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_exercise_type_display()})"

    class Meta:
        verbose_name = "Упражнение"
        verbose_name_plural = "Упражнения"
        ordering = ["order"]  # 👇 Меняем сортировку по умолчанию


# 4. Карточки слов (Для vocabulary_drill)
class VocabularyCard(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="vocabulary_cards",
        verbose_name="Упражнение",
    )
    word = models.CharField(max_length=100, verbose_name="Слово (DE)")
    correct_translation = models.CharField(
        max_length=100, verbose_name="Правильный перевод"
    )
    distractor_1 = models.CharField(max_length=100, verbose_name="Дистрактор 1")
    distractor_2 = models.CharField(max_length=100, verbose_name="Дистрактор 2")
    distractor_3 = models.CharField(max_length=100, verbose_name="Дистрактор 3")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    def __str__(self):
        return f"{self.word} -> {self.correct_translation}"

    class Meta:
        verbose_name = "Карточка слова"
        verbose_name_plural = "Карточки слов"
        ordering = ["order"]


# 5. Предложения и опции (Для gap_fill)
class Sentence(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="sentences",
        verbose_name="Упражнение",
    )
    text = models.TextField(verbose_name="Текст предложения")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    def __str__(self):
        return self.text[:50]

    class Meta:
        verbose_name = "Предложение"
        verbose_name_plural = "Предложения"
        ordering = ["order"]


class GapOption(models.Model):
    sentence = models.ForeignKey(
        Sentence,
        on_delete=models.CASCADE,
        related_name="gap_options",
        verbose_name="Предложение",
    )
    placeholder_index = models.PositiveIntegerField(
        verbose_name="Индекс пропуска"
    )  # Какой по счету пропуск в тексте
    options = models.JSONField(
        verbose_name="Варианты ответов"
    )  # Список вариантов ["der Arzt", "die Apotheke"]
    correct_answer = models.CharField(max_length=100, verbose_name="Правильный ответ")

    def __str__(self):
        return f"Пропуск #{self.placeholder_index} в '{self.sentence.text[:20]}...'"

    class Meta:
        verbose_name = "Опция пропуска"
        verbose_name_plural = "Опции пропусков"


# 6. Результаты и прогресс
class ExerciseResult(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="results"
    )
    exercise = models.ForeignKey(
        Exercise, on_delete=models.CASCADE, related_name="results"
    )
    score = models.IntegerField(default=0, verbose_name="Баллы")
    total_questions = models.IntegerField(default=0, verbose_name="Всего вопросов")
    completed_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(
        default=dict, blank=True, verbose_name="Детали ответа"
    )  # Храним JSON с ответами

    def __str__(self):
        return f"{self.student} - {self.exercise.title} ({self.score}/{self.total_questions})"

    class Meta:
        verbose_name = "Результат упражнения"
        verbose_name_plural = "Результаты упражнений"
        ordering = ["-completed_at"]


class StudentTopicProgress(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="topic_progress"
    )
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="student_progress"
    )
    exercises_completed = models.IntegerField(
        default=0, verbose_name="Выполнено упражнений"
    )
    last_practiced = models.DateTimeField(
        auto_now=True, verbose_name="Последняя практика"
    )
    mastery_level = models.FloatField(
        default=0.0, verbose_name="Уровень освоения (0-1)"
    )

    def __str__(self):
        return f"{self.student} - {self.topic.name}"

    class Meta:
        verbose_name = "Прогресс по теме"
        verbose_name_plural = "Прогресс по темам"
        unique_together = ("student", "topic")
