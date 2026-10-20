import uuid

from django.db import models
from django.contrib.auth.models import User

LEVEL_CHOICES = [
    ("A1", "A1"),
    ("A2", "A2"),
    ("B1", "B1"),
    ("B2", "B2"),
    ("C1", "C1"),
    ("C2", "C2"),
]


class Topic(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название темы",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Темы"
        ordering = ["name"]


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    first_name = models.CharField(
        max_length=50,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name="Фамилия",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Уровень",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"


class Exercise(models.Model):
    EXERCISE_TYPES = [
        ("vocabulary_drill", "Vocabulary Drill"),
        ("multiple_choice", "Multiple Choice"),
        ("dropdown", "Dropdown"),
        ("gap_fill", "Gap Fill"),
        ("sentence_builder", "Sentence Builder"),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name="Название упражнения",
    )
    exercise_type = models.CharField(
        max_length=50,
        choices=EXERCISE_TYPES,
        verbose_name="Тип",
    )
    topics = models.ManyToManyField(
        Topic,
        related_name="exercises",
        verbose_name="Темы",
    )
    language = models.CharField(
        max_length=20,
        default="german",
        verbose_name="Язык",
    )
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default="A1",
        verbose_name="Уровень",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
        help_text="Определяет последовательность упражнений",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_exercise_type_display()})"

    class Meta:
        verbose_name = "Упражнение"
        verbose_name_plural = "Упражнения"
        ordering = ["order"]


class VocabularyItem(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="vocabulary_items",
        verbose_name="Упражнение",
    )
    prompt = models.CharField(
        max_length=200,
        verbose_name="Задание",
    )
    correct_answer = models.CharField(
        max_length=200,
        verbose_name="Правильный ответ",
    )
    distractor_1 = models.CharField(
        max_length=200,
        verbose_name="Дистрактор 1",
    )
    distractor_2 = models.CharField(
        max_length=200,
        verbose_name="Дистрактор 2",
    )
    distractor_3 = models.CharField(
        max_length=200,
        verbose_name="Дистрактор 3",
    )
    correct_option_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID правильного варианта",
    )
    distractor_1_option_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID дистрактора 1",
    )
    distractor_2_option_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID дистрактора 2",
    )
    distractor_3_option_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID дистрактора 3",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    def __str__(self):
        return f"{self.prompt} -> {self.correct_answer}"

    class Meta:
        verbose_name = "Элемент Vocabulary Drill"
        verbose_name_plural = "Элементы Vocabulary Drill"
        ordering = ["order"]


