# exercises/serializers.py

from rest_framework import serializers
from .models import (
    Topic, Student, Exercise, VocabularyCard, 
    Sentence, GapOption, ExerciseResult, StudentTopicProgress
)

# --- 1. Сериализаторы для вложенных сущностей ---

class VocabularyCardSerializer(serializers.ModelSerializer):
    """
    Сериализатор для карточек слов.
    Формат должен точно соответствовать JSON импорта и ответа фронтенду.
    """
    class Meta:
        model = VocabularyCard
        fields = [
            'id', 'word', 'correct_translation', 
            'distractor_1', 'distractor_2', 'distractor_3', 'order'
        ]

class GapOptionSerializer(serializers.ModelSerializer):
    """Сериализатор для опций пропуска в предложениях."""
    class Meta:
        model = GapOption
        fields = ['id', 'placeholder_index', 'options', 'correct_answer']

class SentenceSerializer(serializers.ModelSerializer):
    """Сериализатор предложений с вложенными опциями."""
    gap_options = GapOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Sentence
        fields = ['id', 'text', 'order', 'gap_options']

# --- 2. Основные Сериализаторы ---

class TopicSerializer(serializers.ModelSerializer):
    """Простой сериализатор тем (название)."""
    class Meta:
        model = Topic
        fields = ['id', 'name', 'description']

class StudentSerializer(serializers.ModelSerializer):
    """Сериализатор профиля студента."""
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'email', 'level', 'created_at']

