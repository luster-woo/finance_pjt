from rest_framework import serializers
from .models import CommodityPrice


class CommodityPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommodityPrice
        fields = '__all__'