class MultipleChoiceItem(models.Model):
    SELECTION_MODES = [
        ("single", "Single"),
        ("multiple", "Multiple"),
    ]

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="multiple_choice_items",
        verbose_name="Упражнение",
    )
    question = models.TextField(
        verbose_name="Вопрос",
    )
    selection_mode = models.CharField(
        max_length=10,
        choices=SELECTION_MODES,
        default="single",
        verbose_name="Режим выбора",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    def __str__(self):
        return self.question[:80]

    class Meta:
        verbose_name = "Элемент Multiple Choice"
        verbose_name_plural = "Элементы Multiple Choice"
        ordering = ["order"]


class MultipleChoiceOption(models.Model):
    item = models.ForeignKey(
        MultipleChoiceItem,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Вопрос",
    )
    text = models.TextField(
        verbose_name="Текст варианта",
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name="Правильный",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    def __str__(self):
        return self.text[:80]

    class Meta:
        verbose_name = "Вариант Multiple Choice"
        verbose_name_plural = "Варианты Multiple Choice"
        ordering = ["order"]


class DropdownItem(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="dropdown_items",
        verbose_name="Упражнение",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    def __str__(self):
        return f"Dropdown #{self.pk}"

    class Meta:
        verbose_name = "Элемент Dropdown"
        verbose_name_plural = "Элементы Dropdown"
        ordering = ["order"]


class DropdownPart(models.Model):
    PART_TYPES = [
        ("text", "Text"),
        ("select", "Select"),
    ]

    item = models.ForeignKey(
        DropdownItem,
        on_delete=models.CASCADE,
        related_name="parts",
        verbose_name="Элемент",
    )
    part_type = models.CharField(
        max_length=10,
        choices=PART_TYPES,
        verbose_name="Тип части",
    )
    text = models.TextField(
        blank=True,
        default="",
        verbose_name="Текст",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    def __str__(self):
        return f"{self.get_part_type_display()} #{self.pk}"

    class Meta:
        verbose_name = "Часть Dropdown"
        verbose_name_plural = "Части Dropdown"
        ordering = ["order"]


class DropdownOption(models.Model):
    part = models.ForeignKey(
        DropdownPart,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Часть",
    )
    text = models.CharField(
        max_length=200,
        verbose_name="Текст варианта",
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name="Правильный",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Вариант Dropdown"
        verbose_name_plural = "Варианты Dropdown"
        ordering = ["order"]


class GapFillItem(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="gap_fill_items",
        verbose_name="Упражнение",
    )
    text = models.TextField(
        verbose_name="Текст задания",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    def __str__(self):
        return self.text[:80]

    class Meta:
        verbose_name = "Элемент Gap Fill"
        verbose_name_plural = "Элементы Gap Fill"
        ordering = ["order"]


class GapFillGap(models.Model):
    item = models.ForeignKey(
        GapFillItem,
        on_delete=models.CASCADE,
        related_name="gaps",
        verbose_name="Элемент",
    )
    placeholder = models.CharField(
        max_length=50,
        verbose_name="Идентификатор пропуска",
        help_text='Например: "gap_1"',
    )
    correct_answer = models.CharField(
        max_length=200,
        verbose_name="Правильный ответ",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    def __str__(self):
        return f"{self.placeholder}: {self.correct_answer}"

    class Meta:
        verbose_name = "Пропуск Gap Fill"
        verbose_name_plural = "Пропуски Gap Fill"
        ordering = ["order"]


class SentenceBuilderItem(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="sentence_builder_items",
        verbose_name="Упражнение",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    def __str__(self):
        return f"Sentence Builder #{self.pk}"

    class Meta:
        verbose_name = "Элемент Sentence Builder"
        verbose_name_plural = "Элементы Sentence Builder"
        ordering = ["order"]


class SentenceBuilderToken(models.Model):
    item = models.ForeignKey(
        SentenceBuilderItem,
        on_delete=models.CASCADE,
        related_name="tokens",
        verbose_name="Элемент",
    )
    text = models.CharField(
        max_length=200,
        verbose_name="Текст токена",
    )
    correct_position = models.PositiveIntegerField(
        verbose_name="Правильная позиция",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Токен Sentence Builder"
        verbose_name_plural = "Токены Sentence Builder"
        ordering = ["order"]


class ExerciseResult(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name="Ученик",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name="Упражнение",
    )
    score = models.FloatField(
        default=0.0,
        verbose_name="Баллы",
    )
    max_score = models.FloatField(
        default=0.0,
        verbose_name="Максимальный балл",
    )
    percentage = models.FloatField(
        default=0.0,
        verbose_name="Процент",
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Детали результата",
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Завершено",
    )

    def __str__(self):
        return (
            f"{self.student} - {self.exercise.title} "
            f"({self.score}/{self.max_score})"
        )

    class Meta:
        verbose_name = "Результат упражнения"
        verbose_name_plural = "Результаты упражнений"
        ordering = ["-completed_at"]


class StudentTopicProgress(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="topic_progress",
        verbose_name="Ученик",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="student_progress",
        verbose_name="Тема",
    )
    exercises_completed = models.IntegerField(
        default=0,
        verbose_name="Выполнено упражнений",
    )
    last_practiced = models.DateTimeField(
        auto_now=True,
        verbose_name="Последняя практика",
    )
    mastery_level = models.FloatField(
        default=0.0,
        verbose_name="Уровень освоения (0-1)",
    )

    def __str__(self):
        return f"{self.student} - {self.topic.name}"

    class Meta:
        verbose_name = "Прогресс по теме"
        verbose_name_plural = "Прогресс по темам"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "topic"],
                name="unique_student_topic_progress",
            ),
        ]


class TeacherRecommendation(models.Model):
    PRIORITY_CHOICES = [
        ("high", "Высокий"),
        ("normal", "Обычный"),
        ("low", "Низкий"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="teacher_recommendations",
        verbose_name="Ученик",
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок",
    )
    message = models.TextField(
        verbose_name="Текст рекомендации",
    )
    reason = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Причина рекомендации",
        help_text="Необязательное объяснение, почему назначена рекомендация.",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_recommendations",
        verbose_name="Тема",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_recommendations",
        verbose_name="Упражнение",
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="normal",
        verbose_name="Приоритет",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_teacher_recommendations",
        verbose_name="Создал",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создана",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлена",
    )

    def __str__(self):
        return f"{self.title} — {self.student}"

    class Meta:
        verbose_name = "Рекомендация учителя"
        verbose_name_plural = "Рекомендации учителя"
        ordering = ["-created_at"]
