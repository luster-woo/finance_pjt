from django.db import models
from django.conf import settings


class Stock(models.Model):
    stock_code = models.CharField(max_length=50, unique=True)
    stock_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class StockPrice(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    change_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    recorded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('stock', 'recorded_at')


class StockFavorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'stock')
