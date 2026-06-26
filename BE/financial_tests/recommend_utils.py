"""
금융상품 추천 알고리즘 및 AI 프롬프트 생성
"""


def generate_recommendation_prompt(test_score, result_type, product, product_option, desired_amount=1000000):
    """
    AI 추천 프롬프트 생성
    
    Args:
        test_score: 금융성향 점수 (0-100)
        result_type: 성향 타입 ('안정형', '안정추구형', '위험중립형', '적극투자형', '공격투자형')
        product: FinancialProduct 인스턴스
        product_option: FinancialProductOption 인스턴스
        desired_amount: 예상 금액 (기본 100만원)
    
    Returns:
        dict: 프롬프트 정보
    """
    
    prompt = f"""
사용자의 금융상품 추천 점수를 계산해주세요.

사용자 정보:
- 금융성향 점수: {test_score}/100
- 성향 타입: {result_type}
- 예상 투자 금액: {desired_amount:,}원

상품 정보:
- 상품명: {product.product_name}
- 은행: {product.bank_name}
- 상품타입: {product.product_type}
- 가입기간: {product_option.save_trm}개월
- 이자율: {product_option.interest_rate or 0}%
- 최고이자율: {product_option.max_interest_rate or 0}%

다음 기준으로 0~100점을 부여해주세요:
1. 성향과 상품의 적합도 (위험도)
2. 기간과 사용자 목표의 부합도
3. 이자율 경쟁력
4. 자금 규모와 상품의 적합도

JSON 형식으로 응답:
{{
    "score": <0-100의 숫자>,
    "reason": "추천 이유",
    "pros": ["장점1", "장점2"],
    "cons": ["단점1", "단점2"]
}}
"""
    
    return {
        'score': test_score,
        'result_type': result_type,
        'product_name': product.product_name,
        'product_type': product.product_type,
        'period': product_option.save_trm,
        'interest_rate': product_option.interest_rate,
        'desired_amount': desired_amount,
        'prompt': prompt,
    }


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


def call_ai_recommendation_api(prompt_data):
    """
    AI API를 호출하여 추천 점수 계산 (미구현 - 추후 GMS API 또는 다른 AI 연동)
    
    Args:
        prompt_data: generate_recommendation_prompt에서 반환한 dict
    
    Returns:
        dict: {'score': 0-100, 'reason': str}
    
    참고: 현재는 알고리즘 기반, 추후 다음과 같이 연동 가능:
    - GMS API (사용자 언급)
    - OpenAI GPT API
    - 네이버 Papago API
    - 기타 LLM
    """
    
    # TODO: AI API 연동 구현
    # response = requests.post(
    #     'https://api.example.com/recommend',
    #     json=prompt_data,
    #     headers={'Authorization': f'Bearer {settings.AI_API_KEY}'}
    # )
    # return response.json()
    
    raise NotImplementedError("AI API 연동은 추후 구현 예정")
