import json
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from django.db import transaction
from jsonschema import Draft202012Validator

from exercises.models import (
    DropdownItem,
    DropdownOption,
    DropdownPart,
    Exercise,
    GapFillGap,
    GapFillItem,
    MultipleChoiceItem,
    MultipleChoiceOption,
    SentenceBuilderItem,
    SentenceBuilderToken,
    Topic,
    VocabularyItem,
)


class ExerciseImportValidationError(Exception):
    """
    Ошибка валидации импортируемого файла.

    errors содержит список словарей вида:
    {
        "path": "exercises[0].data.items[0]",
        "message": "..."
    }
    """

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors

        message = "\n".join(f"{error['path']}: {error['message']}" for error in errors)

        super().__init__(message)


class ExerciseImportService:
    """
    Сервис импорта упражнений из JSON.

    Ответственность сервиса:
    1. Загрузить JSON.
    2. Проверить JSON Schema.
    3. Проверить бизнес-правила.
    4. Предоставить preview без записи в БД.
    5. Выполнить атомарный импорт в БД.
    """

    SCHEMA_PATH = (
        Path(__file__).resolve().parent.parent
        / "schemas"
        / "exercise_import.schema.json"
    )

    SUPPORTED_EXERCISE_TYPES = {
        "vocabulary_drill",
        "multiple_choice",
        "dropdown",
        "gap_fill",
        "sentence_builder",
    }

    def __init__(self) -> None:
        self.schema = self._load_schema()
        self.validator = Draft202012Validator(self.schema)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_json(
        self,
        source: str | Path | TextIO | BinaryIO,
    ) -> dict[str, Any]:
        """
        Загружает JSON из:
        - пути к файлу;
        - строкового JSON;
        - текстового/binary file-like объекта.

        Возвращает Python dict.
        """

        try:
            if isinstance(source, Path):
                with source.open("r", encoding="utf-8") as file:
                    return json.load(file)

            if isinstance(source, str):
                source_path = Path(source)

                if source_path.exists() and source_path.is_file():
                    with source_path.open("r", encoding="utf-8") as file:
                        return json.load(file)

                return json.loads(source)

            return json.load(source)

        except json.JSONDecodeError as exc:
            raise ExerciseImportValidationError(
                [
                    {
                        "path": "file",
                        "message": (
                            f"Некорректный JSON: {exc.msg} "
                            f"(строка {exc.lineno}, колонка {exc.colno})"
                        ),
                    }
                ]
            ) from exc

        except (OSError, TypeError, ValueError) as exc:
            raise ExerciseImportValidationError(
                [
                    {
                        "path": "file",
                        "message": f"Не удалось прочитать JSON: {exc}",
                    }
                ]
            ) from exc

    def validate_schema(self, data: Any) -> list[dict[str, str]]:
        """
        Проверяет JSON по JSON Schema.

        Возвращает список ошибок.
        """

        errors = []

        for error in sorted(
            self.validator.iter_errors(data),
            key=lambda item: list(item.absolute_path),
        ):
            path = self._format_json_path(error.absolute_path)

            errors.append(
                {
                    "path": path,
                    "message": error.message,
                }
            )

        return errors

    def validate_business_rules(
        self,
        data: dict[str, Any],
    ) -> list[dict[str, str]]:
        """
        Проверяет правила, которые невозможно или нежелательно
        выражать только средствами JSON Schema.
        """

        errors: list[dict[str, str]] = []

        exercises = data.get("exercises", [])

        if not isinstance(exercises, list):
            return errors

        for exercise_index, exercise_data in enumerate(exercises):
            exercise_path = f"exercises[{exercise_index}]"

            if not isinstance(exercise_data, dict):
                continue

            exercise_type = exercise_data.get("type")

            if exercise_type not in self.SUPPORTED_EXERCISE_TYPES:
                continue

            topics = exercise_data.get("topics", [])

            errors.extend(
                self._validate_topics(
                    topics,
                    exercise_path,
                )
            )

            if exercise_type == "vocabulary_drill":
                errors.extend(
                    self._validate_vocabulary(
                        exercise_data,
                        exercise_path,
                    )
                )

            elif exercise_type == "multiple_choice":
                errors.extend(
                    self._validate_multiple_choice(
                        exercise_data,
                        exercise_path,
                    )
                )

            elif exercise_type == "dropdown":
                errors.extend(
                    self._validate_dropdown(
                        exercise_data,
                        exercise_path,
                    )
                )

            elif exercise_type == "gap_fill":
                errors.extend(
                    self._validate_gap_fill(
                        exercise_data,
                        exercise_path,
                    )
                )

            elif exercise_type == "sentence_builder":
                errors.extend(
                    self._validate_sentence_builder(
                        exercise_data,
                        exercise_path,
                    )
                )

        errors.extend(self._validate_duplicate_exercises(exercises))

        return errors

    def validate(self, data: Any) -> list[dict[str, str]]:
        """
        Выполняет полную валидацию:
        1. JSON Schema.
        2. Business rules.

        Важно:
        бизнес-валидация выполняется только если структура
        уже соответствует Schema.
        """

        schema_errors = self.validate_schema(data)

        if schema_errors:
            return schema_errors

        return self.validate_business_rules(data)

    def preview(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Формирует preview импорта без записи в БД.

        Возвращает:
        {
            "valid": bool,
            "errors": [...],
            "summary": {...}
        }
        """

        errors = self.validate(data)

        if errors:
            return {
                "valid": False,
                "errors": errors,
                "summary": {
                    "exercise_count": 0,
                    "by_type": {},
                    "topics": [],
                },
            }

        exercises = data["exercises"]

        by_type: dict[str, int] = {}

        for exercise in exercises:
            exercise_type = exercise["type"]
            by_type[exercise_type] = by_type.get(exercise_type, 0) + 1

        topics = sorted(
            {topic for exercise in exercises for topic in exercise["topics"]}
        )

        return {
            "valid": True,
            "errors": [],
            "summary": {
                "exercise_count": len(exercises),
                "by_type": by_type,
                "topics": topics,
                "language": data["language"],
                "version": data["version"],
            },
        }

    def import_exercises(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Полностью импортирует упражнения в БД.

        Импорт выполняется атомарно:
        если создание любого объекта завершится ошибкой,
        вся транзакция откатывается.
        """

        errors = self.validate(data)

        if errors:
            raise ExerciseImportValidationError(errors)

        created_exercises: list[Exercise] = []

        with transaction.atomic():
            for index, exercise_data in enumerate(data["exercises"]):
                exercise = self._create_exercise(
                    exercise_data=exercise_data,
                    language=data["language"],
                    fallback_order=index,
                )

                created_exercises.append(exercise)

        return {
            "created_count": len(created_exercises),
            "exercise_ids": [exercise.id for exercise in created_exercises],
        }

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _load_schema(self) -> dict[str, Any]:
        if not self.SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Schema file not found: {self.SCHEMA_PATH}")

        with self.SCHEMA_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)

    # ------------------------------------------------------------------
    # Business validation
    # ------------------------------------------------------------------

    def _validate_topics(
        self,
        topics: Any,
        exercise_path: str,
    ) -> list[dict[str, str]]:
        errors = []

        if not isinstance(topics, list):
            return errors

        normalized_topics = [
            topic.strip() for topic in topics if isinstance(topic, str)
        ]

        for index, topic in enumerate(topics):
            if not isinstance(topic, str):
                continue

            if not topic.strip():
                errors.append(
                    {
                        "path": f"{exercise_path}.topics[{index}]",
                        "message": "Название темы не может быть пустым.",
                    }
                )

        if len(normalized_topics) != len(set(normalized_topics)):
            errors.append(
                {
                    "path": f"{exercise_path}.topics",
                    "message": "Темы не должны повторяться.",
                }
            )

        return errors

    def _validate_vocabulary(
        self,
        exercise_data: dict[str, Any],
        exercise_path: str,
    ) -> list[dict[str, str]]:
        errors = []

        items = exercise_data["data"]["items"]

        words_seen: set[str] = set()

        for index, item in enumerate(items):
            path = f"{exercise_path}.data.items[{index}]"

            word = item["word"].strip()
            correct = item["correct"].strip()

            if word in words_seen:
                errors.append(
                    {
                        "path": f"{path}.word",
                        "message": (
                            "Слово word уже используется " "в этом упражнении."
                        ),
                    }
                )

            words_seen.add(word)

            distractors = [distractor.strip() for distractor in item["distractors"]]

            answers = [correct, *distractors]

            if len(set(answers)) != len(answers):
                errors.append(
                    {
                        "path": f"{path}.distractors",
                        "message": (
                            "Правильный ответ и distractors " "должны быть уникальными."
                        ),
                    }
                )

        return errors

    def _validate_multiple_choice(
        self,
        exercise_data: dict[str, Any],
        exercise_path: str,
    ) -> list[dict[str, str]]:
        errors = []

        items = exercise_data["data"]["items"]

        for index, item in enumerate(items):
            path = f"{exercise_path}.data.items[{index}]"

            options = item["options"]
            selection_mode = item["selection_mode"]

            correct_count = sum(1 for option in options if option["correct"])

            if selection_mode == "single" and correct_count != 1:
                errors.append(
                    {
                        "path": f"{path}.options",
                        "message": (
                            "Для selection_mode='single' "
                            "должен быть ровно один правильный вариант."
                        ),
                    }
                )

            elif selection_mode == "multiple" and correct_count < 1:
                errors.append(
                    {
                        "path": f"{path}.options",
                        "message": (
                            "Для selection_mode='multiple' "
                            "должен быть хотя бы один правильный вариант."
                        ),
                    }
                )

            option_texts = [option["text"].strip() for option in options]

            if len(set(option_texts)) != len(option_texts):
                errors.append(
                    {
                        "path": f"{path}.options",
                        "message": "Варианты ответа не должны повторяться.",
                    }
                )

        return errors

    def _validate_dropdown(
        self,
        exercise_data: dict[str, Any],
        exercise_path: str,
    ) -> list[dict[str, str]]:
        errors = []

        items = exercise_data["data"]["items"]

        for item_index, item in enumerate(items):
            parts = item["parts"]

            for part_index, part in enumerate(parts):
                if part["type"] != "select":
                    continue

                path = (
                    f"{exercise_path}.data.items[{item_index}]" f".parts[{part_index}]"
                )

                options = part["options"]

                correct_count = sum(1 for option in options if option["correct"])

                if correct_count != 1:
                    errors.append(
                        {
                            "path": f"{path}.options",
                            "message": (
                                "Для select-part должен быть "
                                "ровно один правильный вариант."
                            ),
                        }
                    )

                option_texts = [option["text"].strip() for option in options]

                if len(set(option_texts)) != len(option_texts):
                    errors.append(
                        {
                            "path": f"{path}.options",
                            "message": ("Варианты dropdown не должны повторяться."),
                        }
                    )

        return errors

    def _validate_gap_fill(
        self,
        exercise_data: dict[str, Any],
        exercise_path: str,
    ) -> list[dict[str, str]]:
        errors = []

        items = exercise_data["data"]["items"]

        for item_index, item in enumerate(items):
            path = f"{exercise_path}.data.items[{item_index}]"

            text = item["text"]
            gaps = item["gaps"]

            placeholders = [gap["placeholder"] for gap in gaps]

            if len(set(placeholders)) != len(placeholders):
                errors.append(
                    {
                        "path": f"{path}.gaps",
                        "message": (
                            "Placeholder каждого gap должен быть "
                            "уникальным внутри задания."
                        ),
                    }
                )

            for gap_index, gap in enumerate(gaps):
                placeholder = gap["placeholder"]

                if placeholder not in text:
                    errors.append(
                        {
                            "path": (f"{path}.gaps[{gap_index}].placeholder"),
                            "message": (
                                f"Placeholder '{placeholder}' "
                                "не найден в тексте задания."
                            ),
                        }
                    )

        return errors

    def _validate_sentence_builder(
        self,
        exercise_data: dict[str, Any],
        exercise_path: str,
    ) -> list[dict[str, str]]:
        errors = []

        items = exercise_data["data"]["items"]

        for item_index, item in enumerate(items):
            path = f"{exercise_path}.data.items[{item_index}]"

            tokens = item["tokens"]

            positions = [token["position"] for token in tokens]

            expected_positions = list(range(len(tokens)))

            if sorted(positions) != expected_positions:
                errors.append(
                    {
                        "path": f"{path}.tokens",
                        "message": (
                            "Позиции tokens должны образовывать "
                            f"последовательность 0..{len(tokens) - 1} "
                            "без пропусков и повторений."
                        ),
                    }
                )

        return errors

    def _validate_duplicate_exercises(
        self,
        exercises: Any,
    ) -> list[dict[str, str]]:
        errors = []

        if not isinstance(exercises, list):
            return errors

        seen: dict[tuple[str, str, str], int] = {}

        for index, exercise in enumerate(exercises):
            if not isinstance(exercise, dict):
                continue

            key = (
                exercise.get("title", "").strip(),
                exercise.get("type", ""),
                exercise.get("level", ""),
            )

            if key in seen:
                first_index = seen[key]

                errors.append(
                    {
                        "path": f"exercises[{index}]",
                        "message": (
                            "Дублирующееся упражнение в файле. "
                            f"Первое вхождение: exercises[{first_index}]."
                        ),
                    }
                )
            else:
                seen[key] = index

        return errors

    # ------------------------------------------------------------------
    # Database import
    # ------------------------------------------------------------------

    def _create_exercise(
        self,
        exercise_data: dict[str, Any],
        language: str,
        fallback_order: int,
    ) -> Exercise:
        exercise = Exercise.objects.create(
            title=exercise_data["title"],
            exercise_type=exercise_data["type"],
            language=language,
            level=exercise_data["level"],
            is_active=exercise_data.get("active", True),
            order=exercise_data.get("order", fallback_order),
        )

        self._assign_topics(
            exercise=exercise,
            topic_names=exercise_data["topics"],
        )

        exercise_type = exercise_data["type"]
        data = exercise_data["data"]

        if exercise_type == "vocabulary_drill":
            self._create_vocabulary_items(
                exercise=exercise,
                data=data,
            )

        elif exercise_type == "multiple_choice":
            self._create_multiple_choice_items(
                exercise=exercise,
                data=data,
            )

        elif exercise_type == "dropdown":
            self._create_dropdown_items(
                exercise=exercise,
                data=data,
            )

        elif exercise_type == "gap_fill":
            self._create_gap_fill_items(
                exercise=exercise,
                data=data,
            )

        elif exercise_type == "sentence_builder":
            self._create_sentence_builder_items(
                exercise=exercise,
                data=data,
            )

        return exercise

    def _assign_topics(
        self,
        exercise: Exercise,
        topic_names: list[str],
    ) -> None:
        topics = []

        for topic_name in topic_names:
            topic, _ = Topic.objects.get_or_create(name=topic_name.strip())
            topics.append(topic)

        exercise.topics.set(topics)

    def _create_vocabulary_items(
        self,
        exercise: Exercise,
        data: dict[str, Any],
    ) -> None:
        for index, item in enumerate(data["items"]):
            VocabularyItem.objects.create(
                exercise=exercise,
                prompt=item["word"],
                correct_answer=item["correct"],
                distractor_1=item["distractors"][0],
                distractor_2=item["distractors"][1],
                distractor_3=item["distractors"][2],
                order=index,
            )

    def _create_multiple_choice_items(
        self,
        exercise: Exercise,
        data: dict[str, Any],
    ) -> None:
        for item_index, item in enumerate(data["items"]):
            multiple_choice_item = MultipleChoiceItem.objects.create(
                exercise=exercise,
                question=item["question"],
                selection_mode=item["selection_mode"],
                order=item_index,
            )

            for option_index, option in enumerate(item["options"]):
                MultipleChoiceOption.objects.create(
                    item=multiple_choice_item,
                    text=option["text"],
                    is_correct=option["correct"],
                    order=option_index,
                )

    def _create_dropdown_items(
        self,
        exercise: Exercise,
        data: dict[str, Any],
    ) -> None:
        for item_index, item in enumerate(data["items"]):
            dropdown_item = DropdownItem.objects.create(
                exercise=exercise,
                order=item_index,
            )

            for part_index, part in enumerate(item["parts"]):
                dropdown_part = DropdownPart.objects.create(
                    item=dropdown_item,
                    part_type=part["type"],
                    text=part.get("text", ""),
                    order=part_index,
                )

                if part["type"] == "select":
                    for option_index, option in enumerate(part["options"]):
                        DropdownOption.objects.create(
                            part=dropdown_part,
                            text=option["text"],
                            is_correct=option["correct"],
                            order=option_index,
                        )

    def _create_gap_fill_items(
        self,
        exercise: Exercise,
        data: dict[str, Any],
    ) -> None:
        for item_index, item in enumerate(data["items"]):
            gap_fill_item = GapFillItem.objects.create(
                exercise=exercise,
                text=item["text"],
                order=item_index,
            )

            for gap_index, gap in enumerate(item["gaps"]):
                GapFillGap.objects.create(
                    item=gap_fill_item,
                    placeholder=gap["placeholder"],
                    correct_answer=gap["correct"],
                    order=gap_index,
                )

    def _create_sentence_builder_items(
        self,
        exercise: Exercise,
        data: dict[str, Any],
    ) -> None:
        for item_index, item in enumerate(data["items"]):
            sentence_builder_item = SentenceBuilderItem.objects.create(
                exercise=exercise,
                order=item_index,
            )

            for token_index, token in enumerate(item["tokens"]):
                SentenceBuilderToken.objects.create(
                    item=sentence_builder_item,
                    text=token["text"],
                    correct_position=token["position"],
                    order=token_index,
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_json_path(path: Any) -> str:
        """
        Преобразует jsonschema absolute_path в удобный путь.

        Например:
        ["exercises", 2, "data", "items", 0, "options"]

        ->
        exercises[2].data.items[0].options
        """

        if not path:
            return "root"

        result = ""

        for part in path:
            if isinstance(part, int):
                result += f"[{part}]"
            else:
                if result:
                    result += "."

                result += str(part)

        return result
