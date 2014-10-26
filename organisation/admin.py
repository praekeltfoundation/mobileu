from django.contrib import admin
from django.core.urlresolvers import reverse
from .models import *
from content.admin import LearningChapterInline


class SchoolInline(admin.TabularInline):
    model = School
    extra = 1
    fields = ("name", "description")
    ordering = ("name", )


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ("name", "description", "order")
    ordering = ("order", )


class CourseModuleInline(admin.TabularInline):
    model = CourseModuleRel
    extra = 1


class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description"]}),
        ("Contact Information", {"fields": ["website", "email"]}),
    ]
    inlines = (SchoolInline,)
    ordering = ("name", )


class SchoolAdmin(admin.ModelAdmin):
    list_display = ("organisation", "name", "description")
    list_filter = ("organisation", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,
            {"fields": ["name", "description", "organisation"]}),
        ("Contact Information", {"fields": ["website", "email"]}),
    ]
    ordering = ("organisation", "name")


class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description", "slug"]})
    ]
    inlines = (CourseModuleInline, )
    ordering = ("name", )


class ModuleAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "order", "is_active", "question_change_url")
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description", "order", "is_active"]})
    ]
    ordering = ("name", "order")
    # NOTE: TestingQuestionInline has been removed for 2 reasons:
    # 1. There might be too many questions.
    # 2. It would separate question editing from question option editing.
    inlines = (LearningChapterInline, )

    def question_change_url(self, obj):
        return '<a href="%s?module__id__exact=%s">Edit questions</a>' % (
            reverse('admin:content_testingquestion_changelist'),
            obj.pk
        )
    question_change_url.allow_tags = True
    question_change_url.short_description = ''


# Organisation
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Module, ModuleAdmin)