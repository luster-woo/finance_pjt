from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from products.models import FinancialProduct
from stocks.models import Stock, StockPrice
from cards.models import Card

from .models import (
    AIProductRecommendation,
    AIStockRecommendation,
    FinancialTest,
    FinancialTestAnswer,
)
from .serializers import (
    AIProductRecommendationSerializer,
    AIStockRecommendationSerializer,
)
from .services.recommendation_service import (
    recommend_products_with_ai,
    recommend_stocks_with_ai,
    generate_test_description_with_gms,
    recommend_products_by_criteria_with_gms,
    _get_nearby_bank_names,
    _address_bank_bonus,
)


EXPECTED_ANSWER_COUNT = 10

# 역방향 문항 인덱스 (0-based)
# q2(1) : 원금 보장 선호 → 높을수록 보수적
# q6(5) : 충동 투자 경험 → 높을수록 충동적
# q9(8) : FOMO 충동 매수 → 높을수록 충동적
REVERSE_INDICES = {1, 5, 8}


def _normalize_answers(answers):
    return [
        6 - float(a) if i in REVERSE_INDICES else float(a)
        for i, a in enumerate(answers)
    ]


def _calculate_axes(answers):
    """
    10개 답변(1~5)에서 4가지 성향 축 점수(0~100)를 계산합니다.

    answers 인덱스 (0-based):
      0: Q1  위험수용도         → 정방향 (높을수록 공격적)
      1: Q2  원금보장 선호      → 역방향 (높을수록 안전 선호)
      2: Q3  장기투자 선호      → 정방향 (높을수록 장기)
      3: Q4  정보 분석          → 정방향 (높을수록 능동)
      4: Q5  하락장 대응        → 정방향 (높을수록 이성)
      5: Q6  충동투자 경험      → 역방향 (높을수록 감정)
      6: Q7  분산투자           → 정방향 (높을수록 능동·이성)
      7: Q8  금융 이해도        → 정방향 (높을수록 능동)
      8: Q9  FOMO 충동 매수     → 역방향 (높을수록 감정)
      9: Q10 높은 수익 목표     → 정방향 (높을수록 공격적)

    4축:
      risk     : 안전(0) ↔ 공격(100)   — Q1(+) Q2(-) Q10(+)
      rational : 감정(0) ↔ 이성(100)   — Q5(+) Q6(-) Q9(-)
      longterm : 단기(0) ↔ 장기(100)   — Q3(+)
      active   : 수동(0) ↔ 능동(100)   — Q4(+) Q7(+) Q8(+)
    """
    if len(answers) < 10:
        return {}

    def f(v, rev=False):
        v = max(1, min(5, int(v)))
        return ((5 - v) if rev else (v - 1)) / 4

    risk     = round((f(answers[0]) + f(answers[1], 1 in REVERSE_INDICES) + f(answers[9]))   / 3 * 100)
    rational = round((f(answers[4]) + f(answers[5], 5 in REVERSE_INDICES) + f(answers[8], 8 in REVERSE_INDICES)) / 3 * 100)
    longterm = round(f(answers[2]) * 100)
    active   = round((f(answers[3]) + f(answers[6]) + f(answers[7]))         / 3 * 100)

    def code(val, hi, lo):
        return hi if val >= 50 else lo

    axis_code = (
        code(risk, 'A', 'S') +
        code(rational, 'R', 'E') +
        code(longterm, 'L', 'T') +
        code(active, 'N', 'P')
    )

    return {
        'risk': risk,
        'rational': rational,
        'longterm': longterm,
        'active': active,
        'code': axis_code,
    }


TYPE_DESCRIPTIONS = {
    '안정형 투자자': '원금 보존을 중요하게 여기며, 예적금 중심의 안정적인 자산 관리를 선호합니다.',
    '안정추구형 투자자': '안정성을 우선하되 제한적인 범위에서 수익 기회를 함께 고려합니다.',
    '위험중립형 투자자': '안정성과 수익성의 균형을 추구하며, 상품 조건을 비교해 합리적으로 선택합니다.',
    '적극투자형 투자자': '일정 수준의 변동성을 감수하고 더 높은 수익 가능성을 탐색합니다.',
    '공격투자형 투자자': '높은 수익을 위해 적극적인 투자 선택도 고려하는 성향입니다.',
}


