from django.db import transaction
from rest_framework import serializers

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
)


# ============================================================
# Topic
# ============================================================

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = [
            "id",
            "name",
            "description",
        ]


# ============================================================
# Student
# ============================================================

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "level",
            "created_at",
        ]


# ============================================================
# Vocabulary Drill
# ============================================================

class VocabularyOptionSerializer(serializers.Serializer):
    """
    Безопасный вариант ответа.

    correct_answer сюда никогда не попадает.
    """

    id = serializers.CharField()
    text = serializers.CharField()


class VocabularyItemSerializer(serializers.ModelSerializer):
    """
    GET:

    {
        "id": 1,
        "prompt": "sich ausruhen",
        "options": [...]
    }
    """

    options = serializers.SerializerMethodField()

    class Meta:
        model = VocabularyItem
        fields = [
            "id",
            "prompt",
            "options",
        ]

    def get_options(self, obj):
        options = [
            {
                "id": "a",
                "text": obj.correct_answer,
            },
            {
                "id": "b",
                "text": obj.distractor_1,
            },
            {
                "id": "c",
                "text": obj.distractor_2,
            },
            {
                "id": "d",
                "text": obj.distractor_3,
            },
        ]

        # Перемешивание выполняется на backend.
        # Правильный ответ при этом не помечается.
        import random

        random.shuffle(options)

        return [
            {
                "id": chr(ord("a") + index),
                "text": option["text"],
            }
            for index, option in enumerate(options)
        ]


# ============================================================
# Multiple Choice
# ============================================================

class MultipleChoiceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleChoiceOption
        fields = [
            "id",
            "text",
        ]


class MultipleChoiceItemSerializer(serializers.ModelSerializer):
    options = MultipleChoiceOptionSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = MultipleChoiceItem
        fields = [
            "id",
            "question",
            "options",
            "selection_mode",
        ]


# ============================================================
# Dropdown
# ============================================================

class DropdownOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DropdownOption
        fields = [
            "id",
            "text",
        ]


class DropdownPartSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = DropdownPart
        fields = [
            "id",
            "part_type",
            "text",
            "options",
        ]

    def get_options(self, obj):
        if obj.part_type != "select":
            return []

        return DropdownOptionSerializer(
            obj.options.all(),
            many=True,
        ).data


class DropdownItemSerializer(serializers.ModelSerializer):
    parts = DropdownPartSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = DropdownItem
        fields = [
            "id",
            "parts",
        ]


# ============================================================
# Gap Fill
# ============================================================

class GapFillGapSerializer(serializers.ModelSerializer):
    """
    ВАЖНО:
    correct_answer намеренно НЕ возвращается frontend.
    """

    class Meta:
        model = GapFillGap
        fields = [
            "id",
            "placeholder",
        ]


class GapFillItemSerializer(serializers.ModelSerializer):
    gaps = GapFillGapSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = GapFillItem
        fields = [
            "id",
            "text",
            "gaps",
        ]


# ============================================================
# Sentence Builder
# ============================================================

class SentenceBuilderTokenSerializer(serializers.ModelSerializer):
    """
    correct_position намеренно НЕ возвращается frontend.
    """

    id = serializers.SerializerMethodField()

    class Meta:
        model = SentenceBuilderToken
        fields = [
            "id",
            "text",
        ]

    def get_id(self, obj):
        return f"t{obj.id}"


class SentenceBuilderItemSerializer(serializers.ModelSerializer):
    tokens = SentenceBuilderTokenSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = SentenceBuilderItem
        fields = [
            "id",
            "tokens",
        ]


# ============================================================
# Exercise progress helpers
# ============================================================

