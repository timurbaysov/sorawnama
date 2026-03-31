import json

from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.urls import reverse
from django.utils import translation

from .forms import PsychologistCreationForm, StudentRegistrationForm
from .models import Answer, Option, Question, Student, Survey

User = get_user_model()

TRANSLATIONS_PATH = settings.BASE_DIR / "surveys" / "translations.json"
try:
    with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
        TRANSLATIONS = json.load(f)
except Exception:
    TRANSLATIONS = {}


def _lang_from_request(request):
    return (getattr(request, "LANGUAGE_CODE", "uz") or "uz").split("-")[0]


def _tr(request, key):
    lang = _lang_from_request(request)
    return TRANSLATIONS.get(key, {}).get(lang, key)


def _study_language_label(value):
    mapping = {
        1: "UZB",
        2: "QQ",
        3: "RUS",
    }
    return mapping.get(value, "-")


def _is_non_empty(value):
    return bool((value or "").strip())


def _score_from_option_value(value):
    return max(0, min((value or 1) - 1, 2))


def _category_from_score(score, max_score):
    if max_score <= 0:
        return "red"
    if score <= max_score * 0.5:
        return "red"
    if score <= max_score * 0.75:
        return "yellow"
    return "green"


def _text_for_lang(instance, lang):
    return getattr(instance, f"text_{lang}", "") or ""


def _survey_available_languages(survey):
    available = {"uz": True, "kk": True, "ru": True}
    for lang in ("uz", "kk", "ru"):
        if not _is_non_empty(getattr(survey, f"title_{lang}", "")):
            available[lang] = False
            continue
        for question in survey.questions.all():
            if not _is_non_empty(_text_for_lang(question, lang)):
                available[lang] = False
                break
            lang_option_count = sum(
                1 for option in question.options.all() if _is_non_empty(_text_for_lang(option, lang))
            )
            if lang_option_count < 2:
                available[lang] = False
                break
    return available


def _is_psychologist_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or hasattr(user, "psychologist_profile"))


def psychologist_required(view_func):
    @login_required
    def wrapped(request, *args, **kwargs):
        if not _is_psychologist_or_superuser(request.user):
            return HttpResponseForbidden(_tr(request, "Доступ разрешен только психологу или суперадмину."))
        return view_func(request, *args, **kwargs)
    return wrapped


def superuser_required(view_func):
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden(_tr(request, "Доступ разрешен только суперадмину."))
        return view_func(request, *args, **kwargs)
    return wrapped


def register_view(request):
    language = _lang_from_request(request)
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST, language=language)
        if form.is_valid():
            user = form.save()
            Student.objects.create(
                user=user,
                group_code=form.cleaned_data["group_code"],
                course=form.cleaned_data["study_language"],
            )
            messages.success(request, _tr(request, "Регистрация завершена. Теперь войдите в систему."))
            return redirect("login")
    else:
        form = StudentRegistrationForm(language=language)
    return render(request, "registration/register.html", {"form": form})


def set_language_view(request):
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    if request.method == "POST":
        lang = request.POST.get("language")
        valid_codes = {code for code, _ in settings.LANGUAGES}
        if lang in valid_codes:
            request.session["site_language"] = lang
            translation.activate(lang)
            response = redirect(next_url)
            response.set_cookie("django_language", lang)
            return response
    return redirect(next_url)


@login_required
def profile_view(request):
    return render(
        request,
        "surveys/profile.html",
        {"student_profile": getattr(request.user, "student_profile", None)},
    )


@login_required
def survey_list_view(request):
    query = (request.GET.get("q") or "").strip()
    surveys = Survey.objects.prefetch_related("questions__options").all().order_by("-id")
    if query:
        surveys = surveys.filter(
            Q(title_uz__icontains=query)
            | Q(title_kk__icontains=query)
            | Q(title_ru__icontains=query)
        )
    student = getattr(request.user, "student_profile", None)
    completed_ids = set()
    if student:
        completed_ids = set(
            Answer.objects.filter(student=student, question__survey__in=surveys)
            .values_list("question__survey_id", flat=True)
            .distinct()
        )
    for survey in surveys:
        available_languages = _survey_available_languages(survey)
        survey.ui_completed = survey.id in completed_ids
        survey.ui_available_current_lang = any(available_languages.values())
        survey.ui_available_languages = available_languages
    return render(request, "surveys/survey_list.html", {"surveys": surveys, "search_query": query})


