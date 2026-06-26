from rest_framework import serializers
from .models import Card, CardBenefit, CardReview


class CardBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardBenefit
        fields = '__all__'


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'


class CardReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    card = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    def get_username(self, obj):
        return getattr(obj.user, 'nickname', None) or obj.user.username

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

    class Meta:
        model = CardReview
        fields = (
            'id', 'rating', 'content',
            'user', 'username', 'is_mine',
            'card', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'user', 'card', 'created_at', 'updated_at')
