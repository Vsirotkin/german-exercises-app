from django.contrib import admin
from .models import (
    Topic,
    Student,
    Exercise,
    VocabularyCard,
    Sentence,
    GapOption,
    ExerciseResult,
    StudentTopicProgress,
)

# --- Inline редакторы (для вложенного редактирования) ---


class VocabularyCardInline(admin.TabularInline):
    """Позволяет редактировать карточки слов прямо внутри Упражнения"""

    model = VocabularyCard
    extra = 1  # Сколько пустых полей показывать для добавления новых
    fields = [
        "word",
        "correct_translation",
        "distractor_1",
        "distractor_2",
        "distractor_3",
        "order",
    ]
    ordering = ["order"]


class GapOptionInline(admin.TabularInline):
    """Редактирование вариантов ответов для пропусков"""

    model = GapOption
    extra = 1
    fields = ["placeholder_index", "options", "correct_answer"]


class SentenceInline(admin.StackedInline):
    """Редактирование предложений внутри Упражнения (с вложенными опциями)"""

    model = Sentence
    extra = 1
    fields = ["text", "order"]
    ordering = ["order"]

    # Включаем редактирование опций прямо внутри предложения
    inlines = [GapOptionInline]


# --- Основные регистраторы ---


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("title", "exercise_type", "order", "is_active", "created_at")
    list_filter = ("exercise_type", "is_active", "topics")
    search_fields = ("title",)

    # Подключаем инлайны в зависимости от типа упражнения можно было бы сделать хитрее,
    # но пока подключим оба. Django сам скроет лишнее, если связей нет.
    inlines = [VocabularyCardInline, SentenceInline]

    fieldsets = (
        (
            "Основная информация",
            {"fields": ("title", "exercise_type", "topics", "language", "is_active")},
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),  # Сворачиваемый блок
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "level")
    list_filter = ("level",)
    search_fields = ("first_name", "last_name", "email")


@admin.register(ExerciseResult)
class ExerciseResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "get_exercise_title",
        "score",
        "total_questions",
        "completed_at",
    )
    list_filter = ("completed_at",)
    readonly_fields = ("id", "completed_at")

    # Создаем метод, который возвращает название упражнения
    def get_exercise_title(self, obj):
        return obj.exercise.title if obj.exercise else "-"

    # Указываем заголовок колонки и возможность сортировки
    get_exercise_title.short_description = "Упражнение"
    get_exercise_title.admin_order_field = "exercise__title"


@admin.register(StudentTopicProgress)
class StudentTopicProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "topic", "mastery_level", "exercises_completed")
    list_filter = ("topic",)