# --------------- helpers for JSON-based survey save ---------------

def _save_survey_from_json(data, survey=None, creator=None):
    if survey is None:
        survey = Survey.objects.create(
            title_uz=data.get("title_uz", ""),
            title_kk=data.get("title_kk", ""),
            title_ru=data.get("title_ru", ""),
            created_by=creator,
        )
    else:
        survey.title_uz = data.get("title_uz", "")
        survey.title_kk = data.get("title_kk", "")
        survey.title_ru = data.get("title_ru", "")
        survey.save()

    keep_question_ids = set()
    for q_data in data.get("questions", []):
        q_id = q_data.get("id")
        q_fields = {
            "text_uz": q_data.get("text_uz", ""),
            "text_kk": q_data.get("text_kk", ""),
            "text_ru": q_data.get("text_ru", ""),
        }
        if q_id:
            try:
                question = Question.objects.get(id=q_id, survey=survey)
                for k, v in q_fields.items():
                    setattr(question, k, v)
                question.save()
            except Question.DoesNotExist:
                question = Question.objects.create(survey=survey, **q_fields)
        else:
            question = Question.objects.create(survey=survey, **q_fields)
        keep_question_ids.add(question.id)

        keep_option_ids = set()
        for idx, opt in enumerate(q_data.get("options", [])):
            opt_id = opt.get("id")
            opt_fields = {
                "text_uz": opt.get("text_uz", ""),
                "text_kk": opt.get("text_kk", ""),
                "text_ru": opt.get("text_ru", ""),
                "value": opt.get("value", 1),
                "order": idx,
            }
            if opt_id:
                try:
                    option = Option.objects.get(id=opt_id, question=question)
                    for k, v in opt_fields.items():
                        setattr(option, k, v)
                    option.save()
                except Option.DoesNotExist:
                    option = Option.objects.create(question=question, **opt_fields)
            else:
                option = Option.objects.create(question=question, **opt_fields)
            keep_option_ids.add(option.id)

        question.options.exclude(id__in=keep_option_ids).delete()
    survey.questions.exclude(id__in=keep_question_ids).delete()
    return survey


def _survey_to_json(survey):
    data = {
        "title": {"uz": survey.title_uz, "kk": survey.title_kk, "ru": survey.title_ru},
        "questions": [],
    }
    for question in survey.questions.prefetch_related("options").all():
        q_data = {
            "id": question.id,
            "text": {"uz": question.text_uz, "kk": question.text_kk, "ru": question.text_ru},
            "options": [],
        }
        for option in question.options.all():
            q_data["options"].append({
                "id": option.id,
                "text": {"uz": option.text_uz, "kk": option.text_kk, "ru": option.text_ru},
                "value": option.value,
            })
        data["questions"].append(q_data)
    return data


# --------------- survey CRUD views ---------------

@psychologist_required
def survey_create_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": _tr(request, "Некорректный JSON")}, status=400)
        creator = getattr(request.user, "psychologist_profile", None)
        _save_survey_from_json(data, creator=creator)
        return JsonResponse({"status": "ok", "redirect": reverse("survey_list")})
    return render(request, "surveys/survey_edit.html", {"is_create": True, "survey_json": "null"})


@psychologist_required
def survey_edit_view(request, survey_id):
    survey = get_object_or_404(Survey.objects.prefetch_related("questions__options"), id=survey_id)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": _tr(request, "Некорректный JSON")}, status=400)
        _save_survey_from_json(data, survey=survey)
        return JsonResponse({"status": "ok", "redirect": reverse("survey_list")})
    survey_data = _survey_to_json(survey)
    return render(request, "surveys/survey_edit.html", {
        "is_create": False,
        "survey": survey,
        "survey_json": json.dumps(survey_data, ensure_ascii=False),
    })


