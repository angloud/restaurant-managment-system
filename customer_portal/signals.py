from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from restaurant.models import Customer

@receiver(post_save, sender=User)
def create_customer_for_user(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(
            user=instance,
            customer_name=instance.username,
            customer_info=''
        ) 