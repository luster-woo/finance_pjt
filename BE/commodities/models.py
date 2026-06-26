from django.db import models


class CommodityPrice(models.Model):
    commodity_type = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    recorded_at = models.DateTimeField(null=True, blank=True)