def _get_result_type(score):
    if score <= 30:
        return '안정형 투자자'
    if score <= 45:
        return '안정추구형 투자자'
    if score <= 60:
        return '위험중립형 투자자'
    if score <= 75:
        return '적극투자형 투자자'
    return '공격투자형 투자자'


def _validate_answers(answers):
    if answers is None:
        return 'answers 필드는 필수입니다.'
    if not isinstance(answers, list):
        return 'answers는 리스트여야 합니다.'
    if len(answers) != EXPECTED_ANSWER_COUNT:
        return f'answers는 {EXPECTED_ANSWER_COUNT}개여야 합니다.'
    if not all(isinstance(answer, (int, float)) for answer in answers):
        return 'answers의 모든 값은 숫자여야 합니다.'
    if not all(1 <= float(answer) <= 5 for answer in answers):
        return 'answers의 모든 값은 1부터 5 사이여야 합니다.'
    return None


def _latest_test(user):
    return FinancialTest.objects.filter(user=user).order_by('-created_at').first()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_test(request):
    answers = request.data.get('answers')
    error = _validate_answers(answers)
    if error:
        return Response({'detail': error}, status=400)

    normalized = _normalize_answers(answers)
    score = round((sum(normalized) / (EXPECTED_ANSWER_COUNT * 5)) * 100)
    result_type = _get_result_type(score)

    with transaction.atomic():
        test = FinancialTest.objects.create(
            user=request.user,
            score=score,
            result_type=result_type,
        )
        FinancialTestAnswer.objects.bulk_create([
            FinancialTestAnswer(
                test=test,
                question_no=index + 1,
                answer_value=int(answer),
            )
            for index, answer in enumerate(answers)
        ])
        request.user.financial_type = result_type
        request.user.save(update_fields=['financial_type', 'updated_at'])

    # GMS로 개인화 설명 생성 (실패 시 기본 설명 사용)
    gms_description = generate_test_description_with_gms(result_type, score, answers)
    description = gms_description or TYPE_DESCRIPTIONS.get(result_type, '')

    axes = _calculate_axes(answers)
    return Response({
        'id': test.id,
        'score': test.score,
        'result_type': test.result_type,
        'type_name': test.result_type,
        'description': description,
        'ai_generated': bool(gms_description),
        'created_at': test.created_at,
        'axes': axes,
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_result(request):
    test = _latest_test(request.user)
    if not test:
        return Response({'detail': '테스트 결과가 없습니다.'}, status=404)

    raw_answers = list(
        FinancialTestAnswer.objects.filter(test=test)
        .order_by('question_no')
        .values_list('answer_value', flat=True)
    )
    axes = _calculate_axes(raw_answers)
    return Response({
        'id': test.id,
        'score': test.score,
        'result_type': test.result_type,
        'type_name': test.result_type,
        'description': TYPE_DESCRIPTIONS.get(test.result_type, ''),
        'created_at': test.created_at,
        'axes': axes,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_products_by_criteria(request):
    """기간 + 목돈 입력 시 GMS가 점수 기반으로 금융상품 추천."""
    try:
        amount = int(float(request.data.get('amount', 0)))
        months = int(request.data.get('months', 0))
    except (TypeError, ValueError):
        return Response({'detail': 'amount와 months는 숫자여야 합니다.'}, status=400)

    if amount <= 0:
        return Response({'detail': '금액은 0원 초과여야 합니다.'}, status=400)
    if months not in [1, 3, 6, 12, 24, 36]:
        return Response({'detail': 'months는 1, 3, 6, 12, 24, 36 중 하나여야 합니다.'}, status=400)

    products = list(
        FinancialProduct.objects
        .prefetch_related('financialproductoption_set')
        .all()
    )

    recommendations = recommend_products_by_criteria_with_gms(amount, months, products)[:5]

    # 점수 기준 계산용 (근거 표시)
    all_for_period = []
    for p in products:
        opts = [o for o in p.financialproductoption_set.all() if o.save_trm == months]
        if not opts:
            continue
        br = max((o.max_interest_rate or o.interest_rate or 0 for o in opts), default=0)
        all_for_period.append({'id': p.id, 'best_rate': float(br),
                                'interest': round(amount * float(br) / 100 * months / 12)})

    max_rate = max((x['best_rate'] for x in all_for_period), default=1) or 1
    max_interest = max((x['interest'] for x in all_for_period), default=1) or 1
    major_banks = {'KB국민', '신한', '우리', '하나', 'NH농협', 'IBK기업', '카카오뱅크', '토스뱅크'}

    product_map = {p.id: p for p in products}
    result = []
    for item in recommendations:
        product = product_map.get(item.get('product_id'))
        if not product:
            continue
        options = [o for o in product.financialproductoption_set.all() if o.save_trm == months]
        best_rate = max((o.max_interest_rate or o.interest_rate or 0 for o in options), default=0)
        interest = round(amount * float(best_rate) / 100 * months / 12)

        # 채점 근거 계산
        rate_score = round((float(best_rate) / float(max_rate)) * 40, 1)
        profit_score = round((interest / float(max_interest)) * 30, 1)
        type_pref = 'deposit' if months <= 6 else 'saving'
        type_score = 15.0 if product.product_type == type_pref else 5.0
        bank_score = 15.0 if any(k in product.bank_name for k in major_banks) else 8.0

        result.append({
            'product_id': product.id,
            'product_name': product.product_name,
            'bank_name': product.bank_name,
            'product_type': product.product_type,
            'best_rate': float(best_rate),
            'interest': interest,
            'maturity_amount': amount + interest,
            'score': item.get('score', 0),
            'reason': item.get('reason', ''),
            'score_breakdown': {
                'rate_score': rate_score,
                'profit_score': profit_score,
                'type_score': type_score,
                'bank_score': bank_score,
                'rate_rank_pct': round(float(best_rate) / max_rate * 100),
            },
        })

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_cards_by_habits(request):
    """소비 습관 카테고리 선택 → GMS가 카드 추천."""
    from cards.models import Card, CardBenefit
    from financial_tests.services.recommendation_service import (
        recommend_cards_by_habits_with_gms,
    )

    habits = request.data.get('habits', [])  # e.g. ['식비', '교통', '온라인쇼핑']
    if not habits or not isinstance(habits, list):
        return Response({'detail': '소비 습관 카테고리를 하나 이상 선택해주세요.'}, status=400)

    cards = list(Card.objects.prefetch_related('cardbenefit_set').all())
    if not cards:
        return Response([])

    recommendations = recommend_cards_by_habits_with_gms(habits, cards)[:5]
    card_map = {c.id: c for c in cards}

    result = []
    for item in recommendations:
        card = card_map.get(item.get('card_id'))
        if not card:
            continue
        benefits = list(card.cardbenefit_set.all())
        matched = [b for b in benefits if any(h in (b.benefit_category or '') or h in (b.benefit_detail or '') for h in habits)]
        result.append({
            'card_id': card.id,
            'card_name': card.card_name,
            'company': card.company,
            'card_type': card.card_type,
            'annual_fee': card.annual_fee,
            'min_performance': card.min_performance,
            'score': item.get('score', 0),
            'reason': item.get('reason', ''),
            'matched_benefits': [
                {'category': b.benefit_category, 'detail': b.benefit_detail}
                for b in (matched or benefits)[:3]
            ],
            'score_breakdown': item.get('score_breakdown', {}),
        })

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_stocks_page(request):
    """성향 기반 주식 추천 - 상세 근거 포함."""
    test = _latest_test(request.user)
    if not test:
        return Response({'detail': '먼저 금융성향 테스트를 진행해주세요.'}, status=404)

    stocks = list(Stock.objects.all()[:15])
    if not stocks:
        return Response([])

    recommendations = recommend_stocks_with_ai(test, stocks)[:5]
    stock_map = {s.id: s for s in stocks}

    result = []
    for item in recommendations:
        stock = stock_map.get(item.get('stock_id'))
        if not stock:
            continue
        latest_price = stock.stockprice_set.order_by('-recorded_at').first()
        result.append({
            'stock_id': stock.id,
            'stock_code': stock.stock_code,
            'stock_name': stock.stock_name,
            'description': stock.description,
            'score': item.get('score', 0),
            'reason': item.get('reason', ''),
            'latest_price': float(latest_price.price) if latest_price else None,
            'change_rate': float(latest_price.change_rate) if latest_price and latest_price.change_rate else None,
        })

    return Response({
        'test': {
            'result_type': test.result_type,
            'score': test.score,
        },
        'recommendations': result,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_products(request):
    test = _latest_test(request.user)
    if not test:
        return Response({'detail': '테스트 결과가 없습니다.'}, status=404)

    refresh = request.GET.get('refresh') == '1'

    # 캐시 (refresh 파라미터 없으면 DB 캐시 사용)
    if not refresh:
        cached = list(AIProductRecommendation.objects.filter(user=request.user, test=test).select_related('product').order_by('-score')[:3])
        if cached:
            serializer = AIProductRecommendationSerializer(cached, many=True)
            return Response(serializer.data)

    products = list(
        FinancialProduct.objects
        .prefetch_related('financialproductoption_set')
        .all()[:30]
    )
    if not products:
        return Response([])

    recommendations = recommend_products_with_ai(test, products)

    # 인근 은행 가산점 적용
    user_address = getattr(request.user, 'address', '') or ''
    if user_address:
        nearby = _get_nearby_bank_names(user_address)
        for item in recommendations:
            prod = next((p for p in products if p.id == item.get('product_id')), None)
            if prod and _address_bank_bonus(prod.bank_name, nearby):
                item['score'] = min(100, int(item.get('score', 0)) + 8)
                item['reason'] = '📍 내 주변 지점 있음 · ' + item.get('reason', '')
        recommendations.sort(key=lambda x: x['score'], reverse=True)

    top3 = recommendations[:3]
    product_map = {product.id: product for product in products}

    saved = []
    with transaction.atomic():
        AIProductRecommendation.objects.filter(user=request.user, test=test).delete()
        for item in top3:
            product = product_map.get(item.get('product_id'))
            if not product:
                continue
            recommendation = AIProductRecommendation.objects.create(
                user=request.user, test=test, product=product,
                score=item.get('score', 0), reason=item.get('reason', ''),
            )
            saved.append(recommendation)

    serializer = AIProductRecommendationSerializer(saved, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_stocks(request):
    test = _latest_test(request.user)
    if not test:
        return Response({'detail': '테스트 결과가 없습니다.'}, status=404)

    refresh = request.GET.get('refresh') == '1'
    if not refresh:
        cached = list(AIStockRecommendation.objects.filter(user=request.user, test=test).select_related('stock').order_by('-score')[:3])
        if cached:
            serializer = AIStockRecommendationSerializer(cached, many=True)
            return Response(serializer.data)

    stocks = list(Stock.objects.all()[:15])
    if not stocks:
        return Response([])

    recommendations = recommend_stocks_with_ai(test, stocks)[:3]
    stock_map = {stock.id: stock for stock in stocks}

    saved = []
    with transaction.atomic():
        # refresh 시 기존 추천을 모두 삭제 후 새로 저장 (누적 방지)
        AIStockRecommendation.objects.filter(user=request.user, test=test).delete()
        for item in recommendations:
            stock = stock_map.get(item.get('stock_id'))
            if not stock:
                continue
            recommendation = AIStockRecommendation.objects.create(
                user=request.user,
                test=test,
                stock=stock,
                score=item.get('score', 0),
                reason=item.get('reason', ''),
            )
            saved.append(recommendation)

    serializer = AIStockRecommendationSerializer(saved, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_cards(request):
    test = _latest_test(request.user)
    if not test:
        return Response({'detail': '테스트 결과가 없습니다.'}, status=404)

    cards = list(Card.objects.prefetch_related('cardbenefit_set').all()[:30])
    if not cards:
        return Response([])

    def sort_key(card):
        benefit_count = len(card.cardbenefit_set.all())
        annual_fee = card.annual_fee if card.annual_fee is not None else 10 ** 9
        performance = card.min_performance if card.min_performance is not None else 10 ** 9
        if test.score <= 50:
            return annual_fee, performance, -benefit_count, card.id
        return -benefit_count, annual_fee, performance, card.id

    recommended = sorted(cards, key=sort_key)[:3]
    result = []
    for index, card in enumerate(recommended):
        benefits = list(card.cardbenefit_set.all())
        main_benefit = benefits[0].benefit_category if benefits else None
        if main_benefit:
            reason = f'{main_benefit} 혜택을 중심으로 활용하기 좋은 카드입니다.'
        elif card.annual_fee is not None:
            reason = f'연회비 {card.annual_fee:,}원으로 부담과 혜택을 함께 비교해 볼 수 있습니다.'
        else:
            reason = f'{test.result_type} 성향에서 함께 비교해 볼 만한 카드입니다.'

        result.append({
            'id': card.id,
            'card_name': card.card_name,
            'company': card.company,
            'card_type': card.card_type,
            'score': max(70, 94 - index * 5),
            'reason': reason,
        })

    return Response(result)
