from django.db import models
from django.contrib.auth.models import AbstractUser
from organisation.models import School, Course
import uuid
from base64 import b64encode
from datetime import datetime, timedelta

# Base class for custom MobileU user model
class CustomUser(AbstractUser):
    mobile = models.CharField(verbose_name="Mobile Phone Number",
                              max_length=50, blank=False, unique=True)
    country = models.CharField(verbose_name="Country", max_length=50,
                               blank=False)
    area = models.CharField(verbose_name="Local Area", max_length=50,
                            blank=True)
    city = models.CharField(verbose_name="City", max_length=50, blank=True)
    optin_sms = models.BooleanField(verbose_name="Opt-In SMS Communications",
                                    default=False)
    optin_email = models.BooleanField(
        verbose_name="Opt-In Email Communications", default=False)

    unique_token = models.CharField(
        verbose_name="Unique Login Token",
        max_length=500,
        blank=True
    )

    unique_token_expiry = models.DateTimeField(
        verbose_name="Unique Login Token Expiry",
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        # TODO: Check uniqueness
        #Generate unique guid
        self.unique_token = b64encode(uuid.uuid1().bytes)
        self.unique_token_expiry = datetime.now() + timedelta(days=30)

        #Save object
        super(CustomUser, self).save(*args, **kwargs)

    def __str__(self):
        return self.username


# System administrator with access to the admin console
class SystemAdministrator(CustomUser):

    class Meta:
        verbose_name = "System Administrator"
        verbose_name_plural = "System Administrators"


# A manager of a school
class SchoolManager(CustomUser):
    school = models.ForeignKey(School, null=True, blank=False)

    class Meta:
        verbose_name = "School Manager"
        verbose_name_plural = "School Managers"


# A manager of a course
class CourseManager(CustomUser):
    course = models.ForeignKey(Course, null=True, blank=False)

    class Meta:
        verbose_name = "Course Manager"
        verbose_name_plural = "Course Managers"


# A mentor for a course
class CourseMentor(CustomUser):
    course = models.ForeignKey(Course, null=True, blank=False)

    class Meta:
        verbose_name = "Course Mentor"
        verbose_name_plural = "Course Mentors"


# A learner
class Learner(CustomUser):
    school = models.ForeignKey(School, null=True, blank=False)

    class Meta:
        verbose_name = "Learner"
        verbose_name_plural = "Learners"