@superuser_required
def create_psychologist_view(request):
    language = _lang_from_request(request)
    if request.method == "POST":
        form = PsychologistCreationForm(request.POST, language=language)
        if form.is_valid():
            form.save()
            messages.success(request, _tr(request, "Психолог успешно добавлен!"))
            return redirect("users_list")
    else:
        form = PsychologistCreationForm(language=language)
    return render(request, "surveys/create_psychologist.html", {"form": form})


@superuser_required
def users_list_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")
        target_user = get_object_or_404(User, id=user_id)

        if action == "reset_password":
            new_password = (request.POST.get("new_password") or "").strip()
            if not new_password:
                new_password = User.objects.make_random_password(length=10)
            target_user.set_password(new_password)
            target_user.save(update_fields=["password"])
            messages.success(
                request,
                f"{_tr(request, 'Пароль пользователя обновлён.')} {_tr(request, 'Новый пароль')}: {new_password}",
            )
        return redirect("users_list")

    staff_users = User.objects.filter(is_staff=True, is_superuser=False).select_related("psychologist_profile").order_by("-id")
    student_users = User.objects.filter(is_staff=False, is_superuser=False).select_related("student_profile").order_by("-id")
    
    return render(request, "surveys/users_list.html", {
        "staff_users": staff_users,
        "student_users": student_users,
        "title_psychologists": _tr(request, "Психологи"),
        "title_students": _tr(request, "Студенты"),
    })


@login_required
def take_survey_view(request, survey_id):
    if _is_psychologist_or_superuser(request.user):
        messages.info(request, _tr(request, "Психолог использует страницу статистики, а не прохождение опроса."))
        return redirect("survey_statistics", survey_id=survey_id)

    survey = get_object_or_404(Survey.objects.prefetch_related("questions__options"), id=survey_id)
    questions = survey.questions.all()
    student, _ = Student.objects.get_or_create(user=request.user)
    available_languages = _survey_available_languages(survey)
    survey_language_code = request.GET.get("survey_language") or _lang_from_request(request)
    if not available_languages.get(survey_language_code, False):
        for fallback_lang in ("uz", "kk", "ru"):
            if available_languages.get(fallback_lang, False):
                survey_language_code = fallback_lang
                break

    if not questions.exists():
        messages.warning(request, _tr(request, "В этом опросе пока нет вопросов."))
        return redirect("survey_list")

    if Answer.objects.filter(student=student, question__survey=survey).exists():
        messages.info(request, _tr(request, "Вы уже прошли этот опрос. Повторное прохождение недоступно."))
        return redirect("survey_list")

    if request.method == "POST":
        all_answered = True
        for question in questions:
            option_id = request.POST.get(f"question_{question.id}")
            if not option_id:
                all_answered = False
                continue
            try:
                option = Option.objects.get(id=int(option_id), question=question)
                Answer.objects.create(student=student, question=question, selected_option=option)
            except (Option.DoesNotExist, ValueError):
                all_answered = False
            except IntegrityError:
                all_answered = False
        if all_answered:
            messages.success(request, _tr(request, "Ответы успешно сохранены."))
        else:
            messages.warning(request, _tr(request, "Ответьте на все вопросы."))
        return redirect("survey_list")

    existing_answers = {}
    for ans in Answer.objects.filter(student=student, question__survey=survey):
        existing_answers[ans.question_id] = ans.selected_option_id

    survey.ui_title = survey.localized_title(survey_language_code)
    for question in questions:
        question.ui_text = question.localized_text(survey_language_code)
        for option in question.options.all():
            option.ui_text = option.localized_text(survey_language_code)

    return render(request, "surveys/take_survey.html", {
        "survey": survey,
        "questions": questions,
        "survey_language_code": survey_language_code,
        "existing_answers": existing_answers,
        "available_languages": available_languages,
    })