class ExerciseProgressMixin:
    """
    Общая логика определения последнего результата студента.
    """

    def _get_student(self):
        request = self.context.get("request")

        if (
            request
            and hasattr(request, "user")
            and request.user.is_authenticated
        ):
            try:
                return Student.objects.get(user=request.user)
            except Student.DoesNotExist:
                return None

        return None

    def _get_last_result(self, exercise, student):
        if not student:
            return None

        return (
            ExerciseResult.objects
            .filter(
                student=student,
                exercise=exercise,
            )
            .order_by("-completed_at")
            .first()
        )

    def _calculate_status(self, percentage):
        if percentage is None:
            return "not_started"

        if percentage >= 100:
            return "mastered"

        if percentage >= 80:
            return "completed"

        if percentage >= 50:
            return "review_recommended"

        return "needs_review"

    def _get_score(self, exercise):
        student = self._get_student()

        if not student:
            return None

        result = self._get_last_result(
            exercise,
            student,
        )

        if not result:
            return None

        return int(round(result.percentage))

    def _get_status(self, exercise):
        student = self._get_student()

        if not student:
            return "not_started"

        result = self._get_last_result(
            exercise,
            student,
        )

        if not result:
            return "not_started"

        return self._calculate_status(
            result.percentage
        )

    def _get_is_locked(self, exercise):
        student = self._get_student()

        if not student:
            return False

        previous_exercise = (
            Exercise.objects
            .filter(
                order__lt=exercise.order,
                is_active=True,
            )
            .order_by("-order")
            .first()
        )

        if not previous_exercise:
            return False

        previous_result = self._get_last_result(
            previous_exercise,
            student,
        )

        if not previous_result:
            return False

        return previous_result.percentage < 50


# ============================================================
# Exercise List
# ============================================================

class ExerciseListSerializer(
    ExerciseProgressMixin,
    serializers.ModelSerializer,
):
    topics = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            "id",
            "title",
            "exercise_type",
            "topics",
            "language",
            "level",
            "is_active",
            "created_at",
            "updated_at",
            "order",
            "score",
            "status",
            "is_locked",
        ]

    def get_topics(self, obj):
        return [
            topic.name
            for topic in obj.topics.all()
        ]

    def get_score(self, obj):
        return self._get_score(obj)

    def get_status(self, obj):
        return self._get_status(obj)

    def get_is_locked(self, obj):
        return self._get_is_locked(obj)


# ============================================================
# Full Exercise
# ============================================================

class ExerciseSerializer(
    ExerciseProgressMixin,
    serializers.ModelSerializer,
):
    """
    Основной GET-сериализатор упражнения.

    В зависимости от exercise_type возвращается только
    соответствующая структура.

    Правильные ответы frontend НЕ получает.
    """

    topics = serializers.SerializerMethodField()

    vocabulary_items = VocabularyItemSerializer(
        many=True,
        read_only=True,
    )

    multiple_choice_items = MultipleChoiceItemSerializer(
        many=True,
        read_only=True,
    )

    dropdown_items = DropdownItemSerializer(
        many=True,
        read_only=True,
    )

    gap_fill_items = GapFillItemSerializer(
        many=True,
        read_only=True,
    )

    sentence_builder_items = SentenceBuilderItemSerializer(
        many=True,
        read_only=True,
    )

    score = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            "id",
            "title",
            "exercise_type",
            "topics",
            "language",
            "level",
            "is_active",
            "created_at",
            "updated_at",
            "order",

            "vocabulary_items",
            "multiple_choice_items",
            "dropdown_items",
            "gap_fill_items",
            "sentence_builder_items",

            "score",
            "status",
            "is_locked",
        ]

    def get_topics(self, obj):
        return [
            topic.name
            for topic in obj.topics.all()
        ]

    def get_score(self, obj):
        return self._get_score(obj)

    def get_status(self, obj):
        return self._get_status(obj)

    def get_is_locked(self, obj):
        return self._get_is_locked(obj)


# ============================================================
# Exercise Result
# ============================================================

class ExerciseResultSerializer(serializers.ModelSerializer):
    """
    Сериализатор сохранённого результата.

    ВАЖНО:
    score / max_score / percentage / details создаются backend.

    Frontend не должен иметь возможность подменить результат.
    """

    student = StudentSerializer(
        read_only=True,
    )

    exercise_title = serializers.CharField(
        source="exercise.title",
        read_only=True,
    )

    class Meta:
        model = ExerciseResult
        fields = [
            "id",
            "student",
            "exercise",
            "exercise_title",
            "score",
            "max_score",
            "percentage",
            "details",
            "completed_at",
        ]

        read_only_fields = [
            "id",
            "student",
            "score",
            "max_score",
            "percentage",
            "details",
            "completed_at",
        ]


