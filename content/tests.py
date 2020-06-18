from content.models import TestingQuestion, Mathml, SUMit, Event, TestingQuestionOption, EventQuestionRel, \
    EventQuestionAnswer
from content.forms import process_mathml_content, render_mathml, convert_to_tags, convert_to_text, \
    TestingQuestionCreateForm
from organisation.models import Course, Module, CourseModuleRel, School, Organisation
from auth.models import Learner
from core.models import Participant, Class, ParticipantBadgeTemplateRel, ParticipantQuestionAnswer
from content.tasks import end_event_processing_body, sms_new_questions_body
from mobileu.tasks import send_sumit_counts_body

from django.test import TestCase
from datetime import datetime, timedelta
from mock import ANY, patch
from django.conf import settings
import responses
import os


class TestContent(TestCase):

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_module(self, name, course, **kwargs):
        module = Module.objects.create(name=name, **kwargs)
        rel = CourseModuleRel.objects.create(course=course, module=module)
        module.save()
        rel.save()
        return module

    def create_class(self, name, course, **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_organisation(self, name='organisation name', **kwargs):
        return Organisation.objects.create(name=name, **kwargs)

    def create_test_question(self, name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)

    def create_test_question_option(self, name, question, correct=True):
        return TestingQuestionOption.objects.create(
            name=name, question=question, correct=correct)

    def create_school(self, name, organisation, **kwargs):
        return School.objects.create(
            name=name,
            organisation=organisation,
            **kwargs)

    def create_learner(self, school, **kwargs):
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        return Participant.objects.create(
            learner=learner,
            classs=classs,
            **kwargs)

    def delete_test_question(self, question, **kwargs):
        question.delete()

    def setUp(self):
        self.course = self.create_course()
        self.module = self.create_module('module', self.course)
        self.classs = self.create_class('class name', self.course)
        self.question = self.create_test_question('question', self.module)
        self.fake_mail_msg = ""
        self.organisation = self.create_organisation()
        self.school = self.create_school('school name', self.organisation)
        self.learner = self.create_learner(
            self.school,
            mobile="+27123456789",
            country="country")
        self.participant = self.create_participant(
            self.learner,
            self.classs,
            datejoined=datetime.now()
        )

    @responses.mock.activate
    def create_test_question_helper(self, q_content, a_content, index):
        responses.mock.add(responses.mock.POST,
                           settings.MATHML_URL,
                           body='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAAAXNSR0IArs4c6Q' +
                                'AAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAEnQAABJ0Ad5mH3gAAAAMSURBVBhXY/j//z8ABf4C/qc1gYQAAA' +
                                'AASUVORK5CYII=',
                           status=200,
                           stream=True)
        old_path = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = "/tmp/"

        question_content = "Please solve the following mess: %s" % q_content
        answer_content = "<div><strong>This is the answer: </strong><div>%s" % a_content

        testing_question = self.create_test_question("question_%d" % index, self.module,
                                                     question_content=question_content,
                                                     answer_content=answer_content)

        content = process_mathml_content(question_content, 0, testing_question.id)

        #does the question content contain the img tag
        self.assertNotEquals(testing_question.question_content, content)

        not_rendered = Mathml.objects.filter(rendered=False, source_id=testing_question.id).count()
        render_mathml()
        rendered = Mathml.objects.filter(rendered=True, source_id=testing_question.id).count()

        # check if any not rendered mathml has been rendered
        self.assertEquals(not_rendered, rendered)

        m = Mathml.objects.filter(source_id=testing_question.id)
        self.assertEquals(m.count(), 1)
        self.assertEquals(m[0].rendered, True)

        # Test extraction
        self.assertEquals(convert_to_tags(m[0].mathml_content), q_content)

        settings.MEDIA_ROOT = old_path

    def test_create_test_question(self):

        # normal mathml content
        question_content = "<math xmlns='http://www.w3.org/1998/Math/MathML' display='block'>" \
                           "<msup>" \
                           "<mi>x</mi>" \
                           "<mn>2</mn>" \
                           "<mo>+</mo>" \
                           "<mi>y</mi>" \
                           "<mn>2</mn>" \
                           "</msup>" \
                           "</math>"

        answer_content = "<math xmlns='http://www.w3.org/1998/Math/MathML' display='block'>" \
                         "<msup>" \
                         "<mi>x</mi>" \
                         "<mn>2</mn>" \
                         "<mo>+</mo>" \
                         "<mi>y</mi>" \
                         "<mn>2</mn>" \
                         "</msup>" \
                         "</math>"

        self.create_test_question_helper(question_content, answer_content, 1)

        # namespaced mathml tags
        question_content = "<mml:math xmlns:mml='http://www.w3.org/1998/Math/MathML'>" \
                           "<mml:msup>" \
                           "<mml:mi>x</mml:mi>" \
                           "<mml:mn>2</mml:mn>" \
                           "<mml:mo>+</mml:mo>" \
                           "<mml:mi>y</mml:mi>" \
                           "<mml:mn>2</mml:mn>" \
                           "</mml:msup>" \
                           "</mml:math>"

        answer_content = "<mml:math xmlns:mml='http://www.w3.org/1998/Math/MathML' display='block'>" \
                         "<mml:msup>" \
                         "<mml:mi>x</mml:mi>" \
                         "<mml:mn>2</mml:mn>" \
                         "<mml:mo>+</mml:mo>" \
                         "<mml:mi>y</mml:mi>" \
                         "<mml:mn>2</mml:mn>" \
                         "</mml:msup>" \
                         "</mml:math>"

        self.create_test_question_helper(question_content, answer_content, 2)

    def test_delete_test_question(self):
        q = self.create_test_question('question?', self.module)
        self.delete_test_question(q)
        self.assertEqual(len(TestingQuestion.objects.filter(name=q.name)), 0, 'Q2 not deleted')

    def test_linebreaks(self):
        content = "<p>heading</p><p>content</p>"

        self.question.question_content = content
        self.question.save()

        self.assertEquals(
            self.question.question_content,
            u'<div>heading<br/>content<br/></div>')

    def test_html_sanitize(self):
        content = "<body><head></head><p><b><strike><img>" \
                  "<a href='/test'>Test</a><strike></b></p></body>"

        self.question.question_content = content
        self.question.save()

        self.assertEquals(
            self.question.question_content,
            u'<div><b><img/><a href="/test">Test</a></b><br/></div>')

    def test_convert_to_tags(self):
        content = ''
        tag_content = ''

        converted_content = convert_to_tags(content)

        self.assertEquals(converted_content, tag_content, "Incorrect tag conversion")

    def test_process_math_content(self):
        testing_question = TestingQuestion.objects.filter(name='question').first()

        mathml_content = "Content without mathml markup"
        expected_output = "Content without mathml markup"
        output = process_mathml_content(mathml_content, '0', testing_question.id)
        self.assertEquals(output, expected_output, "They are not equal")

        mathml_content = "Content with mathml markup <mathxmlns='http://www.w3.org/1998/Math/MathML' display='block'>" \
                         "</math> more text"
        expected_output = "Content with mathml markup <img src='/"
        output = process_mathml_content(mathml_content, '0', testing_question.id)

        if expected_output not in output:
            raise Exception

    def test_convert_to_tags(self):
        content = "text &lt;math&gt;x&lt;/math&gt; more text"
        expected_output = "text <math>x</math> more text"
        output = convert_to_tags(content)
        self.assertEquals(output, expected_output, "They are not equal")

    def test_convert_to_text(self):
        content = "text <math>x</math> more text"
        expected_output = "text &lt;math&gt;x&lt;/math&gt; more text"
        output = convert_to_text(content)
        self.assertEquals(output, expected_output, "They are not equal")

    @patch("content.models.mail_managers")
    def test_sumit_create_questions(self, mocked_mail_manages):
        s = SUMit()
        s.course = self.course
        s.name = "Test"
        q = self.create_test_question(
            'question2',
            self.module,
            difficulty=TestingQuestion.DIFF_EASY,
            state=TestingQuestion.PUBLISHED
        )
        q2 = self.create_test_question(
            'question3',
            self.module,
            difficulty=TestingQuestion.DIFF_NORMAL,
            state=TestingQuestion.PUBLISHED
        )
        q3 = self.create_test_question(
            'question4',
            self.module,
            difficulty=TestingQuestion.DIFF_ADVANCED,
            state=TestingQuestion.PUBLISHED
        )
        s.get_questions()
        mocked_mail_manages.assert_called_once_with(
            subject="Test SUMit! - NOT ENOUGH QUESTIONS",
            message="Test SUMit! does not have enough questions. \nEasy Difficulty requires 14 questions"
                    "\nNormal Difficulty requires 10 questions\nAdvanced Difficulty requires 4 questions",
            fail_silently=False)

    #TODO def test_render_mathml(self):

    def create_eov_event(self):
        return Event.objects.create(
            name="Test Event",
            course=self.course,
            activation_date=datetime(2015, 8, 3, 1, 0, 0),
            deactivation_date=datetime(2015, 8, 9, 23, 59, 59),
            number_sittings=Event.MULTIPLE,
            event_points=10,
            type=Event.ET_EXAM,
        )

    def test_end_of_event_task_no_events(self):
        self.assertEquals(Event.objects.all().count(), 0)

        # Test empty run doesn't crash it
        end_event_processing_body()

    def test_end_of_event_task_event_with_no_answers(self):
        e = self.create_eov_event()
        self.assertEquals(Event.objects.all().count(), 1)

        end_event_processing_body()

        e = Event.objects.get(pk=e.pk)

        # event got processed
        self.assertEquals(e.end_processed, True)

        # check that it doesn't crash
        end_event_processing_body()

    def answer_event_question(self, event, question, question_option, correct, answer_date, participant):
        return EventQuestionAnswer.objects.create(
            event=event,
            participant=participant,
            question=question,
            question_option=question_option,
            correct=correct,
            answer_date=answer_date
        )

    def test_end_of_event_task_event_with_answers(self):
        e = self.create_eov_event()
        self.assertEquals(Event.objects.all().count(), 1)

        q = self.create_test_question(
            'question2',
            self.module,
            difficulty=TestingQuestion.DIFF_EASY,
            state=TestingQuestion.PUBLISHED,
        )

        qo = self.create_test_question_option(name="q2_o1", question=q)

        eqr = EventQuestionRel.objects.create(order=1, event=e, question=q)
        self.answer_event_question(event=e, question=q, question_option=qo, correct=True, answer_date=datetime.now(),
                                   participant=self.participant)

        end_event_processing_body()

        e = Event.objects.get(pk=e.pk)

        # event got processed
        self.assertEquals(e.end_processed, True)

        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        # check that it doesn't crash
        end_event_processing_body()

        # ensure no double awarding took place on the second run
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

    def test_end_of_event_task_event_with_answers_for_multiple_learners_both_awarded(self):
        e = self.create_eov_event()
        self.assertEquals(Event.objects.all().count(), 1)

        self.learner2 = self.create_learner(
            self.school,
            mobile="+27123456781",
            country="country",
            username="+27123456781",
        )

        self.participant2 = self.create_participant(
            self.learner2,
            self.classs,
            datejoined=datetime.now()
        )

        q = self.create_test_question(
            'question3',
            self.module,
            difficulty=TestingQuestion.DIFF_EASY,
            state=TestingQuestion.PUBLISHED,
        )

        qo = self.create_test_question_option(name="q3_o1", question=q)

        eqr = EventQuestionRel.objects.create(order=1, event=e, question=q)
        self.answer_event_question(event=e, question=q, question_option=qo, correct=True, answer_date=datetime.now(),
                                   participant=self.participant)
        self.answer_event_question(event=e, question=q, question_option=qo, correct=True, answer_date=datetime.now(),
                                   participant=self.participant2)

        end_event_processing_body()

        e = Event.objects.get(pk=e.pk)

        # event got processed
        self.assertEquals(e.end_processed, True)

        # participant 1 got awarded the badge
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        # participant 2 got awarded the badge
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant2, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        # check that it doesn't crash
        end_event_processing_body()

        # ensure no double awarding took place on the second run
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant2, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

    def test_end_of_event_task_event_with_answers_for_multiple_learners_first_awarded(self):
        e = self.create_eov_event()
        self.assertEquals(Event.objects.all().count(), 1)

        self.learner2 = self.create_learner(
            self.school,
            mobile="+27123456781",
            country="country",
            username="+27123456781"
        )

        self.participant2 = self.create_participant(
            self.learner2,
            self.classs,
            datejoined=datetime.now()
        )

        q = self.create_test_question(
            'question3',
            self.module,
            difficulty=TestingQuestion.DIFF_EASY,
            state=TestingQuestion.PUBLISHED,
        )

        qo = self.create_test_question_option(name="q3_o1", question=q)

        eqr = EventQuestionRel.objects.create(order=1, event=e, question=q)
        self.answer_event_question(event=e, question=q, question_option=qo, correct=True, answer_date=datetime.now(),
                                   participant=self.participant)
        self.answer_event_question(event=e, question=q, question_option=qo, correct=False, answer_date=datetime.now(),
                                   participant=self.participant2)

        end_event_processing_body()

        e = Event.objects.get(pk=e.pk)

        # event got processed
        self.assertEquals(e.end_processed, True)

        # participant 1 got awarded the badge
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        # participant 2 got awarded the badge
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant2, badgetemplate__name="Exam Champ")

        self.assertEquals(awarded_badge.count(), 0)

        # check that it doesn't crash
        end_event_processing_body()

        # ensure no double awarding took place on the second run
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant2, badgetemplate__name="Exam Champ")

        self.assertEquals(awarded_badge.count(), 0)

    def test_sumit_counts(self):
        s = SUMit.objects.create(name='Blarg',
                                 course=self.course,
                                 activation_date=datetime.now()+timedelta(hours=12),
                                 deactivation_date=datetime.now()+timedelta(hours=24))
        counts = s.get_question_counts()
        self.assertDictEqual(
            {'easy': 0, 'normal': 0, 'advanced': 0},
            counts,
            'Should have no eligible questions, got %s' % str(counts))
        q1 = TestingQuestion.objects.create(name='TQ1',
                                            module=self.module,
                                            question_content='First question?',
                                            state=TestingQuestion.PUBLISHED,
                                            difficulty=TestingQuestion.DIFF_EASY)
        counts = s.get_question_counts()
        self.assertDictEqual(
            {'easy': 1, 'normal': 0, 'advanced': 0},
            counts,
            'Should have easy=1, got %s' % str(counts))
        q2 = TestingQuestion.objects.create(name='TQ2',
                                            module=self.module,
                                            question_content='Second question?',
                                            state=TestingQuestion.PUBLISHED,
                                            difficulty=TestingQuestion.DIFF_NORMAL)
        counts = s.get_question_counts()
        self.assertDictEqual(
            {'easy': 1, 'normal': 1, 'advanced': 0},
            counts,
            'Should have easy=1 and normal=1, got %s' % str(counts))
        q1.delete()
        counts = s.get_question_counts()
        self.assertDictEqual(
            {'easy': 0, 'normal': 1, 'advanced': 0},
            counts,
            'Should have normal=1, got %s' % str(counts))
        q3 = TestingQuestion.objects.create(name='TQ3',
                                            module=self.module,
                                            question_content='Third question?',
                                            state=TestingQuestion.PUBLISHED,
                                            difficulty=TestingQuestion.DIFF_NORMAL)
        counts = s.get_question_counts()
        self.assertDictEqual(
            {'easy': 0, 'normal': 2, 'advanced': 0},
            counts,
            'Should have normal=2, got %s' % str(counts))

    @patch("mobileu.tasks.mail_managers")
    def test_send_sumit_counts_insufficient(self, mocked_mail_managers):
        s = SUMit.objects.create(name='Blarg',
                                 course=self.course,
                                 activation_date=datetime.now()+timedelta(hours=12),
                                 deactivation_date=datetime.now()+timedelta(hours=24))
        send_sumit_counts_body()
        mocked_mail_managers.assert_called_once_with(
            subject="DIG-IT: SUMits with too few questions",
            message=u"SUMits with insufficient questions:" +
                    "\nBlarg: activating " + s.activation_date.strftime('%Y-%m-%d %H:%M') + "\n",
            fail_silently=False)

    @patch("mobileu.tasks.mail_managers")
    def test_send_sumit_counts_sufficient(self, mocked_mail_managers):
        s = SUMit.objects.create(name='Blarg',
                                 course=self.course,
                                 activation_date=datetime.now()+timedelta(hours=12),
                                 deactivation_date=datetime.now()+timedelta(hours=24))
        for i in range(15):
            TestingQuestion.objects.create(name='QE%d' % i,
                                           module=self.module,
                                           question_content='Question E%d?' % i,
                                           state=TestingQuestion.PUBLISHED,
                                           difficulty=TestingQuestion.DIFF_EASY)
        for i in range(11):
            TestingQuestion.objects.create(name='QN%d' % i,
                                           module=self.module,
                                           question_content='Question N%d?' % i,
                                           state=TestingQuestion.PUBLISHED,
                                           difficulty=TestingQuestion.DIFF_NORMAL)
        for i in range(5):
            TestingQuestion.objects.create(name='QA%d' % i,
                                           module=self.module,
                                           question_content='Question A%d?' % i,
                                           state=TestingQuestion.PUBLISHED,
                                           difficulty=TestingQuestion.DIFF_ADVANCED)
        send_sumit_counts_body()
        mocked_mail_managers.assert_not_called()

    def test_module_questions_order_max(self):
        module = Module.objects.get(name='module')
        form_data = {
            'name': 'Auto Generated',
            'module': module.id,
            'content': 'This is some content.',
            'difficulty': 3,
            'state': 1,
            'points': 5,
            'order': 0,
            'testingquestionoption_set-0-correct': True,
            'testingquestionoption_set-0-content': True,
            'testingquestionoption_set-1-correct': True,
            'testingquestionoption_set-1-content': True,
            'testingquestionoption_set-TOTAL_FORMS': 2}
        self.assertTrue(TestingQuestionCreateForm(form_data), 'Generated form is invalid')
        q1 = TestingQuestionCreateForm(form_data.copy()).save()
        q2 = TestingQuestionCreateForm(form_data.copy()).save()
        q3 = TestingQuestionCreateForm(form_data.copy()).save()
        self.delete_test_question(q2)
        q4 = TestingQuestionCreateForm(form_data.copy()).save()
        self.assertLess(q3.order, q4.order, 'Q3.order: %d; Q4.order: %d' % (q3.order, q4.order))

    def test_get_unanswered_participants(self):
        num_learners = 15
        self.learner.delete()
        self.participant.delete()
        self.question.state = self.question.PUBLISHED
        self.question.save()
        option = TestingQuestionOption.objects.create(question=self.question, correct=True)

        # no one has answered the question yet
        for i in range(num_learners):
            learner = Learner.objects.create(username='learn%d' % (i,),
                                             first_name='Learn%d' % (i,),
                                             mobile='012345%04d' % (i,),
                                             school=self.school,
                                             grade="Grade 12")
            participant = Participant.objects.create(learner=learner,
                                                     classs=self.classs,
                                                     datejoined=datetime.now())
        self.assertEqual(self.question.get_unanswered_participants().count(), num_learners)

        # some participants have answered
        num_answered = 5
        for p in Participant.objects.all()[:num_answered]:
            ParticipantQuestionAnswer.objects.create(participant=p,
                                                     question=self.question,
                                                     option_selected=option,
                                                     correct=option.correct)
        self.assertEqual(self.question.get_unanswered_participants().count(), num_learners - num_answered)

        # participant is no longer active
        participant = Participant.objects.all().last()
        participant.is_active = False
        participant.save()
        self.assertEqual(self.question.get_unanswered_participants().count(), num_learners - num_answered - 1)

        # participant is in another class
        new_course = self.create_course(name='Best Course')
        new_class = self.create_class('Best class', new_course)
        participant.is_active = True
        participant.classs = new_class
        participant.save()
        self.assertEqual(self.question.get_unanswered_participants().count(), num_learners - num_answered - 1)

    @patch('content.tasks.VumiSmsApi', autospec=True)
    def test_sms_new_questions_body(self, fake_vumi):
        num_learners = 15
        self.learner.delete()
        self.participant.delete()
        self.question.state = self.question.PUBLISHED
        self.question.save()

        # no one has answered the question yet, single question
        for i in range(num_learners):
            learner = Learner.objects.create(username='learn%d' % (i,),
                                             first_name='Learn%d' % (i,),
                                             mobile='012345%04d' % (i,),
                                             school=self.school,
                                             grade="Grade 12")
            participant = Participant.objects.create(learner=learner,
                                                     classs=self.classs,
                                                     datejoined=datetime.now())
        sms_new_questions_body(TestingQuestion.objects.filter(pk=self.question.id))
        fake_vumi().send_all.assert_called_once_with(ANY, message='Hi, there. We have new questions for you on Dig-it!')
        args, kwargs = fake_vumi().send_all.call_args
        self.assertEqual(len(args), 1)
        self.assertEqual(len(args[0]), num_learners)

        # no one has answered the question yet, multiple questions
        fake_vumi.reset_mock()
        self.question.delete()
        num_questions = 5
        for i in range(num_questions):
            TestingQuestion.objects.create(name='Q%d' % (i,),
                                           module=self.module,
                                           state=TestingQuestion.PUBLISHED)
        questions = TestingQuestion.objects.all()
        sms_new_questions_body(questions)
        fake_vumi().send_all.assert_called_once_with(ANY, message='Hi, there. We have new questions for you on Dig-it!')
        args, kwargs = fake_vumi().send_all.call_args
        self.assertEqual(len(args), 1)
        self.assertEqual(len(args[0]), num_learners)

        # some questions answered
        fake_vumi.reset_mock()
        participant = Participant.objects.all().last()
        for i in range(questions.count()):
            question = questions[i]
            option = TestingQuestionOption.objects.create(name='A%d' % (i,),
                                                          question=question,
                                                          correct=True)
            ParticipantQuestionAnswer.objects.create(question=question,
                                                     participant=participant,
                                                     option_selected=option,
                                                     correct=option.correct)
        sms_new_questions_body(questions)
        fake_vumi().send_all.assert_called_once_with(ANY, message='Hi, there. We have new questions for you on Dig-it!')
        args, kwargs = fake_vumi().send_all.call_args
        self.assertEqual(len(args), 1)
        self.assertEqual(len(args[0]), num_learners - 1)

        # some questions in different module
        fake_vumi.reset_mock()
        ParticipantQuestionAnswer.objects.all().delete()
        num_questions_moved = 2
        new_course = self.create_course(name='Best course')
        new_module = self.create_module('Best module', new_course)
        for question in questions[:num_questions_moved]:
            question.module = new_module
            question.save()
        sms_new_questions_body(questions)
        fake_vumi().send_all.assert_called_once_with(ANY, message='Hi, there. We have new questions for you on Dig-it!')
        args, kwargs = fake_vumi().send_all.call_args
        self.assertEqual(len(args), 1)
        self.assertEqual(len(args[0]), num_learners)

        # some learners in different class, with different modules
        fake_vumi.reset_mock()
        num_participants_moved = 5
        new_class = self.create_class('Best class', new_course)
        participants = Participant.objects.all()
        for participant in participants[:num_participants_moved]:
            participant.classs = new_class
            participant.save()
        sms_new_questions_body(questions)
        fake_vumi().send_all.assert_called_once_with(ANY, message='Hi, there. We have new questions for you on Dig-it!')
        args, kwargs = fake_vumi().send_all.call_args
        self.assertEqual(len(args), 1)
        self.assertEqual(len(args[0]), num_learners)

        # different classes, different modules, some answered
        fake_vumi.reset_mock()
        participant_skip_count = 2
        num_participants_answered = 0
        for participant in participants[::participant_skip_count]:
            for question in questions:
                option = TestingQuestionOption.objects.get(question=question)
                ParticipantQuestionAnswer.objects.create(question=question,
                                                         participant=participant,
                                                         option_selected=option,
                                                         correct=option.correct)
            num_participants_answered += 1
        sms_new_questions_body(questions)
        fake_vumi().send_all.assert_called_once_with(ANY, message='Hi, there. We have new questions for you on Dig-it!')
        args, kwargs = fake_vumi().send_all.call_args
        self.assertEqual(len(args), 1)
        self.assertEqual(len(args[0]), num_learners - num_participants_answered)

        # different classes, different modules, all answered
        fake_vumi.reset_mock()
        ParticipantQuestionAnswer.objects.all().delete()
        num_participants_answered = num_learners
        for participant in participants:
            for question in questions:
                option = TestingQuestionOption.objects.get(question=question)
                ParticipantQuestionAnswer.objects.create(question=question,
                                                         participant=participant,
                                                         option_selected=option,
                                                         correct=option.correct)
        sms_new_questions_body(questions)
        self.assertFalse(fake_vumi.called)
