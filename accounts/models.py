from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    ]

    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20, blank=True)
    facebook_url = models.CharField(
        max_length=255, blank=True,
        help_text="Facebook profile URL, used as a backup contact method."
    )
    address = models.CharField(max_length=255, blank=True)
    valid_id = models.ImageField(
        upload_to='user_ids/', blank=True, null=True,
        help_text="Photo of a government-issued ID, used to verify identity for rentals."
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    failed_attempts = models.PositiveIntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    @property
    def is_admin_role(self):
        return self.role == 'admin' or self.is_superuser

    def __str__(self):
        return self.email