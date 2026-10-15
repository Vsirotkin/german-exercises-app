"""
Server-side evaluation for all supported exercise types.

Input format:
[
    {"item_id": 12, "answer": "..."},
    ...
]

Answer formats by exercise type:
- vocabulary_drill: option UUID as a string
- multiple_choice: option IDs as a list (a string is accepted for single mode)
- dropdown: {"part_id": "option_id"}
- gap_fill: {"gap_id": "text"} or {"placeholder": "text"}
- sentence_builder: ["t12", "t10", "t11"]

Correct answers are never included in the returned results.
"""

from collections.abc import Mapping

from django.db.models import Prefetch

from exercises.models import (
    DropdownPart,
    DropdownItem,
    GapFillItem,
    MultipleChoiceItem,
    SentenceBuilderItem,
    VocabularyItem,
)


class EvaluationError(ValueError):
    """Raised when the submitted answer payload is malformed."""


def _normalise_text(value):
    """Compare text answers ignoring surrounding and repeated whitespace."""
    if not isinstance(value, str):
        raise EvaluationError("Text answers must be strings.")

    return " ".join(value.split())


def _id_string(value):
    """Convert an identifier to a comparable string."""
    if isinstance(value, bool) or value is None:
        raise EvaluationError("Invalid identifier.")

    return str(value)


def _parse_submissions(answers):
    """Validate the outer payload and index submissions by item ID."""
    if not isinstance(answers, list):
        raise EvaluationError("'answers' must be a list.")

    submissions = {}

    for entry in answers:
        if not isinstance(entry, Mapping):
            raise EvaluationError("Each answer must be an object.")

        if "item_id" not in entry or "answer" not in entry:
            raise EvaluationError(
                "Each answer must contain 'item_id' and 'answer'."
            )

        item_id = _id_string(entry["item_id"])

        if item_id in submissions:
            raise EvaluationError(
                f"Duplicate answer for item {item_id}."
            )

        submissions[item_id] = entry["answer"]

    return submissions


def _validate_item_ids(submissions, items):
    """Ignore answers for items outside this exercise."""
    valid_ids = {str(item.pk) for item in items}

    for item_id in set(submissions) - valid_ids:
        submissions.pop(item_id, None)


def _result(item_id, is_correct, unit_id=None):
    """Return safe scoring metadata without exposing correct answers."""
    is_correct = bool(is_correct)
    result = {
        "item_id": item_id,
        "is_correct": is_correct,
        "score": int(is_correct),
        "max_score": 1,
        "feedback": (
            "Correct answer." if is_correct else "Incorrect answer."
        ),
    }

    if unit_id is not None:
        result["unit_id"] = unit_id

    return result


def _evaluate_vocabulary(exercise, submissions):
    items = list(
        VocabularyItem.objects
        .filter(exercise=exercise)
        .order_by("order", "id")
    )
    _validate_item_ids(submissions, items)

    results = []

    for item in items:
        submitted = submissions.get(str(item.pk))
        is_correct = (
            submitted is not None
            and str(submitted) == str(item.correct_option_id)
        )

        results.append(_result(item.pk, is_correct))

    return results


def _evaluate_multiple_choice(exercise, submissions):
    items = list(
        MultipleChoiceItem.objects
        .filter(exercise=exercise)
        .prefetch_related("options")
        .order_by("order", "id")
    )
    _validate_item_ids(submissions, items)

    results = []

    for item in items:
        submitted = submissions.get(str(item.pk))

        if submitted is None:
            results.append(_result(item.pk, False))
            continue

        if isinstance(submitted, (str, int)) and not isinstance(
            submitted, bool
        ):
            selected_ids = [str(submitted)]
        elif isinstance(submitted, list):
            selected_ids = [_id_string(value) for value in submitted]
        else:
            raise EvaluationError(
                "Multiple choice answers must be an option ID "
                "or a list of option IDs."
            )

        if len(selected_ids) != len(set(selected_ids)):
            results.append(_result(item.pk, False))
            continue

        options = list(item.options.all())
        option_ids = {str(option.pk) for option in options}

        if not set(selected_ids).issubset(option_ids):
            results.append(_result(item.pk, False))
            continue

        correct_ids = {
            str(option.pk)
            for option in options
            if option.is_correct
        }

        if item.selection_mode == "single" and len(selected_ids) != 1:
            is_correct = False
        else:
            is_correct = (
                bool(correct_ids)
                and set(selected_ids) == correct_ids
            )

        results.append(_result(item.pk, is_correct))

    return results


