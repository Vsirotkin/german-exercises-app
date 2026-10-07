from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from exercises.services.exercise_import import (
    ExerciseImportService,
    ExerciseImportValidationError,
)


class Command(BaseCommand):
    help = "Validate or import exercises from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            type=str,
            help="Path to the JSON file.",
        )

        mode_group = parser.add_mutually_exclusive_group(required=True)

        mode_group.add_argument(
            "--validate",
            action="store_true",
            help="Validate the JSON without changing the database.",
        )

        mode_group.add_argument(
            "--import",
            dest="import_data",
            action="store_true",
            help="Validate and import the JSON into the database.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])

        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise CommandError(f"Path is not a file: {file_path}")

        service = ExerciseImportService()

        try:
            data = service.load_json(file_path)

        except ExerciseImportValidationError as exc:
            self._print_errors(exc.errors)
            raise CommandError("JSON loading failed.")

        if options["validate"]:
            self._validate(service, data)
            return

        if options["import_data"]:
            self._import(service, data)
            return

    def _validate(
        self,
        service: ExerciseImportService,
        data: dict,
    ) -> None:
        preview = service.preview(data)

        if not preview["valid"]:
            self.stdout.write(self.style.ERROR("Validation failed."))

            self._print_errors(preview["errors"])

            raise CommandError("Exercise file contains validation errors.")

        summary = preview["summary"]

        self.stdout.write(self.style.SUCCESS("Validation successful."))

        self.stdout.write(f"Version: {summary['version']}")

        self.stdout.write(f"Language: {summary['language']}")

        self.stdout.write(f"Exercises: {summary['exercise_count']}")

        self.stdout.write("By type:")

        for exercise_type, count in summary["by_type"].items():
            self.stdout.write(f"  - {exercise_type}: {count}")

        self.stdout.write("Topics:")

        for topic in summary["topics"]:
            self.stdout.write(f"  - {topic}")

    def _import(
        self,
        service: ExerciseImportService,
        data: dict,
    ) -> None:
        preview = service.preview(data)

        if not preview["valid"]:
            self.stdout.write(self.style.ERROR("Validation failed. Import cancelled."))

            self._print_errors(preview["errors"])

            raise CommandError("Exercise file contains validation errors.")

        summary = preview["summary"]

        self.stdout.write(
            f"Ready to import {summary['exercise_count']} " "exercise(s)."
        )

        try:
            result = service.import_exercises(data)

        except ExerciseImportValidationError as exc:
            self.stdout.write(
                self.style.ERROR("Import cancelled because validation failed.")
            )

            self._print_errors(exc.errors)

            raise CommandError("Exercise import failed.")

        except Exception as exc:
            raise CommandError(f"Exercise import failed: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("Import successful."))

        self.stdout.write(f"Created exercises: {result['created_count']}")

        self.stdout.write(
            "Exercise IDs: "
            + ", ".join(str(exercise_id) for exercise_id in result["exercise_ids"])
        )

    def _print_errors(
        self,
        errors: list[dict[str, str]],
    ) -> None:
        self.stdout.write("")

        for error in errors:
            self.stdout.write(
                self.style.ERROR(f"- {error['path']}: {error['message']}")
            )

        self.stdout.write("")