# ============================================================
# Student Topic Progress
# ============================================================

class StudentTopicProgressSerializer(
    serializers.ModelSerializer,
):
    topic = TopicSerializer(
        read_only=True,
    )

    student = StudentSerializer(
        read_only=True,
    )

    class Meta:
        model = StudentTopicProgress
        fields = [
            "id",
            "student",
            "topic",
            "exercises_completed",
            "last_practiced",
            "mastery_level",
        ]


# ============================================================
# INPUT SERIALIZERS
# ============================================================

class VocabularyItemInputSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = VocabularyItem
        fields = [
            "prompt",
            "correct_answer",
            "distractor_1",
            "distractor_2",
            "distractor_3",
            "order",
        ]


class MultipleChoiceOptionInputSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = MultipleChoiceOption
        fields = [
            "text",
            "is_correct",
            "order",
        ]


class MultipleChoiceItemInputSerializer(
    serializers.ModelSerializer
):
    options = MultipleChoiceOptionInputSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = MultipleChoiceItem
        fields = [
            "question",
            "selection_mode",
            "order",
            "options",
        ]

    def create(self, validated_data):
        options_data = validated_data.pop(
            "options",
            [],
        )

        item = MultipleChoiceItem.objects.create(
            **validated_data
        )

        for option_data in options_data:
            MultipleChoiceOption.objects.create(
                item=item,
                **option_data,
            )

        return item


class DropdownOptionInputSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = DropdownOption
        fields = [
            "text",
            "is_correct",
            "order",
        ]


class DropdownPartInputSerializer(
    serializers.ModelSerializer
):
    options = DropdownOptionInputSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = DropdownPart
        fields = [
            "part_type",
            "text",
            "order",
            "options",
        ]

    def create(self, validated_data):
        options_data = validated_data.pop(
            "options",
            [],
        )

        part = DropdownPart.objects.create(
            **validated_data
        )

        for option_data in options_data:
            DropdownOption.objects.create(
                part=part,
                **option_data,
            )

        return part


class DropdownItemInputSerializer(
    serializers.ModelSerializer
):
    parts = DropdownPartInputSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = DropdownItem
        fields = [
            "order",
            "parts",
        ]

    def create(self, validated_data):
        parts_data = validated_data.pop(
            "parts",
            [],
        )

        item = DropdownItem.objects.create(
            **validated_data
        )

        for part_data in parts_data:
            options_data = part_data.pop(
                "options",
                [],
            )

            part = DropdownPart.objects.create(
                item=item,
                **part_data,
            )

            for option_data in options_data:
                DropdownOption.objects.create(
                    part=part,
                    **option_data,
                )

        return item


class GapFillGapInputSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = GapFillGap
        fields = [
            "placeholder",
            "correct_answer",
            "order",
        ]


class GapFillItemInputSerializer(
    serializers.ModelSerializer
):
    gaps = GapFillGapInputSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = GapFillItem
        fields = [
            "text",
            "order",
            "gaps",
        ]

    def create(self, validated_data):
        gaps_data = validated_data.pop(
            "gaps",
            [],
        )

        item = GapFillItem.objects.create(
            **validated_data
        )

        for gap_data in gaps_data:
            GapFillGap.objects.create(
                item=item,
                **gap_data,
            )

        return item


class SentenceBuilderTokenInputSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = SentenceBuilderToken
        fields = [
            "text",
            "correct_position",
            "order",
        ]


class SentenceBuilderItemInputSerializer(
    serializers.ModelSerializer
):
    tokens = SentenceBuilderTokenInputSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = SentenceBuilderItem
        fields = [
            "order",
            "tokens",
        ]

    def create(self, validated_data):
        tokens_data = validated_data.pop(
            "tokens",
            [],
        )

        item = SentenceBuilderItem.objects.create(
            **validated_data
        )

        for token_data in tokens_data:
            SentenceBuilderToken.objects.create(
                item=item,
                **token_data,
            )

        return item


