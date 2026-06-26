from rest_framework import serializers
from .models import Stock, StockPrice


class StockPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPrice
        fields = '__all__'


class StockSerializer(serializers.ModelSerializer):
    latest_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=None)
    latest_change_rate = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True, default=None)

    class Meta:
        model = Stock
        fields = '__all__'
