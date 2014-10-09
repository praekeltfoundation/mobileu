from django.conf.urls import patterns, include
from django.contrib import admin

from django_summernote.admin import SummernoteModelAdmin, SummernoteInlineModelAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields

from ..models import TestingQuestion, TestingQuestionOption, LearningChapter
from core.models import ParticipantQuestionAnswer
from .api import api_v1


class TestingQuestionOptionInline(SummernoteInlineModelAdmin, admin.StackedInline):
    model = TestingQuestionOption
    extra = 0
    # TODO: fix admin_thumbnail - call it content preview?
    fields = ("name", "correct", "content")
    ordering = ("name", )


class LearningChapterInline(SummernoteInlineModelAdmin, admin.StackedInline):
    model = LearningChapter
    extra = 0
    fields = ("module", "order", "name", "description", "content")
    ordering = ("module", "order", "name", )


class TestingQuestionResource(resources.ModelResource):
    # TODO: this import/export is not functional. Discard or fix.

    class Meta:
        model = TestingQuestion
        fields = (
            'id',
            'name',
            'description',
            'percentage_correct',
            'correct',
            'incorrect'
        )
        export_order = (
            'id',
            'name',
            'description',
            'percentage_correct',
            'correct',
            'incorrect'
        )

    correct = fields.Field(column_name=u'correct')
    incorrect = fields.Field(column_name=u'incorrect')
    percentage_correct = fields.Field(column_name=u'percentage_correct')

    def dehydrate_correct(self, question):
        return ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=True
        ).count()

    def dehydrate_incorrect(self, question):
        return ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=False
        ).count()

    def dehydrate_percentage_correct(self, question):
        correct = ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=True
        ).count()
        total = ParticipantQuestionAnswer.objects.filter(
            question=question
        ).count()

        if total > 0:
            return 100 * correct / total
        else:
            return 0


class TestingQuestionAdmin(SummernoteModelAdmin, ImportExportModelAdmin):
    list_display = ("module", "order", "name", "description",
                    "correct", "incorrect", "percentage_correct")
    list_filter = ("module", )
    search_fields = ("name", "description")

    def correct(self, question):
        return ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=True
        ).count()
    correct.allow_tags = True
    correct.short_description = "Correct"

    def incorrect(self, question):
        return ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=False
        ).count()
    incorrect.allow_tags = True
    incorrect.short_description = "Incorrect"

    def percentage_correct(self, question):
        correct = ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=True
        ).count()
        total = ParticipantQuestionAnswer.objects.filter(
            question=question
        ).count()
        if total > 0:
            return 100 * correct / total
        else:
            return 0
    percentage_correct.allow_tags = True
    percentage_correct.short_description = "Percentage Correct"

    def get_urls(self):
        return patterns('',
            (r'^api/', include(api_v1.urls))
        ) + super(TestingQuestionAdmin, self).get_urls()

    fieldsets = [
        (None,
            {"fields": ["name", "description", "module", "order"]}),
        ("Content",
            {"fields": ["question_content", "answer_content"]}),
        ("Additional fields",
            {"fields": ["textbook_link", "difficulty", "points"],
             "classes": ("collapse",)})
    ]
    inlines = (TestingQuestionOptionInline,)
    resource_class = TestingQuestionResource


# Content
admin.site.register(TestingQuestion, TestingQuestionAdmin)
