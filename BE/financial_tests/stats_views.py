"""
비슷한 사용자 통계 API
- 같은 성향 유저들의 인기 카드
- 비슷한 나이대 유저들의 인기 금융상품
- 같은 성향 유저들의 인기 주식
"""
from datetime import date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count


def _calc_age(birth_date):
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def similar_users_stats(request):
    from django.contrib.auth import get_user_model
    from cards.models import CardReview
    from favorites.models import SubscribedProduct
    from financial_tests.models import AIStockRecommendation

    User = get_user_model()
    me = request.user
    my_type = getattr(me, 'financial_type', '') or ''

    result = {}

    # ── 1. 같은 성향 인기 카드 ───────────────────────────────────
    if my_type:
        same_type_ids = list(
            User.objects.filter(financial_type=my_type)
            .exclude(pk=me.pk)
            .values_list('id', flat=True)[:500]
        )
        card_counts = (
            CardReview.objects.filter(user_id__in=same_type_ids)
            .values('card__id', 'card__card_name', 'card__company', 'card__card_type')
            .annotate(cnt=Count('id'))
            .order_by('-cnt')[:5]
        )
        total_card = sum(c['cnt'] for c in card_counts) or 1
        result['similar_type_cards'] = [
            {
                'card_id': c['card__id'],
                'card_name': c['card__card_name'],
                'company': c['card__company'],
                'card_type': c['card__card_type'],
                'count': c['cnt'],
                'pct': round(c['cnt'] / total_card * 100),
            }
            for c in card_counts
        ]
    else:
        result['similar_type_cards'] = []

    # ── 2. 비슷한 나이/금액대 인기 금융상품 ────────────────────────
    # 나이 ±5세, 급여 ±30% 범위 유저
    me_age = _calc_age(getattr(me, 'birth_date', None))

    age_qs = User.objects.exclude(pk=me.pk)
    if me_age:
        # birth_date 기반으로 ±5세 범위 필터 (같은 나이대)
        from datetime import timedelta
        today = date.today()
        birth_low  = date(today.year - me_age - 5, today.month, today.day)
        birth_high = date(today.year - me_age + 5, today.month, today.day)
        age_qs = age_qs.filter(birth_date__range=(birth_low, birth_high))

    similar_ids = list(age_qs.values_list('id', flat=True)[:500])
    if not similar_ids:
        # fallback: 같은 성향
        similar_ids = same_type_ids if my_type else []

    product_counts = (
        SubscribedProduct.objects.filter(user_id__in=similar_ids)
        .values('product__id', 'product__product_name', 'product__bank_name', 'product__product_type')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')[:5]
    )
    total_prod = sum(p['cnt'] for p in product_counts) or 1
    result['similar_age_products'] = [
        {
            'product_id': p['product__id'],
            'product_name': p['product__product_name'],
            'bank_name': p['product__bank_name'],
            'product_type': p['product__product_type'],
            'count': p['cnt'],
            'pct': round(p['cnt'] / total_prod * 100),
        }
        for p in product_counts
    ]

    # ── 3. 같은 성향 인기 주식 ──────────────────────────────────
    if my_type and same_type_ids:
        stock_counts = (
            AIStockRecommendation.objects.filter(user_id__in=same_type_ids)
            .values('stock__id', 'stock__stock_code', 'stock__stock_name')
            .annotate(cnt=Count('id'))
            .order_by('-cnt')[:5]
        )
        total_stock = sum(s['cnt'] for s in stock_counts) or 1
        result['similar_type_stocks'] = [
            {
                'stock_id': s['stock__id'],
                'stock_code': s['stock__stock_code'],
                'stock_name': s['stock__stock_name'],
                'count': s['cnt'],
                'pct': round(s['cnt'] / total_stock * 100),
            }
            for s in stock_counts
        ]
    else:
        result['similar_type_stocks'] = []

    result['my_type'] = my_type
    result['my_age'] = me_age
    result['my_birth_date'] = str(getattr(me, 'birth_date', '')) or None
    return Response(result)