def _evaluate_dropdown(exercise, submissions):
    items = list(
        DropdownItem.objects
        .filter(exercise=exercise)
        .prefetch_related(
            Prefetch(
                "parts",
                queryset=(
                    # Options are prefetched separately below by Django.
                    DropdownPart.objects
                    .prefetch_related("options")
                    .order_by("order", "id")
                ),
            )
        )
        .order_by("order", "id")
    )
    _validate_item_ids(submissions, items)

    results = []

    for item in items:
        submitted = submissions.get(str(item.pk), {})

        if not isinstance(submitted, Mapping):
            raise EvaluationError(
                "Dropdown answers must be objects mapping part IDs "
                "to option IDs."
            )

        parts = list(item.parts.all())
        select_parts = [
            part for part in parts if part.part_type == "select"
        ]

        valid_keys = {
            str(part.pk) for part in select_parts
        }

        if not set(str(key) for key in submitted).issubset(valid_keys):
            raise EvaluationError(
                f"Answer for dropdown item {item.pk} contains "
                "an unknown part."
            )

        for part in select_parts:
            raw_option_id = submitted.get(str(part.pk))
            if raw_option_id is None:
                raw_option_id = submitted.get(part.pk)

            is_correct = False

            if raw_option_id is not None:
                selected_id = _id_string(raw_option_id)
                options = list(part.options.all())
                option_ids = {str(option.pk) for option in options}

                if selected_id in option_ids:
                    selected = next(
                        option for option in options
                        if str(option.pk) == selected_id
                    )
                    is_correct = selected.is_correct

            results.append(
                _result(item.pk, is_correct, unit_id=part.pk)
            )

    return results


def _evaluate_gap_fill(exercise, submissions):
    items = list(
        GapFillItem.objects
        .filter(exercise=exercise)
        .prefetch_related("gaps")
        .order_by("order", "id")
    )
    _validate_item_ids(submissions, items)

    results = []

    for item in items:
        submitted = submissions.get(str(item.pk), {})

        if not isinstance(submitted, Mapping):
            raise EvaluationError(
                "Gap fill answers must be objects mapping gap IDs "
                "or placeholders to text."
            )

        gaps = list(item.gaps.all())
        valid_keys = {
            str(gap.pk) for gap in gaps
        } | {
            gap.placeholder for gap in gaps
        }

        if not set(str(key) for key in submitted).issubset(valid_keys):
            raise EvaluationError(
                f"Answer for gap-fill item {item.pk} "
                "contains an unknown gap."
            )

        for gap in gaps:
            raw_answer = submitted.get(str(gap.pk))
            if raw_answer is None:
                raw_answer = submitted.get(gap.pk)
            if raw_answer is None:
                raw_answer = submitted.get(gap.placeholder)

            is_correct = False

            if raw_answer is not None:
                is_correct = (
                    _normalise_text(raw_answer)
                    == _normalise_text(gap.correct_answer)
                )

            results.append(
                _result(item.pk, is_correct, unit_id=gap.pk)
            )

    return results


def _evaluate_sentence_builder(exercise, submissions):
    items = list(
        SentenceBuilderItem.objects
        .filter(exercise=exercise)
        .prefetch_related("tokens")
        .order_by("order", "id")
    )
    _validate_item_ids(submissions, items)

    results = []

    for item in items:
        submitted = submissions.get(str(item.pk))

        if submitted is None:
            results.append(_result(item.pk, False))
            continue

        if not isinstance(submitted, list):
            raise EvaluationError(
                "Sentence builder answers must be ordered lists "
                "of token IDs."
            )

        submitted_ids = [_id_string(value) for value in submitted]

        if len(submitted_ids) != len(set(submitted_ids)):
            results.append(_result(item.pk, False))
            continue

        tokens = list(item.tokens.all())
        token_ids = {f"t{token.pk}" for token in tokens}

        if not set(submitted_ids).issubset(token_ids):
            results.append(_result(item.pk, False))
            continue

        expected_ids = [
            f"t{token.pk}"
            for token in sorted(
                tokens,
                key=lambda token: (token.correct_position, token.pk),
            )
        ]

        is_correct = (
            len(submitted_ids) == len(expected_ids)
            and submitted_ids == expected_ids
        )

        results.append(_result(item.pk, is_correct))

    return results


_EVALUATORS = {
    "vocabulary_drill": _evaluate_vocabulary,
    "multiple_choice": _evaluate_multiple_choice,
    "dropdown": _evaluate_dropdown,
    "gap_fill": _evaluate_gap_fill,
    "sentence_builder": _evaluate_sentence_builder,
}


def evaluate_answers(exercise, answers):
    """
    Evaluate an exercise and return backend-calculated scores.

    Returns:
        {
            "score": int,
            "max_score": int,
            "percentage": float,
            "results": [...]
        }
    """
    evaluator = _EVALUATORS.get(exercise.exercise_type)

    if evaluator is None:
        raise EvaluationError(
            f"Unsupported exercise type: {exercise.exercise_type}"
        )

    submissions = _parse_submissions(answers)
    results = evaluator(exercise, submissions)

    max_score = len(results)
    score = sum(1 for result in results if result["is_correct"])
    percentage = (
        round(score / max_score * 100, 2)
        if max_score
        else 0.0
    )

    return {
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "results": results,
    }



def evaluate_exercise(exercise, answers):
    """Public compatibility entry point used by tests and application code."""
    return evaluate_answers(exercise, answers)
