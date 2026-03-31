from django.urls import path

from .views import (
    create_psychologist_view,
    profile_view,
    register_view,
    set_language_view,
    survey_create_view,
    survey_delete_view,
    survey_edit_view,
    survey_list_view,
    survey_statistics_view,
    survey_student_answers_view,
    take_survey_view,
    users_list_view,
)

urlpatterns = [
    path("", survey_list_view, name="survey_list"),
    path("profile/", profile_view, name="profile"),
    path("register/", register_view, name="register"),
    path("set-language/", set_language_view, name="set_language"),
    path("survey/create/", survey_create_view, name="survey_create"),
    path("survey/<int:survey_id>/edit/", survey_edit_view, name="survey_edit"),
    path("survey/<int:survey_id>/delete/", survey_delete_view, name="survey_delete"),
    path("survey/<int:survey_id>/student/<int:student_id>/answers/", survey_student_answers_view, name="survey_student_answers"),
    path("survey/<int:survey_id>/", take_survey_view, name="take_survey"),
    path("survey/<int:survey_id>/statistics/", survey_statistics_view, name="survey_statistics"),
    path("admin-tools/create-psychologist/", create_psychologist_view, name="create_psychologist"),
    path("admin-tools/users/", users_list_view, name="users_list"),
]