# ============================================================
# Exercise Create / Import
# ============================================================

class ExerciseCreateSerializer(
    serializers.ModelSerializer
):
    """
    Создание полного упражнения через API.

    В зависимости от exercise_type используется
    соответствующий набор вложенных данных.
    """

    topics = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
    )

    vocabulary_items = VocabularyItemInputSerializer(
        many=True,
        required=False,
        write_only=True,
    )

    multiple_choice_items = MultipleChoiceItemInputSerializer(
        many=True,
        required=False,
        write_only=True,
    )

    dropdown_items = DropdownItemInputSerializer(
        many=True,
        required=False,
        write_only=True,
    )

    gap_fill_items = GapFillItemInputSerializer(
        many=True,
        required=False,
        write_only=True,
    )

    sentence_builder_items = SentenceBuilderItemInputSerializer(
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Exercise
        fields = [
            "title",
            "exercise_type",
            "topics",
            "language",
            "level",
            "is_active",
            "order",

            "vocabulary_items",
            "multiple_choice_items",
            "dropdown_items",
            "gap_fill_items",
            "sentence_builder_items",
        ]

    @transaction.atomic
    def create(self, validated_data):
        topics_names = validated_data.pop(
            "topics",
            [],
        )

        vocabulary_items = validated_data.pop(
            "vocabulary_items",
            [],
        )

        multiple_choice_items = validated_data.pop(
            "multiple_choice_items",
            [],
        )

        dropdown_items = validated_data.pop(
            "dropdown_items",
            [],
        )

        gap_fill_items = validated_data.pop(
            "gap_fill_items",
            [],
        )

        sentence_builder_items = validated_data.pop(
            "sentence_builder_items",
            [],
        )

        exercise = Exercise.objects.create(
            **validated_data
        )

        # ----------------------------------------------------
        # Topics
        # ----------------------------------------------------

        topics = []

        for name in topics_names:
            topic, _ = Topic.objects.get_or_create(
                name=name
            )
            topics.append(topic)

        exercise.topics.set(topics)

        # ----------------------------------------------------
        # Vocabulary Drill
        # ----------------------------------------------------

        for item_data in vocabulary_items:
            VocabularyItem.objects.create(
                exercise=exercise,
                **item_data,
            )

        # ----------------------------------------------------
        # Multiple Choice
        # ----------------------------------------------------

        for item_data in multiple_choice_items:
            options_data = item_data.pop(
                "options",
                [],
            )

            item = MultipleChoiceItem.objects.create(
                exercise=exercise,
                **item_data,
            )

            for option_data in options_data:
                MultipleChoiceOption.objects.create(
                    item=item,
                    **option_data,
                )

        # ----------------------------------------------------
        # Dropdown
        # ----------------------------------------------------

        for item_data in dropdown_items:
            parts_data = item_data.pop(
                "parts",
                [],
            )

            item = DropdownItem.objects.create(
                exercise=exercise,
                **item_data,
            )

            for part_data in parts_data:
                options_data = part_data.pop(
                    "options",
                    [],
                )

                part = DropdownPart.objects.create(
                    item=item,
                    **part_data,
                )

                for option_data in options_data:
                    DropdownOption.objects.create(
                        part=part,
                        **option_data,
                    )

        # ----------------------------------------------------
        # Gap Fill
        # ----------------------------------------------------

        for item_data in gap_fill_items:
            gaps_data = item_data.pop(
                "gaps",
                [],
            )

            item = GapFillItem.objects.create(
                exercise=exercise,
                **item_data,
            )

            for gap_data in gaps_data:
                GapFillGap.objects.create(
                    item=item,
                    **gap_data,
                )

        # ----------------------------------------------------
        # Sentence Builder
        # ----------------------------------------------------

        for item_data in sentence_builder_items:
            tokens_data = item_data.pop(
                "tokens",
                [],
            )

            item = SentenceBuilderItem.objects.create(
                exercise=exercise,
                **item_data,
            )

            for token_data in tokens_data:
                SentenceBuilderToken.objects.create(
                    item=item,
                    **token_data,
                )

        return exercise
