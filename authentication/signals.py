from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def Create_User_Account_Balance(sender, instance, created, **kwargs):
    if created:
        "hi"