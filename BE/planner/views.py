import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from products.models import FinancialProduct, FinancialProductOption


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def plan_savings(request):
    """목표 저축 플래너
    - goal_amount: 목표 금액 (원)
    - monthly_savings: 월 저축 가능 금액 (원)
    - months: 목표 기간 (개월)
    """
    try:
        goal_amount = int(request.data.get('goal_amount', 0))
        monthly_savings = int(request.data.get('monthly_savings', 0))
        months = int(request.data.get('months', 12))
    except (TypeError, ValueError):
        return Response({'detail': '올바른 숫자를 입력해주세요.'}, status=400)

    if goal_amount <= 0 or monthly_savings <= 0 or months <= 0:
        return Response({'detail': '금액과 기간은 0보다 커야 합니다.'}, status=400)

    # ── 1. 해당 기간 상품 검색 ────────────────────────────────────
    available_terms = [1, 3, 6, 12, 24, 36]
    best_term = min(available_terms, key=lambda t: abs(t - months))

    products_qs = FinancialProduct.objects.prefetch_related('financialproductoption_set').all()
    candidates = []
    for p in products_qs:
        opts = [o for o in p.financialproductoption_set.all() if o.save_trm == best_term]
        if not opts:
            continue
        best_rate = float(max((o.max_interest_rate or o.interest_rate or 0 for o in opts), default=0))
        if best_rate <= 0:
            continue
        candidates.append({'product': p, 'rate': best_rate, 'term': best_term})

    candidates.sort(key=lambda x: x['rate'], reverse=True)

    # ── 2. 플랜 계산 ──────────────────────────────────────────────
    # 단순 이자 계산 (적금: 월납입 × (1 + r/12×(n+1)/2), 예금: 원금×(1 + r/12×n))
    def calc_maturity_saving(monthly, rate_pct, n):
        r = rate_pct / 100
        return round(monthly * n * (1 + r * (n + 1) / 24))

    def calc_maturity_deposit(principal, rate_pct, n):
        r = rate_pct / 100
        return round(principal * (1 + r * n / 12))

    # 추천 전략: 상위 3개 상품 기준
    top_products = candidates[:3]
    best_rate = top_products[0]['rate'] if top_products else 3.0

    # 적금으로 월납입 시 만기 수령액
    maturity_saving = calc_maturity_saving(monthly_savings, best_rate, months)
    total_principal = monthly_savings * months
    total_interest = maturity_saving - total_principal

    # 달성 여부
    achievable = maturity_saving >= goal_amount

    # 부족 시 필요 월납입액 계산
    required_monthly = None
    if not achievable and best_rate > 0:
        # 역산: monthly = goal / (n * (1 + r*(n+1)/24))
        r = best_rate / 100
        denom = months * (1 + r * (months + 1) / 24)
        required_monthly = round(goal_amount / denom) if denom > 0 else None

    # 달성까지 몇 개월 걸리는지 (현재 월 저축액 기준)
    months_needed = None
    if not achievable:
        for m in range(months + 1, months * 5):
            if calc_maturity_saving(monthly_savings, best_rate, m) >= goal_amount:
                months_needed = m
                break

    # ── 3. 월별 누적 데이터 (그래프용) ────────────────────────────
    monthly_data = []
    for m in range(1, months + 1):
        principal_so_far = monthly_savings * m
        interest_so_far = round(monthly_savings * m * (best_rate / 100) * m / 24)
        monthly_data.append({
            'month': m,
            'principal': principal_so_far,
            'total': principal_so_far + interest_so_far,
        })

    # ── 4. 추천 상품 포맷 ────────────────────────────────────────
    recommended = []
    for c in top_products:
        p = c['product']
        maturity = calc_maturity_saving(monthly_savings, c['rate'], months)
        recommended.append({
            'product_id': p.id,
            'product_name': p.product_name,
            'bank_name': p.bank_name,
            'product_type': p.product_type,
            'rate': c['rate'],
            'term': c['term'],
            'maturity_amount': maturity,
            'estimated_interest': maturity - total_principal,
        })

    return Response({
        'goal_amount': goal_amount,
        'monthly_savings': monthly_savings,
        'months': months,
        'best_rate': best_rate,
        'total_principal': total_principal,
        'total_interest': total_interest,
        'maturity_amount': maturity_saving,
        'achievable': achievable,
        'shortfall': max(0, goal_amount - maturity_saving),
        'required_monthly': required_monthly,
        'months_needed': months_needed,
        'monthly_data': monthly_data,
        'recommended_products': recommended,
    })
