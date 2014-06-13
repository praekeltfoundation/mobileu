from datetime import datetime

from django.db import models
from django.db.models import Sum

from mobileu.organisation.models import Course
from mobileu.auth.models import Learner
from mobileu.gamification.models import (
    GamificationPointBonus, GamificationBadgeTemplate, GamificationScenario)
from mobileu.content.models import TestingQuestion, TestingQuestionOption


class Class(models.Model):
    """
    Classes link Users (learners, mentors, etc) and Courses. A user has to
    be in a class to participate in a modules.
    """
    name = models.CharField(
        "Name", max_length=50, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=50, blank=True)
    course = models.ForeignKey(Course, null=True, blank=False)
    type = models.PositiveIntegerField("Type", choices=(
        (1, "Traditional"), (2, "Open Class ")), default=1)
    startdate = models.DateField("Start Date", null=True, blank=True)
    enddate = models.DateField("End Date", null=True, blank=True)
    #learners
    #mentors
    #managers

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"


class Participant(models.Model):
    """
    Connects a learner to a class. Indicating the learners total points
    earned as well as individual point and badges earned.
    """
    learner = models.ForeignKey(Learner, verbose_name="Learner")
    classs = models.ForeignKey(Class, verbose_name="Class")
    datejoined = models.DateField(verbose_name="Joined")
    points = models.PositiveIntegerField(verbose_name="Points Scored", default=0)
    pointbonus = models.ManyToManyField(
        GamificationPointBonus, through="ParticipantPointBonusRel",
        verbose_name="Point Bonuses", blank=True)
    badgetemplate = models.ManyToManyField(
        GamificationBadgeTemplate, through="ParticipantBadgeTemplateRel",
        verbose_name="Badge Templates", blank=True)

    def __str__(self):
        return self.learner.first_name

    def award_scenario(self, event, module):
        for scenario in GamificationScenario.objects.filter(
                event=event, course=self.classs.course, module=module):
            # Points may be awarded multiple times
            if scenario.point is not None:
                p = ParticipantPointBonusRel(
                    participant=self, pointbonus=scenario.point,
                    scenario=scenario)
                p.save()

            # Badges may only be awarded once
            if scenario.badge is not None:
                template_rels = ParticipantBadgeTemplateRel.objects.filter(
                    participant=self, badgetemplate=scenario.badge)
                if not template_rels.exists():
                    b = ParticipantBadgeTemplateRel(
                        participant=self, badgetemplate=scenario.badge,
                        scenario=scenario)
                    b.save()

        # Recalculate total points
        bonus_rel = ParticipantPointBonusRel.objects.filter(participant=self)
        self.points = max(
            bonus_rel.select_related("pointbonus").aggregate(
                sum=Sum("pointbonus__value"))["sum"], 0)
        self.save()

    class Meta:
        verbose_name = "Participant"
        verbose_name_plural = "Participants"


class ParticipantPointBonusRel(models.Model):
    participant = models.ForeignKey(Participant)
    pointbonus = models.ForeignKey(GamificationPointBonus)
    scenario = models.ForeignKey(GamificationScenario)
    awarddate = models.DateTimeField("Award Date", null=True, blank=True)


class ParticipantBadgeTemplateRel(models.Model):
    participant = models.ForeignKey(Participant)
    badgetemplate = models.ForeignKey(GamificationBadgeTemplate)
    scenario = models.ForeignKey(GamificationScenario)
    awarddate = models.DateTimeField(
        "Award Date", null=True, blank=False, default=datetime.now())


class ParticipantQuestionAnswer(models.Model):
    participant = models.ForeignKey(Participant, verbose_name="Participant")
    question = models.ForeignKey(TestingQuestion, verbose_name="Question")
    option_selected = models.ForeignKey(
        TestingQuestionOption, verbose_name="Selected")
    correct = models.BooleanField("Correct")
    answerdate = models.DateField(
        "Answer Date", null=True, blank=False, default=datetime.now())

    def __str__(self):
        return self.participant.learner.name

    class Meta:
        verbose_name = "Participant Question Response"
        verbose_name_plural = "Participant Question Responses"
