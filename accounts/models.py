from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    ]

    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20, blank=True)
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