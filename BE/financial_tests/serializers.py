from rest_framework import serializers

from .models import (
    FinancialTest,
    FinancialTestAnswer,
    AIProductRecommendation,
    AIStockRecommendation,
)


class FinancialTestSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = FinancialTest
        fields = '__all__'


class FinancialTestAnswerSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = FinancialTestAnswer
        fields = '__all__'


class AIProductRecommendationSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    bank_name = serializers.CharField(source='product.bank_name', read_only=True)
    product_type = serializers.CharField(source='product.product_type', read_only=True)
    description = serializers.CharField(source='product.description', read_only=True)
    join_way = serializers.CharField(source='product.join_way', read_only=True)
    target_user = serializers.CharField(source='product.target_user', read_only=True)

    class Meta:
        model = AIProductRecommendation
        fields = (
            'id',
            'product_id',
            'product_name',
            'bank_name',
            'product_type',
            'description',
            'join_way',
            'target_user',
            'score',
            'reason',
            'created_at',
        )


class AIStockRecommendationSerializer(serializers.ModelSerializer):
    stock_id = serializers.IntegerField(source='stock.id', read_only=True)
    stock_code = serializers.CharField(source='stock.stock_code', read_only=True)
    stock_name = serializers.CharField(source='stock.stock_name', read_only=True)

    class Meta:
        model = AIStockRecommendation
        fields = (
            'id',
            'stock_id',
            'stock_code',
            'stock_name',
            'score',
            'reason',
            'created_at',
        )
