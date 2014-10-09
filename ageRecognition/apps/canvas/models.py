from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_facebook.models import FacebookModel, get_user_model, FacebookProfileModel
from django_facebook.utils import get_profile_model
import logging
logger = logging.getLogger(__name__)


try:
    # There can only be one custom user model defined at the same time
    if getattr(settings, 'AUTH_USER_MODEL', None) == 'member.CustomFacebookUser':
        from django.contrib.auth.models import AbstractUser, UserManager

        class CustomFacebookUser(AbstractUser, FacebookModel):
            """
            The django 1.5 approach to adding the facebook related fields
            """
            objects = UserManager()
            # add any customizations you like
            state = models.CharField(max_length=255, blank=True, null=True)
except ImportError as e:
    logger.info('Couldnt setup FacebookUser, got error %s', e)
    pass


# Create your models here.
class UserProfile(models.Model):
    """
    Inherit the properties from django facebook
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True)

    # Statistics, Scores and Achievements
    upload_pic = models.IntegerField(default=0)
    eval_pic = models.IntegerField(default=0)
    score_day = models.IntegerField(default=0)
    score_global = models.IntegerField(default=0)
    ach_precision = models.IntegerField(default=0)
    hometown = models.CharField(max_length=128)
    terms_conditions = models.BooleanField(default=False)


@receiver(post_save)
def create_profile(sender, instance, created, **kwargs):
    """Create a matching profile whenever a user object is created."""
    if sender == get_user_model():
        user = instance
        # profile_model = get_profile_model()
        if not hasattr(user, 'userprofile') and created:
            profile, new = UserProfile.objects.get_or_create(user=instance)


class Picture(models.Model):
    owner = models.ForeignKey(to=UserProfile)
    pic = models.ImageField(upload_to='images/uploaded_images')  # Upload Images to a folder named by user_id
    hash = models.CharField(max_length=128)
    real_age = models.IntegerField(null=True, blank=True)
    ground_truth = models.IntegerField(default=0)
    date = models.DateField()
    visibility = models.BooleanField(default=True)

    def __unicode__(self):
        return self.pic.name

    def num_votes(self):
        return Votes.objects.filter(pic=self).count()

class Votes(models.Model):
    user = models.ForeignKey(to=UserProfile)
    pic = models.ForeignKey(to=Picture)
    vote = models.IntegerField()
    score = models.IntegerField()
    date = models.DateField()

    def __unicode__(self):
        return 'User: ' + str(self.user.user_id) + ' Picture: ' + str(self.pic.name) + 'Vote: ' + str(self.vote)


class Report(models.Model):
    REPORT_CHOICES = [(0, 'Doesn\'t appear any face'),
                      (1, 'There are more than one face'),
                      (2, 'Unethical'),
                      (3, 'Other')]

    user = models.ForeignKey(to=UserProfile)
    pic = models.ForeignKey(to=Picture)
    date = models.DateField()
    options = models.BooleanField(choices=REPORT_CHOICES)
    other = models.TextField(max_length=500, blank=True, null=True)