from django.contrib import admin

from .models import (
    Topic,
    Student,
    Exercise,
    VocabularyItem,
    MultipleChoiceItem,
    MultipleChoiceOption,
    DropdownItem,
    DropdownPart,
    DropdownOption,
    GapFillItem,
    GapFillGap,
    SentenceBuilderItem,
    SentenceBuilderToken,
    ExerciseResult,
    StudentTopicProgress,
    TeacherRecommendation,
)

# ============================================================
# Topic
# ============================================================


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at",)


# ============================================================
# Student
# ============================================================


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "level",
        "created_at",
    )
    list_filter = ("level",)
    search_fields = (
        "first_name",
        "last_name",
        "email",
    )
    readonly_fields = ("created_at",)


# ============================================================
# Vocabulary Drill
# ============================================================


@admin.register(VocabularyItem)
class VocabularyItemAdmin(admin.ModelAdmin):
    list_display = (
        "prompt",
        "correct_answer",
        "exercise",
        "order",
    )
    list_filter = ("exercise",)
    search_fields = (
        "prompt",
        "correct_answer",
    )
    ordering = ("exercise", "order")


# ============================================================
# Multiple Choice
# ============================================================


class MultipleChoiceOptionInline(admin.TabularInline):
    model = MultipleChoiceOption
    extra = 1
    fields = (
        "text",
        "is_correct",
        "order",
    )
    ordering = ("order",)


@admin.register(MultipleChoiceItem)
class MultipleChoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "exercise",
        "selection_mode",
        "order",
    )
    list_filter = (
        "selection_mode",
        "exercise",
    )
    search_fields = ("question",)
    ordering = ("exercise", "order")
    inlines = [MultipleChoiceOptionInline]


@admin.register(MultipleChoiceOption)
class MultipleChoiceOptionAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "item",
        "is_correct",
        "order",
    )
    list_filter = ("is_correct",)
    search_fields = ("text",)
    ordering = ("item", "order")


# ============================================================
# Dropdown
# ============================================================


@admin.register(DropdownItem)
class DropdownItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "exercise",
        "order",
    )
    list_filter = ("exercise",)
    ordering = ("exercise", "order")


class DropdownOptionInline(admin.TabularInline):
    model = DropdownOption
    extra = 1
    fields = (
        "text",
        "is_correct",
        "order",
    )
    ordering = ("order",)


@admin.register(DropdownPart)
class DropdownPartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "item",
        "part_type",
        "text",
        "order",
    )
    list_filter = (
        "part_type",
        "item__exercise",
    )
    search_fields = ("text",)
    ordering = ("item", "order")
    inlines = [DropdownOptionInline]


@admin.register(DropdownOption)
class DropdownOptionAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "part",
        "is_correct",
        "order",
    )
    list_filter = ("is_correct",)
    search_fields = ("text",)
    ordering = ("part", "order")


# ============================================================
# Gap Fill
# ============================================================


class GapFillGapInline(admin.TabularInline):
    model = GapFillGap
    extra = 1
    fields = (
        "placeholder",
        "correct_answer",
        "order",
    )
    ordering = ("order",)


@admin.register(GapFillItem)
class GapFillItemAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "exercise",
        "order",
    )
    list_filter = ("exercise",)
    search_fields = ("text",)
    ordering = ("exercise", "order")
    inlines = [GapFillGapInline]


@admin.register(GapFillGap)
class GapFillGapAdmin(admin.ModelAdmin):
    list_display = (
        "placeholder",
        "correct_answer",
        "item",
        "order",
    )
    search_fields = (
        "placeholder",
        "correct_answer",
    )
    ordering = ("item", "order")


# ============================================================
# Sentence Builder
# ============================================================


class SentenceBuilderTokenInline(admin.TabularInline):
    model = SentenceBuilderToken
    extra = 1
    fields = (
        "text",
        "correct_position",
        "order",
    )
    ordering = ("order",)


@admin.register(SentenceBuilderItem)
class SentenceBuilderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "exercise",
        "order",
    )
    list_filter = ("exercise",)
    ordering = ("exercise", "order")
    inlines = [SentenceBuilderTokenInline]


@admin.register(SentenceBuilderToken)
class SentenceBuilderTokenAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "item",
        "correct_position",
        "order",
    )
    search_fields = ("text",)
    ordering = ("item", "correct_position")


# ============================================================
# Exercise
# ============================================================


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "exercise_type",
        "level",
        "language",
        "order",
        "is_active",
        "created_at",
    )
    list_filter = (
        "exercise_type",
        "level",
        "language",
        "is_active",
        "topics",
    )
    search_fields = ("title",)
    filter_horizontal = ("topics",)
    ordering = ("order",)

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "title",
                    "exercise_type",
                    "topics",
                    "language",
                    "level",
                    "is_active",
                    "order",
                )
            },
        ),
        (
            "Даты",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# ============================================================
# Exercise Result
# ============================================================


@admin.register(ExerciseResult)
class ExerciseResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "exercise",
        "score",
        "max_score",
        "percentage",
        "completed_at",
    )
    list_filter = (
        "exercise",
        "completed_at",
    )
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__email",
        "exercise__title",
    )
    readonly_fields = (
        "id",
        "completed_at",
    )


# ============================================================
# Student Topic Progress
# ============================================================


@admin.register(StudentTopicProgress)
class StudentTopicProgressAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "topic",
        "exercises_completed",
        "mastery_level",
        "last_practiced",
    )
    list_filter = ("topic",)
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__email",
        "topic__name",
    )
    readonly_fields = ("last_practiced",)


# ============================================================
# Teacher Recommendation
# ============================================================


@admin.register(TeacherRecommendation)
class TeacherRecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "title",
        "priority",
        "is_active",
        "topic",
        "exercise",
        "created_by",
        "created_at",
    )
    list_filter = (
        "is_active",
        "priority",
        "topic",
        "exercise",
    )
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__email",
        "title",
        "message",
        "reason",
        "topic__name",
        "exercise__title",
        "created_by__username",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = (
        "student",
        "topic",
        "exercise",
        "created_by",
    )
    readonly_fields = (
        "created_by",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Рекомендация",
            {
                "fields": (
                    "student",
                    "title",
                    "message",
                    "reason",
                )
            },
        ),
        (
            "Связанные материалы",
            {
                "fields": (
                    "topic",
                    "exercise",
                )
            },
        ),
        (
            "Настройки",
            {
                "fields": (
                    "priority",
                    "is_active",
                )
            },
        ),
        (
            "Служебная информация",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
