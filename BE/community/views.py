from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import F
from django.db.models.functions import Greatest

from config.pagination import StandardPagination
from .models import CommunityPost, Comment, PostLike, CommentLike
from .serializers import CommunityPostSerializer, CommentSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def post_list_create(request):
    if request.method == 'GET':
        posts = CommunityPost.objects.all().order_by('-created_at')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = CommunityPostSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    serializer = CommunityPostSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def post_detail(request, post_id):
    post = get_object_or_404(CommunityPost, pk=post_id)

    if request.method == 'GET':
        serializer = CommunityPostSerializer(post, context={'request': request})
        return Response(serializer.data)

    if not request.user.is_authenticated or post.user != request.user:
        return Response({'detail': '권한이 없습니다.'}, status=403)

    if request.method == 'PUT':
        serializer = CommunityPostSerializer(post, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    post.delete()
    return Response(status=204)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_like_toggle(request, post_id):
    post = get_object_or_404(CommunityPost, pk=post_id)
    like, created = PostLike.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        CommunityPost.objects.filter(pk=post.pk).update(likes_count=Greatest(F('likes_count') - 1, 0))
    else:
        CommunityPost.objects.filter(pk=post.pk).update(likes_count=F('likes_count') + 1)
    post.refresh_from_db(fields=['likes_count'])
    return Response({'is_liked': created, 'likes_count': post.likes_count})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def comment_list_create(request, post_id):
    post = get_object_or_404(CommunityPost, pk=post_id)
    if request.method == 'GET':
        # 최상위 댓글만 반환 (대댓글은 replies에 포함)
        comments = Comment.objects.filter(post=post, parent=None).prefetch_related('replies__user').select_related('user').order_by('created_at')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    if not request.user.is_authenticated:
        return Response({'detail': '로그인이 필요합니다.'}, status=401)
    serializer = CommentSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(user=request.user, post=post)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comment_like_toggle(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
    if not created:
        like.delete()
        Comment.objects.filter(pk=comment.pk).update(likes_count=Greatest(F('likes_count') - 1, 0))
    else:
        Comment.objects.filter(pk=comment.pk).update(likes_count=F('likes_count') + 1)
    comment.refresh_from_db(fields=['likes_count'])
    return Response({'is_liked': created, 'likes_count': comment.likes_count})


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def comment_update_delete(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.user != request.user:
        return Response({'detail': '권한이 없습니다.'}, status=403)

    if request.method == 'PUT':
        serializer = CommentSerializer(comment, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    comment.delete()
    return Response(status=204)
