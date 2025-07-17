from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """Extended User model for SkinScan"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    # Additional fields
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def analysis_count(self):
        return self.skinanalysis_set.count()
    @property
    def conversation_count(self):  # Add this property
        """Return number of chatbot conversations"""
        try:
            return self.conversations.count()
        except:
            return 0

    @property
    def total_messages_sent(self):  # Add this property
        """Return total messages sent by user in chatbot"""
        try:
            from skinscan_chatbot.models import Message
            return Message.objects.filter(
                conversation__user=self,
                message_type='user'
            ).count()
        except:
            return 0

class UserProfile(models.Model):
    """Extended profile information for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    # Skin-related preferences
    skin_type = models.CharField(
        max_length=50,
        choices=[
            ('normal', 'Normal'),
            ('dry', 'Dry'),
            ('oily', 'Oily'),
            ('combination', 'Combination'),
            ('sensitive', 'Sensitive'),
        ],
        blank=True
    )
    medical_conditions = models.TextField(
        blank=True,
        help_text="Optional medical conditions (for reference only)"
    )

    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('private', 'Private'),
        ],
        default='private'
    )

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    analysis_reminders = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} Profile"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'