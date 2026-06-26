from rest_framework import serializers
from .models import CommunityPost, Comment, PostLike, CommentLike
from stocks.models import Stock


class ReplySerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    def get_username(self, obj):
        user = getattr(obj, 'user', None)
        return getattr(user, 'nickname', None) or getattr(user, 'username', '익명')

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommentLike.objects.filter(user=request.user, comment=obj).exists()
        return False

    class Meta:
        model = Comment
        fields = ('id', 'content', 'user', 'username', 'post', 'parent',
                  'likes_count', 'is_liked', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'post', 'likes_count', 'created_at', 'updated_at')


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    def get_username(self, obj):
        user = getattr(obj, 'user', None)
        return getattr(user, 'nickname', None) or getattr(user, 'username', '익명')

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommentLike.objects.filter(user=request.user, comment=obj).exists()
        return False

    def get_replies(self, obj):
        if obj.parent is not None:
            return []
        qs = obj.replies.all().order_by('created_at')
        return ReplySerializer(qs, many=True, context=self.context).data

    class Meta:
        model = Comment
        fields = ('id', 'content', 'user', 'username', 'post', 'parent',
                  'likes_count', 'is_liked', 'replies', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'post', 'likes_count', 'created_at', 'updated_at')


class CommunityPostSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.SerializerMethodField()
    stock = serializers.PrimaryKeyRelatedField(read_only=True)
    stock_id = serializers.PrimaryKeyRelatedField(
        source='stock', queryset=Stock.objects.all(),
        write_only=True, required=False, allow_null=True,
    )
    is_liked = serializers.SerializerMethodField()

    def get_username(self, obj):
        user = getattr(obj, 'user', None)
        return getattr(user, 'nickname', None) or getattr(user, 'username', '익명')

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(user=request.user, post=obj).exists()
        return False

    class Meta:
        model = CommunityPost
        fields = ('id', 'category', 'title', 'content', 'user', 'username',
                  'stock', 'stock_id', 'likes_count', 'view_count',
                  'is_liked', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'likes_count', 'view_count', 'created_at', 'updated_at')
