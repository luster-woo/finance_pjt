from rest_framework import serializers
from .models import Review, ReviewReaction


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    product = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    sad_count = serializers.SerializerMethodField()
    my_reaction = serializers.SerializerMethodField()

    def get_username(self, obj):
        return getattr(obj.user, 'nickname', None) or getattr(obj.user, 'username', '익명')

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

    def get_like_count(self, obj):
        return obj.reactions.filter(reaction_type='like').count()

    def get_sad_count(self, obj):
        return obj.reactions.filter(reaction_type='sad').count()

    def get_my_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            r = obj.reactions.filter(user=request.user).first()
            return r.reaction_type if r else None
        return None

    class Meta:
        model = Review
        fields = (
            'id', 'rating', 'content',
            'user', 'username', 'is_mine',
            'like_count', 'sad_count', 'my_reaction',
            'product', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'user', 'product', 'created_at', 'updated_at')