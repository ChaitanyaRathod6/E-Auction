from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Buyer, Seller, AdminProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.Role == "Buyer":
            Buyer.objects.create(user=instance)

        elif instance.Role == "Seller":
            Seller.objects.create(user=instance)

        elif instance.Role == "Admin":
            AdminProfile.objects.create(user=instance)