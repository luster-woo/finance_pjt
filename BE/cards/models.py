from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator


class Card(models.Model):
    card_name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    card_type = models.CharField(max_length=255, blank=True)
    min_performance = models.IntegerField(null=True, blank=True)
    annual_fee = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('card_name', 'company')


class CardBenefit(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    benefit_category = models.CharField(max_length=255)
    benefit_detail = models.TextField(blank=True)

    class Meta:
        unique_together = ('card', 'benefit_category', 'benefit_detail')


class CardReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'card')
