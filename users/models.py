# agro_ecommerce/users/models.py
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings  # Import settings

# Function to define upload path (optional but good practice)


def profile_pic_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/profile_pics/user_<id>/<filename>
    return f'profile_pics/user_{instance.user.id}/{filename}'


class User(AbstractUser):
    username = models.TextField(max_length=50, unique=True)
    first_name = models.TextField(
        max_length=15, unique=False, null=True, blank=True)
    last_name = models.TextField(
        max_length=15, unique=False, null=True, blank=True)
    email = models.EmailField(unique=True)

    is_farmer = models.BooleanField(default=False)
    is_buyer = models.BooleanField(default=False)

    # Add custom related_name to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="custom_user_set",  # Custom related_name
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",  # Custom related_name
        related_query_name="user",
    )

    # Automatically set is_buyer to True if is_farmer is False during save
    # def save(self, *args, **kwargs):
    #     if not self.is_farmer:
    #         self.is_buyer = True
    #     super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')  # Added related_name
    phone_number = models.CharField(
        max_length=15, default='N/A', blank=True)
    address = models.TextField(blank=True, null=True)
    # --- Add profile picture field ---
    profile_picture = models.ImageField(
        upload_to=profile_pic_path,  # Use the function for path
        null=True,
        blank=True,
        default='profile_pics/default/default_avatar.png'  # Add a default avatar path
    )

    def __str__(self):
        return f"Profile for {self.user.username}"

    # Optional: Method to get picture URL easily
    @property
    def profile_picture_url(self):
        try:
            if self.profile_picture and hasattr(self.profile_picture, 'url'):
                return self.profile_picture.url
        except ValueError:  # Handle case where file might not exist but field has value
            pass  # Fall through to default
        # Return URL to default image if no picture or error accessing URL
        return f"{settings.MEDIA_URL}profile_pics/default/default_avatar.png"


# --- Signal to create profile automatically ---
# (Alternative to modifying UserSerializer.create)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Check if profile exists before trying to save
    # This might not be strictly necessary if create_user_profile always runs first
    # but adds robustness.
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # If profile doesn't exist for some reason (e.g., existing user before signal)
        Profile.objects.get_or_create(user=instance)
