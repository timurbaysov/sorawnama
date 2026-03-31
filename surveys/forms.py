import json

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.conf import settings

from .models import Psychologist

TRANSLATIONS_PATH = settings.BASE_DIR / "surveys" / "translations.json"
try:
    with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
        TRANSLATIONS = json.load(f)
except Exception:
    TRANSLATIONS = {}


def tr(lang, key):
    return TRANSLATIONS.get(key, {}).get(lang, key)


class StudentOnlyAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lang = "uz"
        if self.request is not None:
            lang = (getattr(self.request, "LANGUAGE_CODE", "uz") or "uz").split("-")[0]
        self.error_messages["invalid_login"] = tr(
            lang,
            "Please enter a correct username and password. Note that both fields may be case-sensitive.",
        )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        lang = "uz"
        if self.request is not None:
            lang = (getattr(self.request, "LANGUAGE_CODE", "uz") or "uz").split("-")[0]
        if user.is_superuser:
            raise forms.ValidationError(
                tr(lang, "Суперадмин входит только через /admin."),
                code="superuser_login_forbidden",
            )


class StudentRegistrationForm(UserCreationForm):
    STUDY_LANGUAGE_CHOICES = (
        ("1", "UZB"),
        ("2", "QQ"),
        ("3", "RUS"),
    )

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    group_code = forms.CharField(required=True)
    study_language = forms.TypedChoiceField(
        required=True,
        choices=STUDY_LANGUAGE_CHOICES,
        coerce=int,
        empty_value=None,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "email", "group_code", "study_language", "password1", "password2")

    def __init__(self, *args, **kwargs):
        self.language = (kwargs.pop("language", "uz") or "uz").split("-")[0]
        super().__init__(*args, **kwargs)
        self.fields["first_name"].label = tr(self.language, "Имя")
        self.fields["last_name"].label = tr(self.language, "Фамилия")
        self.fields["email"].label = tr(self.language, "E-mail")
        self.fields["group_code"].label = tr(self.language, "Шифр группы")
        self.fields["study_language"].label = tr(self.language, "Язык обучения")
        self.fields["password1"].label = tr(self.language, "Пароль")
        self.fields["password2"].label = tr(self.language, "Подтверждение пароля")
        self.fields["group_code"].widget.attrs["placeholder"] = "100-24"
        for field in self.fields.values():
            field.error_messages["required"] = tr(self.language, "Это поле обязательно.")
        self.fields["password2"].error_messages["password_mismatch"] = tr(self.language, "Пароли не совпадают.")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(tr(self.language, "Пользователь с таким e-mail уже существует."))
        return email

    def clean_group_code(self):
        group_code = self.cleaned_data["group_code"].strip()
        if not group_code:
            raise forms.ValidationError(tr(self.language, "Шифр группы не может быть пустым."))
        return group_code

    def clean_study_language(self):
        study_language = self.cleaned_data["study_language"]
        if study_language not in (1, 2, 3):
            raise forms.ValidationError(tr(self.language, "Язык обучения должен быть выбран из UZB, QQ, RUS."))
        return study_language

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"]
        user.username = email
        user.email = email
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class PsychologistCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        self.language = (kwargs.pop("language", "uz") or "uz").split("-")[0]
        super().__init__(*args, **kwargs)
        self.fields["first_name"].label = tr(self.language, "Имя")
        self.fields["last_name"].label = tr(self.language, "Фамилия")
        self.fields["email"].label = tr(self.language, "E-mail")
        self.fields["password1"].label = tr(self.language, "Пароль")
        self.fields["password2"].label = tr(self.language, "Подтверждение пароля")
        for field in self.fields.values():
            field.error_messages["required"] = tr(self.language, "Это поле обязательно.")
        self.fields["password2"].error_messages["password_mismatch"] = tr(self.language, "Пароли не совпадают.")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(tr(self.language, "Пользователь с таким e-mail уже существует."))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"]
        user.username = email
        user.email = email
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_staff = True
        if commit:
            user.save()
            Psychologist.objects.get_or_create(user=user)
        return user
