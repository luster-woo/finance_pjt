from rest_framework import serializers
from .models import FinancialProduct, FinancialProductOption


class FinancialProductOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialProductOption
        fields = '__all__'


class FinancialProductSerializer(serializers.ModelSerializer):
    options = FinancialProductOptionSerializer(
        many=True,
        read_only=True,
        source='financialproductoption_set'
    )

    class Meta:
        model = FinancialProduct
        fields = '__all__'