@psychologist_required
def survey_student_answers_view(request, survey_id, student_id):
    survey = get_object_or_404(Survey.objects.prefetch_related("questions__options"), id=survey_id)
    student = get_object_or_404(Student.objects.select_related("user"), id=student_id)
    questions = survey.questions.all()
    available_languages = _survey_available_languages(survey)
    survey_language_code = request.GET.get("survey_language") or _lang_from_request(request)
    if not available_languages.get(survey_language_code, False):
        for fallback_lang in ("uz", "kk", "ru"):
            if available_languages.get(fallback_lang, False):
                survey_language_code = fallback_lang
                break

    existing_answers = {}
    answers_qs = Answer.objects.filter(student=student, question__survey=survey)
    for ans in answers_qs:
        existing_answers[ans.question_id] = ans.selected_option_id

    if not existing_answers:
        messages.warning(request, _tr(request, "Ответы этого студента не найдены по выбранному опросу."))
        return redirect("survey_statistics", survey_id=survey_id)

    survey.ui_title = survey.localized_title(survey_language_code)
    for question in questions:
        question.ui_text = question.localized_text(survey_language_code)
        for option in question.options.all():
            option.ui_text = option.localized_text(survey_language_code)

    return render(request, "surveys/take_survey.html", {
        "survey": survey,
        "questions": questions,
        "survey_language_code": survey_language_code,
        "existing_answers": existing_answers,
        "available_languages": available_languages,
        "review_mode": True,
        "review_student": student,
        "back_to_statistics_url": reverse("survey_statistics", args=[survey.id]),
    })


@psychologist_required
def survey_statistics_view(request, survey_id):
    survey = get_object_or_404(Survey.objects.prefetch_related("questions"), id=survey_id)
    language_code = _lang_from_request(request)
    search_query = (request.GET.get("q") or "").strip()
    question_count = survey.questions.count()
    max_score_per_student = question_count * 2

    students_in_red_category = []
    students_completed = []
    students = (
        Student.objects.filter(answers__question__survey=survey)
        .distinct()
        .select_related("user")
    )
    for student in students:
        answers_qs = student.answers.filter(question__survey=survey).select_related("selected_option")
        total_score = sum(_score_from_option_value(ans.selected_option.value) for ans in answers_qs)
        category = _category_from_score(total_score, max_score_per_student)
        if category == "red":
            category_label = _tr(request, "Красная категория")
        elif category == "yellow":
            category_label = _tr(request, "Желтая категория")
        else:
            category_label = _tr(request, "Зеленая категория")
        item = {
            "student": student,
            "total_score": total_score,
            "max_score": max_score_per_student,
            "category": category,
            "category_label": category_label,
            "study_language": _study_language_label(student.course),
        }
        students_completed.append(item)
        if category == "red":
            haystack = " ".join([
                student.user.get_full_name() or "",
                student.user.username or "",
                student.group_code or "",
            ]).lower()
            if not search_query or search_query.lower() in haystack:
                students_in_red_category.append(item)

    students_completed.sort(key=lambda x: x["total_score"], reverse=True)
    students_in_red_category.sort(key=lambda x: x["total_score"])

    active_tab = request.GET.get("tab", "completed")
    if active_tab not in {"completed", "risk"}:
        active_tab = "completed"
    selected_student = None
    selected_student_answers = []
    selected_student_id = request.GET.get("student")
    if selected_student_id:
        try:
            selected_student = students.filter(id=int(selected_student_id)).first()
        except ValueError:
            selected_student = None
        if selected_student:
            selected_answers_qs = (
                Answer.objects
                .filter(student=selected_student, question__survey=survey)
                .select_related("question", "selected_option")
                .order_by("question_id")
            )
            for answer in selected_answers_qs:
                selected_student_answers.append({
                    "question_text": answer.question.localized_text(language_code),
                    "option_text": answer.selected_option.localized_text(language_code),
                    "score": _score_from_option_value(answer.selected_option.value),
                })

    context = {
        "survey": survey,
        "total_students": Student.objects.filter(answers__question__survey=survey).distinct().count(),
        "question_count": question_count,
        "max_score_per_student": max_score_per_student,
        "students_completed": students_completed,
        "students_in_red_category": students_in_red_category,
        "active_tab": active_tab,
        "selected_student": selected_student,
        "selected_student_answers": selected_student_answers,
        "search_query": search_query,
    }
    return render(request, "surveys/survey_statistics.html", context)


@psychologist_required
def survey_delete_view(request, survey_id):
    if request.method != "POST":
        return HttpResponseForbidden(_tr(request, "Метод не поддерживается."))
    survey = get_object_or_404(Survey, id=survey_id)
    survey.delete()
    messages.success(request, _tr(request, "Опрос удалён."))
    return redirect("survey_list")
