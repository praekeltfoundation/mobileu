from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView


class QuestionEditingAppView(TemplateView):
    template_name = "admin/content/question_editing_app.html"

    def get_context_data(self, **kwargs):
        context = super(QuestionEditingAppView, self).get_context_data(**kwargs)
        context['title'] = _('Question Editing')
        return context
