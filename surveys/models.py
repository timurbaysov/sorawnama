from django.conf import settings
from django.db import models
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _


class Student(models.Model):
    COURSE_CHOICES = (
        (1, "UZB"),
        (2, "QQ"),
        (3, "RUS"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    group_code = models.CharField(max_length=64, default="UNSET")
    course = models.PositiveSmallIntegerField(choices=COURSE_CHOICES, default=1)

    def __str__(self) -> str:
        return f"{self.user.get_username()} ({self.group_code}, {self.get_course_display()})"


class Psychologist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="psychologist_profile",
    )

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.email or self.user.username


class Survey(models.Model):
    title_uz = models.CharField(max_length=255, default="")
    title_kk = models.CharField(max_length=255, default="")
    title_ru = models.CharField(max_length=255, default="")
    created_by = models.ForeignKey(
        Psychologist,
        on_delete=models.CASCADE,
        related_name="surveys",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def localized_title(self, language_code=None):
        lang = (language_code or get_language() or "ru").split("-")[0]
        if lang == "uz":
            return self.title_uz or self.title_ru or self.title_kk
        if lang == "kk":
            return self.title_kk or self.title_ru or self.title_uz
        return self.title_ru or self.title_uz or self.title_kk

    def __str__(self) -> str:
        return self.title_ru


class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions")
    text_uz = models.TextField(default="")
    text_kk = models.TextField(default="")
    text_ru = models.TextField(default="")

    def localized_text(self, language_code=None):
        lang = (language_code or get_language() or "ru").split("-")[0]
        if lang == "uz":
            return self.text_uz or self.text_ru or self.text_kk
        if lang == "kk":
            return self.text_kk or self.text_ru or self.text_uz
        return self.text_ru or self.text_uz or self.text_kk

    def __str__(self) -> str:
        return self.text_ru[:80]


class Option(models.Model):
    RED = 1
    YELLOW = 2
    GREEN = 3
    VALUE_CHOICES = (
        (RED, _("Красный")),
        (YELLOW, _("Жёлтый")),
        (GREEN, _("Зелёный")),
    )

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text_uz = models.CharField(max_length=255, default="")
    text_kk = models.CharField(max_length=255, default="")
    text_ru = models.CharField(max_length=255, default="")
    value = models.PositiveSmallIntegerField(choices=VALUE_CHOICES)
    order = models.PositiveIntegerField(default=0)

    def localized_text(self, language_code=None):
        lang = (language_code or get_language() or "ru").split("-")[0]
        if lang == "uz":
            return self.text_uz or self.text_ru or self.text_kk
        if lang == "kk":
            return self.text_kk or self.text_ru or self.text_uz
        return self.text_ru or self.text_uz or self.text_kk

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.text_ru[:40]} (value={self.value})"


class Answer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "question"], name="unique_student_question_answer")
        ]

    def __str__(self) -> str:
        return f"{self.student} / {self.question_id} / {self.selected_option.value}"
