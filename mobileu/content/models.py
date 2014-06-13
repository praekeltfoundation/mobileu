from django.db import models
from django.core.validators import MaxValueValidator

from mobileu.organisation.models import Module


class LearningChapter(models.Model):
    """
    Each modules has learning content which can be broken up into chapters.
    Essentially this content is HTML and needs to
    be able to include images, videos, audio clips and hyperlinks to
    external resources. The management interface will
    only expose limited formatting options.
    """
    name = models.CharField(
        "Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    module = models.ForeignKey(Module, null=True, blank=False)
    content = models.TextField("Content", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Learning Chapter"
        verbose_name_plural = "Learning Chapters"


class TestingBank(models.Model):
    """
    Each modules has a series of questions. The MVP supports two question
    types, multiple-choice and free-form entry.
    """
    name = models.CharField(
        "Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    module = models.ForeignKey(Module, null=True, blank=False)
    question_order = models.PositiveIntegerField("Question Order", choices=(
        (1, "Random"), (2, "Ordered"), (3, "Random Intelligent")), default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Test Bank"
        verbose_name_plural = "Test Banks"


class TestingQuestion(models.Model):
    name = models.CharField(
        "Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    order = models.PositiveIntegerField("Order", default=1)
    bank = models.ForeignKey(TestingBank, null=True, blank=False)
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
        "Points", validators=[MaxValueValidator(50)], default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Test Question"
        verbose_name_plural = "Test Questions"


class TestingQuestionOption(models.Model):
    name = models.CharField(
        "Name", max_length=50, null=True, blank=False, unique=True)
    question = models.ForeignKey(TestingQuestion, null=True, blank=False)
    order = models.PositiveIntegerField("Order", default=1)
    content = models.TextField("Content", blank=True)
    correct = models.BooleanField("Correct")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Question Option"
        verbose_name_plural = "Question Options"
