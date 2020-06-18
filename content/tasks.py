from datetime import datetime
import operator

from djcelery import celery
from auth.models import Learner
from content.forms import render_mathml
from content.models import Event, EventParticipantRel, EventQuestionAnswer
from core.models import Participant, Setting
from communication.utils import VumiSmsApi
from organisation.models import CourseModuleRel
from django.db.models import Count


@celery.task
def render_mathml_content():
    render_mathml()


@celery.task
def end_event_processing():
    end_event_processing_body()


# function to assist with testing
def today():
    return datetime.now()


def end_event_processing_body():
    # Only get exams and spot tests
    events = Event.objects.filter(
        deactivation_date__lt=today(),
        end_processed=False,
        type__in=[Event.ET_EXAM, Event.ET_SPOT_TEST]
    )

    scenarios = {
        Event.ET_SPOT_TEST: "SPOT_TEST_CHAMP",
        Event.ET_EXAM: "EXAM_CHAMP"
    }

    for event in events:
        scores = EventQuestionAnswer.objects.filter(event=event, correct=True).values("participant") \
            .order_by("-score").annotate(score=Count("pk"))
        if scores:
            winner_ids = [scores[0]["participant"]]
            index = 0
            score_size = len(scores)
            if score_size > 1:
                while index + 1 < score_size and scores[index]["score"] == scores[index + 1]["score"]:
                    winner_ids.append(scores[index + 1]["participant"])
                    index += 1

            winners = Participant.objects.filter(id__in=winner_ids)
            module = CourseModuleRel.objects.filter(course=event.course).first()

            for winner in winners:
                winner.award_scenario(scenarios[event.type], module, special_rule=True)
                EventParticipantRel.objects.filter(event=event, participant__id__in=winner_ids).update(winner=True)

        event.end_processed = True
        event.save()


@celery.task
def sms_new_questions(questions, msg=None):
    sms_new_questions_body(questions, msg)


def sms_new_questions_body(questions, msg=None):
    participants = Participant.objects.none()

    for question in questions:
        new_participants = question.get_unanswered_participants()
        if new_participants is not None:
            participants = participants | new_participants

    learners = Learner.objects.filter(participant__in=participants)
    if learners is None or len(learners) == 0:
        return

    if msg is None:
        msg = Setting.get_setting('LEARNER_NEW_QUESTIONS_MSG',
                                  default='Hi, there. We have new questions for you on Dig-it!')

    vumi = VumiSmsApi()
    vumi.send_all(learners, message=msg)
