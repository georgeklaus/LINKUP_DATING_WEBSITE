from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile, CustomUser

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        # Add registration bonus
        if instance.gender == 'F':
            instance.add_coins(settings.FEMALE_REGISTRATION_BONUS)
        else:
            instance.add_coins(settings.MALE_REGISTRATION_BONUS)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()