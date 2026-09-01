# exercises/management/commands/seed_data.py

from django.core.management.base import BaseCommand
from django.db import transaction
from exercises.models import Topic, Exercise, VocabularyCard, Sentence, GapOption


class Command(BaseCommand):
    help = "Наполняет базу данных упражнениями по теме Reflexivpronomen"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("🌱 Начинаем наполнение базы данных...")

        # === 1. Создаём темы ===
        topics_data = [
            {"name": "Reflexivpronomen", "description": "Возвратные местоимения (mich, dich, sich, uns, euch)"},
        ]

        topics = {}
        for t in topics_data:
            topic, _ = Topic.objects.get_or_create(
                name=t["name"], defaults={"description": t["description"]}
            )
            topics[t["name"]] = topic
            self.stdout.write(self.style.SUCCESS(f"  ✅ Тема: {topic.name}"))

        # === 2. VOCABULARY DRILL Упражнение ===
        vocab_exercises = [
            {
                "title": "Reflexivpronomen - Vokabeln",
                "topic": "Reflexivpronomen",
                "order": 1,
                "cards": [
                    {"word": "sich ausruhen", "translation": "отдыхать", "distractors": ["работать", "спать", "бежать"]},
                    {"word": "sich ärgern", "translation": "злиться", "distractors": ["радоваться", "играть", "читать"]},
                    {"word": "sich erinnern", "translation": "вспоминать", "distractors": ["забывать", "видеть", "слышать"]},
                    {"word": "sich anmelden", "translation": "записываться", "distractors": ["отменять", "приходить", "уходить"]},
                    {"word": "sich beeilen", "translation": "торопиться", "distractors": ["медлить", "отдыхать", "ждать"]},
                    {"word": "sich fühlen", "translation": "чувствовать себя", "distractors": ["выглядеть", "звучать", "пахнуть"]},
                    {"word": "sich treffen", "translation": "встречаться", "distractors": ["прощаться", "звонить", "писать"]},
                    {"word": "sich freuen", "translation": "радоваться", "distractors": ["грустить", "сердиться", "бояться"]},
                ],
            },
        ]

        # === 3. GAP FILL Упражнение ===
        gap_fill_exercises = [
            {
                "title": "Reflexivpronomen - Sätze",
                "topic": "Reflexivpronomen",
                "order": 2,
                "sentences": [
                    {"text": "Ich ruhe ___ ein bisschen aus.", "options": ["mich", "dich", "sich", "uns", "euch"], "correct": "mich", "index": 0},
                    {"text": "Sie ärgert ___ über das Hotelzimmer.", "options": ["mich", "dich", "sich", "uns", "euch"], "correct": "sich", "index": 0},
                    {"text": "Ja, ich erinnere ___.", "options": ["mich", "dich", "sich", "uns", "euch"], "correct": "mich", "index": 0},
                    {"text": "Hast du ___ schon für den Surfkurs angemeldet?", "options": ["mich", "dich", "sich", "uns", "euch"], "correct": "dich", "index": 0},
                    {"text": "Ihr müsst ___ beeilen.", "options": ["mich", "dich", "sich", "uns", "euch"], "correct": "euch", "index": 0},
                    {"text": "Aber heute fühlt sie ___ nicht so gut.", "options": ["mich", "dich", "sich", "uns", "euch"], "correct": "sich", "index": 0},
                    {"text": "Wir wollten ___ doch an der Bar treffen.", "options": ["mich", "dich", "sich", "uns", "euch"], "correct": "uns", "index": 0},
                    {"text": "Ich freue ___ schon den ganzen Tag auf einen Cocktail.", "options": ["mich", "dich", "sich", "uns", "euch"], "correct": "mich", "index": 0},
                ],
            },
        ]

        # === 4. Создаём VOCABULARY DRILL ===
        self.stdout.write("\n📚 Создаём Vocabulary Drill упражнения...")
        for ex_data in vocab_exercises:
            exercise, created = Exercise.objects.get_or_create(
                title=ex_data["title"],
                defaults={
                    "exercise_type": "vocabulary_drill",
                    "language": "german",
                    "is_active": True,
                    "order": ex_data["order"],
                },
            )
            if created:
                exercise.topics.add(topics[ex_data["topic"]])
                for i, card in enumerate(ex_data["cards"]):
                    VocabularyCard.objects.create(
                        exercise=exercise,
                        word=card["word"],
                        correct_translation=card["translation"],
                        distractor_1=card["distractors"][0],
                        distractor_2=card["distractors"][1],
                        distractor_3=card["distractors"][2],
                        order=i + 1,
                    )
                self.stdout.write(self.style.SUCCESS(f"  ✅ {exercise.title}"))
            else:
                exercise.order = ex_data["order"]
                exercise.save()
                self.stdout.write(self.style.WARNING(f"  ⚠️ {exercise.title} (уже существует)"))

        # === 5. Создаём GAP FILL ===
        self.stdout.write("\n📝 Создаём Gap Fill упражнения...")
        for ex_data in gap_fill_exercises:
            exercise, created = Exercise.objects.get_or_create(
                title=ex_data["title"],
                defaults={
                    "exercise_type": "gap_fill",
                    "language": "german",
                    "is_active": True,
                    "order": ex_data["order"],
                },
            )
            if created:
                exercise.topics.add(topics[ex_data["topic"]])
                for sent in ex_data["sentences"]:
                    sentence = Sentence.objects.create(
                        exercise=exercise,
                        text=sent["text"],
                        order=ex_data["sentences"].index(sent) + 1,
                    )
                    GapOption.objects.create(
                        sentence=sentence,
                        placeholder_index=sent["index"],
                        options=sent["options"],
                        correct_answer=sent["correct"],
                    )
                self.stdout.write(self.style.SUCCESS(f"  ✅ {exercise.title}"))
            else:
                exercise.order = ex_data["order"]
                exercise.save()
                self.stdout.write(self.style.WARNING(f"  ⚠️ {exercise.title} (уже существует)"))

        # === 6. ИТОГ ===
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("📊 ИТОГО:"))
        self.stdout.write(f"  Темы: {Topic.objects.count()}")
        self.stdout.write(f"  Упражнения: {Exercise.objects.count()}")
        self.stdout.write(
            f"  Gap Fill: {Exercise.objects.filter(exercise_type='gap_fill').count()}"
        )
        self.stdout.write(
            f"  Vocabulary Drill: {Exercise.objects.filter(exercise_type='vocabulary_drill').count()}"
        )
        self.stdout.write(f"  Карточки слов: {VocabularyCard.objects.count()}")
        self.stdout.write(f"  Предложения: {Sentence.objects.count()}")
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("🎉 Готово! Упражнения созданы!"))
        self.stdout.write("\nПроверьте в админке: /admin/")
        self.stdout.write("Или через API: /api/exercises/")