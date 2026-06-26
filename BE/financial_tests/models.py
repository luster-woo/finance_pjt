from django.db import models
from django.conf import settings

# Create your models here.
class FinancialTest(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    result_type = models.CharField(
        max_length=255
    )

    score = models.IntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

class FinancialTestAnswer(models.Model):

    test = models.ForeignKey(
        FinancialTest,
        on_delete=models.CASCADE
    )

    question_no = models.IntegerField()

    answer_value = models.IntegerField()


class AIProductRecommendation(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    test = models.ForeignKey(
        FinancialTest,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        'products.FinancialProduct',
        on_delete=models.CASCADE
    )

    score = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'test', 'product')


class AIStockRecommendation(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    test = models.ForeignKey(
        FinancialTest,
        on_delete=models.CASCADE
    )

    stock = models.ForeignKey(
        'stocks.Stock',
        on_delete=models.CASCADE
    )

    score = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'test', 'stock')
