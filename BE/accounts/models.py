from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(
        unique=True
    )

    nickname = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    birth_date = models.DateField(
        null=True,
        blank=True
    )

    financial_type = models.CharField(
        max_length=50,
        blank=True
    )

    profile_image = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )

    bio = models.TextField(
        blank=True
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        help_text='거주 주소 (인근 은행 기반 추천에 사용)'
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )

    updated_at = models.DateTimeField(
        default=timezone.now,
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
