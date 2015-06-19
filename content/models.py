from django.db import models
from django.core.validators import MaxValueValidator
from organisation.models import Module
from django.core.urlresolvers import reverse
from django.utils.html import remove_tags
from mobileu.utils import format_content, format_option
from django.db.models import Count
from datetime import datetime


class LearningChapter(models.Model):

    """
    Each modules has learning content which can be broken up into chapters.
    Essentially this content is HTML and needs to
    be able to include images, videos, audio clips and hyperlinks to
    external resources. The management interface will
    only expose limited formatting options.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    module = models.ForeignKey(Module, null=True, blank=False)
    content = models.TextField("Content", blank=True)

    def save(self, *args, **kwargs):
        self.content = format_content(self.content)
        super(LearningChapter, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Learning Chapter"
        verbose_name_plural = "Learning Chapters"


class TestingQuestion(models.Model):
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    module = models.ForeignKey(Module, null=True, blank=False)
    question_content = models.TextField("Question", blank=True)
    answer_content = models.TextField("Answer", blank=True)
    difficulty = models.PositiveIntegerField(
        "Difficulty", choices=(
            (1, "Not Specified"),
            (2, "Easy"),
            (3, "Normal"),
            (4, "Advanced")
        ),
        default=1)
    points = models.PositiveIntegerField(
        "Points",
        validators=[MaxValueValidator(500)],
        default=1,
        blank=False,
    )

    textbook_link = models.CharField(
        "Textbook Link",
        max_length=500,
        blank=True,
        null=True)
    state = models.PositiveIntegerField("State",
                                        choices=(
                                            (1, "Incomplete"),
                                            (2, "Ready for Review"),
                                            (3, "Published")
                                        ),
                                        default=1)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.question_content = format_content(self.question_content)
        self.answer_content = format_content(self.answer_content)
        super(TestingQuestion, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Test Question"
        verbose_name_plural = "Test Questions"
        ordering = ['name']


class TestingQuestionOption(models.Model):
    name = models.CharField(
        "Name",
        max_length=500,
        null=True,
        blank=False,
        unique=True)
    question = models.ForeignKey(TestingQuestion, null=True, blank=False)
    order = models.PositiveIntegerField("Order", default=1)
    content = models.TextField("Content", blank=True)
    correct = models.BooleanField("Correct")

    def save(self, *args, **kwargs):
        if self.content:
            self.content = format_option(self.content)
        super(TestingQuestionOption, self).save(*args, **kwargs)

    def link(self):
        if self.id:
            return "<a href='%s' target='_blank'>Edit</a>" % reverse(
                'admin:content_testingquestionoption_change',
                args=[
                    self.id])
        else:
            return "<span>Edit</span>"
    link.allow_tags = True

    def admin_thumbnail(self):
        thumbnail = remove_tags(self.content, "p br")
        return u'%s' % thumbnail
    admin_thumbnail.short_description = 'Content'
    admin_thumbnail.allow_tags = True

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Question Option"
        verbose_name_plural = "Question Options"


class Mathml(models.Model):
    TESTING_QUESTION_QUESTION = 0
    TESTING_QUESTION_ANSWER = 1
    TESTING_QUESTION_OPTION = 2

    SOURCE_CHOICES = (
        (TESTING_QUESTION_QUESTION, 'tq_q'),
        (TESTING_QUESTION_ANSWER, 'tq_a'),
        (TESTING_QUESTION_OPTION, 'tq_o'),
    )

    mathml_content = models.TextField(null=False, blank=False)
    filename = models.CharField(max_length=255, null=False, blank=True)
    rendered = models.BooleanField(default=False)
    source = models.IntegerField(max_length=1, choices=SOURCE_CHOICES)
    source_id = models.IntegerField(null=False, blank=False)
    error = models.TextField(null=False, blank=True)

    def __str__(self):
        return self.filename

allowed_tags = ['b', 'i', 'strong', 'em', 'img', 'a', 'br']
allowed_attributes = ['href', 'title', 'style', 'src']
allowed_styles = [
    'font-family',
    'font-weight',
    'text-decoration',
    'font-variant',
    'width',
    'height']


class GoldenEgg(models.Model):
    course = models.ForeignKey("organisation.Course", null=False, blank=False, verbose_name="Course")
    classs = models.ForeignKey("core.Class", null=True, blank=True, verbose_name="Class")
    active = models.BooleanField(default=False, verbose_name="Is Active")
    point_value = models.PositiveIntegerField(null=True, blank=True, verbose_name="Points")
    airtime = models.PositiveIntegerField(null=True, blank=True)
    badge = models.ForeignKey("gamification.GamificationScenario", null=True, blank=True)

    class Meta:
        verbose_name = "Golden Egg"
        verbose_name_plural = "Golden Eggs"


class GoldenEggRewardLog(models.Model):
    participant = models.ForeignKey("core.Participant", null=False, blank=False)
    award_date = models.DateTimeField(auto_now_add=True)
    points = models.PositiveIntegerField(null=True, blank=True)
    airtime = models.PositiveIntegerField(null=True, blank=True)
    badge = models.ForeignKey("gamification.GamificationScenario", null=True, blank=True)


class Event(models.Model):
    ONE = 1
    MULTIPLE = 2
    SITTINGS_CHOICES = (
        (ONE, "One"),
        (MULTIPLE, "Multiple")
    )

    TYPE_CHOICES = (
        (1, "Spot Test"),
        (2, "Exam")
    )

    name = models.CharField(max_length=50, unique=True)
    course = models.ForeignKey("organisation.Course", null=False, blank=False)
    activation_date = models.DateTimeField("Activate On", null=False, blank=False)
    deactivation_date = models.DateTimeField("Deactivate On", null=False, blank=False)
    number_sittings = models.PositiveIntegerField("Number of Sittings", choices=SITTINGS_CHOICES, default=ONE)
    event_points = models.PositiveIntegerField("Event Points", null=True, blank=True)
    airtime = models.PositiveIntegerField("Airtime Value", null=True, blank=True)
    event_badge = models.ForeignKey("gamification.GamificationScenario",
                                    related_name="event_badge", null=True, blank=True)
    type = models.PositiveIntegerField("Type of Event", choices=TYPE_CHOICES, default=1)
    end_processed = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_next_event_question_rel(self, participant):
        if self.is_active():
            event_answers = EventQuestionAnswer.objects.filter(event=self, participant=participant) \
                .aggregate(Count('question'))['question__count']

            all_event_questions = EventQuestionRel.objects.filter(event=self)

            total_event_questions = all_event_questions.aggregate(Count('question'))['question__count']
            if event_answers < total_event_questions:
                event_question_rel = EventQuestionRel.objects.filter(event=self, order=event_answers+1).first()
                return event_question_rel

        return None

    def get_next_event_question(self, participant):
        event_question_rel = self.get_next_event_question_rel(participant)
        if event_question_rel:
            return event_question_rel.question
        else:
            return None

    def get_next_event_question_order(self, participant):
        event_question_rel = self.get_next_event_question_rel(participant)
        if event_question_rel:
            return event_question_rel.order
        else:
            return None

    def is_active(self):
        return self.activation_date < datetime.now() < self.deactivation_date


class EventStartPage(models.Model):
    event = models.ForeignKey(Event, null=True, blank=False)
    header = models.CharField("Header Text", max_length=50)
    paragraph = models.TextField("Paragraph Text", max_length=500)


class EventEndPage(models.Model):
    event = models.ForeignKey(Event, null=True, blank=False)
    header = models.CharField("Header Text", max_length=50)
    paragraph = models.TextField("Paragraph Text", max_length=500)


class EventSplashPage(models.Model):
    event = models.ForeignKey(Event, null=True, blank=False)
    order_number = models.PositiveIntegerField("Order", null=True, blank=False)
    header = models.CharField("Header Text", max_length=50)
    paragraph = models.TextField("Paragraph Text", max_length=500)


class EventQuestionRel(models.Model):
    order = models.PositiveIntegerField("Order", null=True, blank=False)
    event = models.ForeignKey(Event, null=True, blank=False)
    question = models.ForeignKey(TestingQuestion, limit_choices_to=dict(module__type=2, state=3), null=True,
                                 blank=False)


class EventQuestionAnswer(models.Model):
    event = models.ForeignKey(Event, null=True, blank=False)
    participant = models.ForeignKey("core.Participant", null=True, blank=False)
    question = models.ForeignKey(TestingQuestion, null=True, blank=False)
    question_option = models.ForeignKey(TestingQuestionOption, null=True, blank=False)
    correct = models.BooleanField()
    answer_date = models.DateTimeField("Answer Date", null=True, blank=False, auto_now_add=True)


class EventParticipantRel(models.Model):
    event = models.ForeignKey(Event, null=True, blank=False)
    participant = models.ForeignKey("core.Participant", null=True, blank=False)
    sitting_number = models.PositiveIntegerField(null=True, blank=False)
    results_received = models.BooleanField(default=False)