class ExerciseSerializer(serializers.ModelSerializer):
    """
    Основной сериализатор упражнения.
    Включает вложенные списки карточек или предложений в зависимости от типа.
    + Добавлены поля для статуса прогресса студента
    """
    vocabulary_cards = VocabularyCardSerializer(many=True, read_only=True)
    sentences = SentenceSerializer(many=True, read_only=True)
    topics = serializers.SerializerMethodField()
    
    # 👇 НОВЫЕ ПОЛЯ для индикации прогресса
    score = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            'id', 'title', 'exercise_type', 'topics', 'language', 
            'is_active', 'created_at', 'updated_at', 'order',
            'vocabulary_cards', 'sentences',
            'score', 'status', 'is_locked'  # 👈 Добавили новые поля
        ]

    def get_topics(self, obj):
        # Возвращаем список названий тем: ["Krankenhaus", "Uhrzeit"]
        return [topic.name for topic in obj.topics.all()]

    def _get_student(self):
        """Получить студента из контекста запроса"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                return Student.objects.get(user=request.user)
            except Student.DoesNotExist:
                return None
        return None

    def _get_last_result(self, exercise, student):
        """Получить последний результат студента для упражнения"""
        if not student:
            return None
        return ExerciseResult.objects.filter(
            student=student, 
            exercise=exercise
        ).order_by('-completed_at').first()

    def _calculate_status(self, score_percent):
        """Определить статус по проценту выполнения"""
        if score_percent is None:
            return "not_started"
        elif score_percent == 100:
            return "mastered"
        elif score_percent >= 80:
            return "completed"
        elif score_percent >= 50:
            return "review_recommended"
        else:
            return "needs_review"

    def get_score(self, obj):
        """Вернуть процент выполнения (0-100) из последнего результата"""
        student = self._get_student()
        if not student:
            return None
        
        result = self._get_last_result(obj, student)
        if not result or result.total_questions == 0:
            return None
        
        # 👇 ИСПРАВЛЕНО: возвращаем процент (0-100), а не сырые баллы
        percentage = (result.score / result.total_questions) * 100
        return int(percentage)

    def get_status(self, obj):
        """Вернуть статус упражнения на основе последнего результата"""
        student = self._get_student()
        if not student:
            return "not_started"
        
        result = self._get_last_result(obj, student)
        if not result or result.total_questions == 0:
            return "not_started"
        
        score_percent = (result.score / result.total_questions) * 100
        return self._calculate_status(score_percent)

    def get_is_locked(self, obj):
        """
        Проверить, заблокировано ли упражнение.
        👇 ИСПРАВЛЕНО: Заблокировано ТОЛЬКО если предыдущее упражнение имеет статус < 50% (needs_review)
        Если предыдущее not_started — следующее ДОСТУПНО
        """
        student = self._get_student()
        if not student:
            return False
        
        # Найти предыдущее упражнение (по order - 1)
        prev_exercise = Exercise.objects.filter(
            order=obj.order - 1
        ).first()
        
        if not prev_exercise:
            # Это первое упражнение — не заблокировано
            return False
        
        # Проверить статус предыдущего
        prev_result = self._get_last_result(prev_exercise, student)
        
        # 👇 Если предыдущее упражнение НЕ ПРОЙДЕНО (not_started) — следующее доступно
        if not prev_result or prev_result.total_questions == 0:
            return False
        
        prev_score_percent = (prev_result.score / prev_result.total_questions) * 100
        prev_status = self._calculate_status(prev_score_percent)
        
        # 👇 Заблокировано ТОЛЬКО если предыдущее < 50% (needs_review)
        return prev_status == "needs_review"

# --- 3. Сериализаторы для результатов и аналитики ---

class ExerciseResultSerializer(serializers.ModelSerializer):
    """
    Сериализатор для результатов упражнений.
    - Для POST: student устанавливается автоматически во View
    - Для GET: возвращает полную информацию о студенте
    """
    
    # Для ЧТЕНИЯ (GET) — возвращаем объект студента
    student = StudentSerializer(read_only=True)
    
    # Для ЗАПИСИ (POST) — принимаем ID студента (но мы его не используем, ставим во View)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        source='student',
        write_only=True,
        required=False
    )
    
    # Для ЧТЕНИЯ (GET) — возвращаем название упражнения
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)

    class Meta:
        model = ExerciseResult
        fields = [
            'id', 'student', 'student_id', 'exercise', 'exercise_title', 
            'score', 'total_questions', 'completed_at', 'details'
        ]
        read_only_fields = ['id', 'completed_at', 'student']
    
    def validate(self, attrs):
        score = attrs.get('score')
        total = attrs.get('total_questions')
        
        if score is not None and total is not None and total > 0:
            # 🛡️ Защита: если вдруг прилетит процент вместо баллов, конвертируем
            if score > total:
                attrs['score'] = round((score / 100) * total)
            # Ограничиваем диапазон [0, total]
            attrs['score'] = max(0, min(attrs['score'], total))
            
        return attrs
    
    def create(self, validated_data):
        # Если student не передан явно, пытаемся взять из контекста (request.user)
        if 'student' not in validated_data and 'request' in self.context:
            try:
                student = Student.objects.get(user=self.context['request'].user)
                validated_data['student'] = student
            except Student.DoesNotExist:
                raise serializers.ValidationError({"student": "Student profile not found"})
        
        return super().create(validated_data)

class StudentTopicProgressSerializer(serializers.ModelSerializer):
    topic = TopicSerializer(read_only=True)
    student = StudentSerializer(read_only=True)

    class Meta:
        model = StudentTopicProgress
        fields = [
            'id', 'student', 'topic', 'exercises_completed', 
            'last_practiced', 'mastery_level'
        ]

# --- 4. Сериализаторы для Записи (Input) ---

class VocabularyCardInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyCard
        fields = ['word', 'correct_translation', 'distractor_1', 'distractor_2', 'distractor_3', 'order']

class GapOptionInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = GapOption
        fields = ['placeholder_index', 'options', 'correct_answer']

class SentenceInputSerializer(serializers.ModelSerializer):
    gap_options = GapOptionInputSerializer(many=True)

    class Meta:
        model = Sentence
        fields = ['text', 'order', 'gap_options']

    def create(self, validated_data):
        gap_options_data = validated_data.pop('gap_options')
        # exercise передаётся из родительского сериализатора
        sentence = Sentence.objects.create(**validated_data)
        for option_data in gap_options_data:
            GapOption.objects.create(sentence=sentence, **option_data)
        return sentence

class ExerciseCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания упражнения через API (Импорт JSON).
    """
    vocabulary_cards = VocabularyCardInputSerializer(many=True, required=False)
    sentences = SentenceInputSerializer(many=True, required=False)
    topics = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = Exercise
        fields = [
            'title', 'exercise_type', 'topics', 'language', 'is_active',
            'vocabulary_cards', 'sentences'
        ]

    def create(self, validated_data):
        topics_names = validated_data.pop('topics')
        vocab_cards_data = validated_data.pop('vocabulary_cards', [])
        sentences_data = validated_data.pop('sentences', [])

        exercise = Exercise.objects.create(**validated_data)

        topics = []
        for name in topics_names:
            topic, _ = Topic.objects.get_or_create(name=name)
            topics.append(topic)
        exercise.topics.set(topics)

        for card_data in vocab_cards_data:
            VocabularyCard.objects.create(exercise=exercise, **card_data)

        for sent_data in sentences_data:
            Sentence.objects.create(exercise=exercise, **sent_data)
            # Примечание: gap_options обрабатываются внутри Sentence, 
            # но здесь упрощённая логика. Для полной вложенности нужно доработать.
            
        return exercise
    