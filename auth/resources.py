from import_export import resources, fields
from datetime import datetime

from organisation.models import School
from auth.models import Learner, Teacher
from core.models import ParticipantQuestionAnswer
from core.models import Participant, Class


class LearnerResource(resources.ModelResource):
    class_name = fields.Field(column_name=u'class')
    completed_questions = fields.Field(column_name=u'completed_questions')
    percentage_correct = fields.Field(column_name=u'percentage_correct')
    default_country = 'South Africa'

    class Meta:
        model = Learner
        exclude = (
            'customuser_ptr', 'password', 'last_login', 'is_superuser',
            'groups', 'user_permissions', 'is_staff', 'is_active',
            'date_joined', 'unique_token', 'unique_token_expiry'
            'welcome_message_sent', 'welcome_message'
        )
        export_order = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'school',
            'country',
            'area',
            'city',
            'optin_sms',
            'optin_email',
            'completed_questions',
            'percentage_correct',
            'class_name',
        )

    def dehydrate_class_name(self, learner):
        participant = Participant.objects.filter(learner=learner)
        if participant.first() is not None:
            return participant.first().classs.name
        else:
            return ""

    def dehydrate_school(self, learner):
        if learner.school is not None:
            return learner.school.name
        else:
            return ""

    def dehydrate_completed_questions(self, learner):
        return ParticipantQuestionAnswer.objects.filter(
            participant__learner=learner
        ).count()

    def dehydrate_percentage_correct(self, learner):
        complete = self.dehydrate_completed_questions(learner)
        if complete > 0:
            return ParticipantQuestionAnswer.objects.filter(
                participant__learner=learner,
                correct=True
            ).count() * 100 / complete
        else:
            return 0

    def get_or_init_instance(self, instance_loader, row):
        row[u'is_staff'] = False
        row[u'is_superuser'] = False
        row[u'is_active'] = True
        row[u'date_joined'] = datetime.now()
        row[u'welcome_message_sent'] = None
        row[u'welcome_message'] = None

        return super(resources.ModelResource, self) \
            .get_or_init_instance(instance_loader, row)

    def import_obj(self, obj, data, dry_run):
        school, created = School.objects.get_or_create(name=data[u'school'])
        data[u'school'] = school.id

        if type(data[u'username']) == float or type(data[u'username']) == int:
            data[u'username'] = str(int(data[u'username']))

        data[u'mobile'] = data[u'username']

        if dry_run:
            rows = Learner.objects.filter(mobile=data[u'mobile']).count()
            if rows > 0:
                raise Exception('mobile number %s has already been used'
                    % (data[u'mobile']))
        else:
            if not obj.mobile:
                obj.mobile = data['username']
            if not obj.country:
                country = data[u'country']
                if country and len(country) > 0:
                    obj.country = country
                else:
                    obj.country = self.default_country
        return super(resources.ModelResource, self)\
            .import_obj(obj, data, dry_run)

    def save_m2m(self, obj, data, dry_run):
        obj.class_name = data[u'class']
        classs = Class.objects.filter(name=data[u'class']).first()

        # If the course and respective class exist, create participant
        if classs and not dry_run:
            Participant.objects.create(
                learner=obj,
                classs=classs,
                datejoined=datetime.now(),
            )
        elif not classs and data[u'class'] is not None:
            error = ("Invalid class '%s' provided for user %s"
                     % (data[u'class'], data["username"]))
            raise Exception(error)

        return super(resources.ModelResource, self)\
            .save_m2m(obj, data, dry_run)


class TeacherResource(resources.ModelResource):
    class_name = fields.Field(column_name=u'class')
    students_completed_questions = fields.Field(column_name=u'students_completed_questions')
    students_percentage_correct = fields.Field(column_name=u'students_percentage_correct')
    default_country = 'South Africa'

    class Meta:
        model = Teacher
        exclude = (
            'customuser_ptr', 'password', 'last_login', 'is_superuser',
            'groups', 'user_permissions', 'is_staff', 'is_active',
            'date_joined', 'unique_token', 'unique_token_expiry'
            'welcome_message_sent', 'welcome_message'
        )
        export_order = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'school',
            'country',
            'area',
            'city',
            'optin_sms',
            'optin_email',
            'students_completed_questions',
            'students_percentage_correct',
        )

    def dehydrate_school(self, teacher):
        if teacher.school is not None:
            return teacher.school.name
        else:
            return ""

    def dehydrate_students_completed_questions(self, teacher):
        return ParticipantQuestionAnswer.objects.filter(
            participant__classs__teacher=teacher
        ).count()

    def dehydrate_students_percentage_correct(self, teacher):
        complete = self.dehydrate_students_completed_questions(teacher)
        if complete > 0:
            return ParticipantQuestionAnswer.objects.filter(
                participant__classs__teacher=teacher,
                correct=True
            ).count() * 100 / complete
        else:
            return 0

    def get_or_init_instance(self, instance_loader, row):
        row[u'is_staff'] = False
        row[u'is_superuser'] = False
        row[u'is_active'] = True
        row[u'date_joined'] = datetime.now()
        row[u'welcome_message_sent'] = None
        row[u'welcome_message'] = None

        return super(resources.ModelResource, self) \
            .get_or_init_instance(instance_loader, row)

    def import_obj(self, obj, data, dry_run):
        school, created = School.objects.get_or_create(name=data[u'school'])
        data[u'school'] = school.id

        if type(data[u'username']) == float or type(data[u'username']) == int:
            data[u'username'] = str(int(data[u'username']))

        data[u'mobile'] = data[u'username']

        if dry_run:
            rows = Teacher.objects.filter(mobile=data[u'mobile']).count()
            if rows > 0:
                raise Exception('mobile number %s has already been used' % data[u'mobile'])
        else:
            if not obj.mobile:
                obj.mobile = data['username']
            if not obj.country:
                country = data[u'country']
                if country and len(country) > 0:
                    obj.country = country
                else:
                    obj.country = self.default_country
        return super(resources.ModelResource, self)\
            .import_obj(obj, data, dry_run)