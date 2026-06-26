from django.db import models
from django.conf import settings
from products.models import FinancialProduct


class Favorite(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        FinancialProduct,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            'user',
            'product'
        )


class SubscribedProduct(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        FinancialProduct,
        on_delete=models.CASCADE
    )

    subscribed_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            'user',
            'product'
        )


class RecentProduct(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        FinancialProduct,
        on_delete=models.CASCADE
    )

    viewed_at = models.DateTimeField()

    class Meta:
        unique_together = (
            'user',
            'product'
        )
