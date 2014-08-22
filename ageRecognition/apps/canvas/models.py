from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_facebook.models import FacebookModel, get_user_model
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
class UserProfile(FacebookModel):
    """
    Inherit the properties from django facebook
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    # Statistics, Scores and Achievements
    upload_pic = models.IntegerField(default=0)
    eval_pic = models.IntegerField(default=0)
    score_day = models.IntegerField(default=0)
    score_week = models.IntegerField(default=0)
    score_global = models.IntegerField(default=0)
    ach_friends = models.IntegerField(default=0)
    ach_precision = models.IntegerField(default=0)


@receiver(post_save)
def create_profile(sender, instance, created, **kwargs):
    """Create a matching profile whenever a user object is created."""
    if sender == get_user_model():
        user = instance
        profile_model = get_profile_model()
        if profile_model == UserProfile and created:
            profile, new = UserProfile.objects.get_or_create(user=instance)


class Picture(models.Model):
    id_pic = models.CharField(max_length=128, unique=True, primary_key=True)
    owner = models.ForeignKey(to=UserProfile)

    pic = models.ImageField(upload_to='pictures')
    ground_truth = models.IntegerField(default=0)

    def __unicode__(self):
        return self.id_pic


class Votes(models.Model):
    user = models.ForeignKey(to=UserProfile)
    pic = models.ForeignKey(to=Picture)
    vote = models.IntegerField()

    def __unicode__(self):
        return 'User: ' + str(self.user.user_id) + ' Picture: ' + str(self.pic.id_pic) + 'Vote: ' + str(self.vote)
