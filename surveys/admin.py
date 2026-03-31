from django.contrib import admin
from .models import Answer, Option, Psychologist, Question, Student, Survey


class OptionInline(admin.TabularInline):
    model = Option
    extra = 1


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("id", "title_ru", "title_uz", "title_kk", "created_by", "created_at")
    search_fields = ("title_ru", "title_uz", "title_kk")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "survey", "text_ru")
    list_filter = ("survey",)
    search_fields = ("text_ru", "text_uz", "text_kk")
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "text_ru", "value", "order")
    list_filter = ("value", "question__survey")
    search_fields = ("text_ru", "text_uz", "text_kk")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "question", "get_value", "submitted_at")
    list_filter = ("selected_option__value", "question__survey")
    search_fields = ("student__user__username", "question__text_ru")

    @admin.display(description="Value")
    def get_value(self, obj):
        return obj.selected_option.get_value_display()


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "group_code", "course")
    search_fields = ("user__username", "user__email", "group_code")


@admin.register(Psychologist)
class PsychologistAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
