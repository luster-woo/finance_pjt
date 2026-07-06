"""
금융상품 추천 폴백 알고리즘

GMS / Gemini API 장애 시 recommendation_service.py에서 호출하는
순수 수식 기반 스코어링 함수입니다. AI 호출 없이 동작합니다.
"""


def calculate_recommendation_score_algorithm(test_score, result_type, product, product_option, desired_amount=1000000):
    """
    현재: 알고리즘 기반 추천 점수 계산
    미래: AI API 호출로 대체 가능
    
    Args:
        test_score: 금융성향 점수
        result_type: 성향 타입
        product: FinancialProduct 인스턴스
        product_option: FinancialProductOption 인스턴스
        desired_amount: 예상 금액
    
    Returns:
        dict: {'score': 0-100, 'reason': str}
    """
    
    score = 0
    factors = []
    
    # 1. 성향과 상품 타입 매칭 (40점 만점)
    stability_score = 0
    if result_type in ('안정형', '안정추구형'):
        if product.product_type == 'deposit':
            stability_score = 40
            factors.append('성향에 완벽히 맞는 예금상품')
        elif product.product_type == 'saving':
            stability_score = 25
            factors.append('성향보다 위험한 적금상품')
    elif result_type == '위험중립형':
        if product.product_type == 'deposit':
            stability_score = 30
            factors.append('안정적인 예금상품')
        elif product.product_type == 'saving':
            stability_score = 35
            factors.append('균형잡힌 적금상품')
    else:  # 적극투자형, 공격투자형
        if product.product_type == 'saving':
            stability_score = 40
            factors.append('성향에 맞는 적금상품')
        elif product.product_type == 'deposit':
            stability_score = 25
            factors.append('성향보다 안정적인 예금상품')
    
    score += stability_score
    
    # 2. 기간 적합도 (25점 만점)
    # 일반적으로 6-12개월이 인기
    period = product_option.save_trm
    if 6 <= period <= 12:
        period_score = 25
        factors.append(f'{period}개월의 적당한 기간')
    elif 3 <= period < 6 or 12 < period <= 24:
        period_score = 18
        factors.append(f'{period}개월 기간 (다소 짧거나 김)')
    elif 24 < period <= 36:
        period_score = 12
        factors.append(f'{period}개월 장기 기간')
    else:
        period_score = 5
        factors.append(f'{period}개월 (비추천 기간)')
    
    score += period_score
    
    # 3. 이자율 경쟁력 (20점 만점)
    # 평균 이자율 기준: 예금 2.5%, 적금 3.5%
    interest = product_option.interest_rate or 0
    max_interest = product_option.max_interest_rate or interest
    
    if product.product_type == 'deposit':
        baseline = 2.5
    else:
        baseline = 3.5
    
    avg_interest = (interest + max_interest) / 2
    if avg_interest >= baseline + 1.0:
        interest_score = 20
        factors.append(f'높은 이자율 ({avg_interest:.2f}%)')
    elif avg_interest >= baseline + 0.5:
        interest_score = 15
        factors.append(f'우수한 이자율 ({avg_interest:.2f}%)')
    elif avg_interest >= baseline:
        interest_score = 10
        factors.append(f'평균 수준 이자율 ({avg_interest:.2f}%)')
    else:
        interest_score = 5
        factors.append(f'낮은 이자율 ({avg_interest:.2f}%)')
    
    score += interest_score
    
    # 4. 자금 규모 (15점 만점)
    # 100만원 이상이 무난
    if desired_amount >= 1000000:
        amount_score = 15
        factors.append(f'충분한 자금 규모 ({desired_amount:,}원)')
    elif desired_amount >= 500000:
        amount_score = 12
        factors.append(f'적절한 자금 규모 ({desired_amount:,}원)')
    elif desired_amount >= 100000:
        amount_score = 8
        factors.append(f'소액 자금 ({desired_amount:,}원)')
    else:
        amount_score = 3
        factors.append(f'매우 소액 ({desired_amount:,}원)')
    
    score += amount_score
    
    # 점수 보정 (사용자 성향 점수 반영)
    # 성향 점수가 높을수록 약간 더 높은 점수 부여
    test_score_adjustment = min(test_score / 100 * 5, 5)
    score = min(score + test_score_adjustment, 100)
    
    reason = ', '.join(factors)
    
    return {
        'score': round(score, 1),
        'reason': reason,
        'factors': factors,
    }


