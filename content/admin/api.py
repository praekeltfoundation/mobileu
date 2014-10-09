'''
A limited RESTful API for editing TestingQuestion and
TestingQuestionOption objects. Only staff members are
authorized to use the API.
'''
from tastypie import fields
from tastypie.api import NamespacedApi
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import NamespacedModelResource, ALL, ALL_WITH_RELATIONS


from organisation.models import Module
from ..models import TestingQuestion, TestingQuestionOption


class BaseResource(NamespacedModelResource):
    class Meta:
        always_return_data = True
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class ModuleResource(NamespacedModelResource):
    class Meta(BaseResource.Meta):
        queryset = Module.objects.all()
        # Note: we are not allowing module creation/deletion via the API for now
        allowed_methods = ['get', 'put']
        fields = ['id', 'name', 'description', 'is_active']
        filtering = {
            'id': ALL
        }


class TestingQuestionResource(NamespacedModelResource):
    module = fields.ToOneField(ModuleResource, 'module')
    options = fields.ToManyField(
        'content.admin.api.TestingQuestionOptionResource',
        'testingquestionoption_set',
        related_name='question',
        full=True
    )

    class Meta(BaseResource.Meta):
        resource_name = 'question'
        queryset = TestingQuestion.objects.all()
        fields = ['id', 'name', 'question_content', 'answer_content',
                  'difficulty', 'points', 'textbook_link']
        filtering = {
            'id': ALL,
            'name': ALL,
            'module': ALL_WITH_RELATIONS
        }


class TestingQuestionOptionResource(NamespacedModelResource):
    question = fields.ToOneField(TestingQuestionResource, 'question')

    class Meta(BaseResource.Meta):
        resource_name = 'option'
        queryset = TestingQuestionOption.objects.all()
        fields = ['id', 'name', 'correct', 'content']
        filtering = {
            'id': ALL,
            'name': ALL,
            'question': ALL_WITH_RELATIONS,
        }


api_v1 = NamespacedApi(api_name='v1', urlconf_namespace='admin')
api_v1.register(ModuleResource())
api_v1.register(TestingQuestionResource())
api_v1.register(TestingQuestionOptionResource())
