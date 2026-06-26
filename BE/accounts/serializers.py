from rest_framework import serializers
from .models import User


class SignupSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True
    )

    class Meta:
        model = User
        fields = (
            'username',
            'nickname',
            'email',
            'password',
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            nickname=validated_data.get('nickname'),
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class ProfileSerializer(serializers.ModelSerializer):

    def validate_email(self, value):
        qs = User.objects.exclude(pk=self.instance.pk if self.instance else None).filter(email=value)
        if qs.exists():
            raise serializers.ValidationError('이미 사용 중인 이메일입니다.')
        return value

    def validate_profile_image(self, image):
        if image and image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('프로필 이미지는 5MB 이하만 업로드할 수 있습니다.')
        return image

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'nickname',
            'email',
            'birth_date',
            'financial_type',
            'profile_image',
            'bio',
            'address',
            'date_joined',
            'last_login',
        )
        read_only_fields = (
            'id',
            'username',
            'date_joined',
            'last_login',
        )
