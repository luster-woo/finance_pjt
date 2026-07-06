import json
from pathlib import Path

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from config.pagination import StandardPagination

from .models import Card, CardBenefit, CardReview
from .serializers import CardSerializer, CardBenefitSerializer, CardReviewSerializer


@api_view(['GET'])
def card_list(request):
    cards = Card.objects.all()
    paginator = StandardPagination()
    page = paginator.paginate_queryset(cards, request)
    serializer = CardSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def card_detail(request, card_id):
    card = get_object_or_404(Card, pk=card_id)
    serializer = CardSerializer(card)
    return Response(serializer.data)


@api_view(['GET'])
def card_benefits(request, card_id):
    benefits = CardBenefit.objects.filter(card_id=card_id)
    serializer = CardBenefitSerializer(benefits, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def import_cards(request):
    data_file = Path(__file__).resolve().parents[2] / 'data' / 'card_data.json'
    if not data_file.exists():
        return Response({'detail': 'card_data.json 파일을 찾을 수 없습니다.'}, status=404)

    try:
        with data_file.open('r', encoding='utf-8') as f:
            card_items = json.load(f)
    except Exception as exc:
        return Response({'detail': f'card_data.json 로드 실패: {str(exc)}'}, status=500)

    created = 0
    updated = 0
    benefits_created = 0

    for item in card_items:
        card, created_flag = Card.objects.update_or_create(
            card_name=item.get('card_name', ''),
            company=item.get('company', ''),
            defaults={
                'card_type': item.get('card_type', ''),
                'min_performance': item.get('min_performance'),
                'annual_fee': item.get('annual_fee'),
            }
        )
        if created_flag:
            created += 1
        else:
            updated += 1

        for benefit in item.get('benefits', []):
            benefit_obj, benefit_created_flag = CardBenefit.objects.get_or_create(
                card=card,
                benefit_category=benefit.get('category', ''),
                benefit_detail=benefit.get('detail', ''),
            )
            if benefit_created_flag:
                benefits_created += 1

    return Response({
        'created': created,
        'updated': updated,
        'benefits_created': benefits_created,
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def card_review_list_create(request, card_id):
    card = get_object_or_404(Card, pk=card_id)

    if request.method == 'GET':
        reviews = CardReview.objects.filter(card=card).select_related('user')
        serializer = CardReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)

    if CardReview.objects.filter(user=request.user, card=card).exists():
        return Response({'detail': '이미 리뷰를 작성했습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = CardReviewSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            serializer.save(user=request.user, card=card)
        except IntegrityError:
            return Response({'detail': '이미 리뷰를 작성했습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
