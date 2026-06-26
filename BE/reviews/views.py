from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.db.models import Count, Q

from .models import Review, ReviewReaction
from .serializers import ReviewSerializer
from products.models import FinancialProduct
from cards.models import CardReview
from cards.serializers import CardReviewSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def review_list_create(request, product_id):
    product = get_object_or_404(FinancialProduct, pk=product_id)

    if request.method == 'GET':
        reviews = Review.objects.filter(product=product).select_related('user')
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)

    if Review.objects.filter(user=request.user, product=product).exists():
        return Response({'detail': '이미 리뷰를 작성했습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        try:
            serializer.save(user=request.user, product=product)
        except IntegrityError:
            return Response({'detail': '이미 리뷰를 작성했습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_update_delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if review.user != request.user:
        return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    review.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_react(request, review_id):
    """리뷰에 도움돼요/아쉬워요 반응 토글."""
    review = get_object_or_404(Review, pk=review_id)
    reaction_type = request.data.get('reaction_type')
    if reaction_type not in ('like', 'sad'):
        return Response({'detail': 'reaction_type은 like 또는 sad여야 합니다.'}, status=400)

    existing = ReviewReaction.objects.filter(user=request.user, review=review).first()
    if existing:
        if existing.reaction_type == reaction_type:
            existing.delete()
            action = 'removed'
            my_reaction_type = None
        else:
            existing.reaction_type = reaction_type
            existing.save()
            action = 'changed'
            my_reaction_type = reaction_type
    else:
        ReviewReaction.objects.create(user=request.user, review=review, reaction_type=reaction_type)
        action = 'added'
        my_reaction_type = reaction_type

    # 단일 쿼리로 like/sad 카운트 동시 집계
    counts = ReviewReaction.objects.filter(review=review).aggregate(
        like_count=Count('id', filter=Q(reaction_type='like')),
        sad_count=Count('id', filter=Q(reaction_type='sad')),
    )
    return Response({
        'action': action,
        'like_count': counts['like_count'],
        'sad_count': counts['sad_count'],
        'my_reaction': my_reaction_type,
    })


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def card_review_update_delete(request, review_id):
    review = get_object_or_404(CardReview, pk=review_id)
    if review.user != request.user:
        return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = CardReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    review.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
