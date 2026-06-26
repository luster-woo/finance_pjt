import json
import re

import requests
from django.conf import settings


GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'


def _request_json(url, **kwargs):
    response = requests.post(url, timeout=20, **kwargs)
    response.raise_for_status()
    return response.json()


def _extract_json(text):
    if not text:
        return []

    cleaned = text.strip()
    fenced = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []

    if isinstance(data, dict):
        for key in ('recommendations', 'items', 'results', 'data'):
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            data = []
    return data if isinstance(data, list) else []


def _normalize_recommendations(items, id_key, valid_ids):
    normalized = []
    seen = set()

    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            item_id = int(item.get(id_key))
            score = float(item.get('score', 0))
        except (TypeError, ValueError):
            continue
        if item_id not in valid_ids or item_id in seen:
            continue

        reason = str(item.get('reason', '')).strip()
        # 50자 초과 시 자르되, 숫자 안 소수점은 건드리지 않음
        if reason and len(reason) > 50:
            reason = reason[:50].rsplit(' ', 1)[0] + '…'
        normalized.append({
            id_key: item_id,
            'score': max(0, min(score, 100)),
            'reason': reason or '성향 기반 추천.',
        })
        seen.add(item_id)

    return normalized


def _call_gemini(prompt):
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    model = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
    if not api_key:
        return []
    if not model.startswith('gemini-'):
        return []

    payload = _request_json(
        GEMINI_URL.format(model=model),
        params={'key': api_key},
        json={
            'contents': [
                {
                    'parts': [
                        {'text': prompt}
                    ]
                }
            ],
            'generationConfig': {
                'temperature': 0.2,
                'responseMimeType': 'application/json',
            },
        },
    )
    text = (
        payload.get('candidates', [{}])[0]
        .get('content', {})
        .get('parts', [{}])[0]
        .get('text', '')
    )
    return _extract_json(text)


def _is_gemini_url(url):
    return 'generativelanguage' in url or 'gemini' in url.lower()


def _gms_raw_call(prompt, max_tokens=2048):
    """SSAFY GMS API 호출 — Gemini/OpenAI URL 자동 감지 후 적절한 포맷으로 요청."""
    api_key = (getattr(settings, 'GMS_API_KEY', '') or '').strip()
    api_url = getattr(settings, 'GMS_API_URL', '')
    model = getattr(settings, 'GMS_MODEL', 'gpt-4o-mini')
    if not api_key or not api_url:
        return None
    try:
        if _is_gemini_url(api_url):
            # Gemini API 포맷 — key를 쿼리 파라미터로 전달 (GMS 방식)
            payload = _request_json(
                api_url,
                params={'key': api_key},
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [{'parts': [{'text': prompt}]}],
                    'generationConfig': {
                        'temperature': 0.3,
                        'maxOutputTokens': max_tokens,
                    },
                },
            )
        else:
            # OpenAI 호환 포맷
            payload = _request_json(
                api_url,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_completion_tokens': max_tokens,
                    'temperature': 0.3,
                },
            )
        return payload
    except Exception:
        pass
    return None


def _extract_text_from_response(payload):
    """GMS 응답에서 텍스트 추출 (Gemini·Anthropic·OpenAI 모두 처리)."""
    if not payload:
        return ''
    # Gemini 형식: candidates[0].content.parts[0].text
    candidates = payload.get('candidates')
    if isinstance(candidates, list) and candidates:
        content = candidates[0].get('content', {})
        parts = content.get('parts', [{}]) if isinstance(content, dict) else [{}]
        return parts[0].get('text', '') if parts else ''
    # Anthropic 형식: content[0].text
    if isinstance(payload.get('content'), list):
        parts = payload['content']
        return parts[0].get('text', '') if parts else ''
    if isinstance(payload.get('content'), str):
        return payload['content']
    # OpenAI 형식: choices[0].message.content
    choices = payload.get('choices')
    if isinstance(choices, list) and choices:
        return choices[0].get('message', {}).get('content', '')
    return ''


def _call_gms(prompt):
    payload = _gms_raw_call(prompt)
    if not payload:
        return []
    text = _extract_text_from_response(payload)
    return _extract_json(text)


def generate_test_description_with_gms(result_type, score, answers):
    """GMS로 금융성향 테스트 결과 3~4문장 설명 생성."""
    prompt = (
        f'당신은 전문 금융 컨설턴트입니다. 사용자의 금융성향 테스트 결과를 바탕으로 '
        f'개인화된 설명을 한국어 3~4문장으로 작성하세요. JSON 없이 순수 텍스트로만 답하세요.\n\n'
        f'성향 유형: {result_type}\n'
        f'종합 점수: {score}/100\n\n'
        f'포함 내용:\n'
        f'- 이 성향의 핵심 투자 특징\n'
        f'- 추천하는 금융상품 방향\n'
        f'- 주의해야 할 투자 습관 한 가지'
    )
    payload = _gms_raw_call(prompt, max_tokens=512)
    return _extract_text_from_response(payload).strip()


def recommend_products_by_criteria_with_gms(amount, months, products):
    """목돈·기간 기준으로 GMS가 알고리즘 기반 점수로 금융상품 추천.

    점수 알고리즘 기준 (GMS 프롬프트에 명시):
      - 금리 경쟁력   (40점): 같은 기간 내 최고금리 상위일수록 높음
      - 수익 절대액   (30점): 만기 예상 이자 금액이 클수록 높음
      - 상품 유형 적합성 (15점): 단기(≤6개월)→예금, 장기(≥12개월)→적금 선호
      - 은행 신뢰도   (15점): 시중은행 > 지방은행 > 기타 순
    """
    product_payload = []
    for product in products:
        options_match = [
            o for o in product.financialproductoption_set.all()
            if o.save_trm == months
        ]
        if not options_match:
            continue
        best_rate = max(
            (o.max_interest_rate or o.interest_rate or 0 for o in options_match),
            default=0,
        )
        base_rate = min(
            (o.interest_rate or 0 for o in options_match),
            default=0,
        )
        estimated_interest = round(amount * (best_rate / 100) * (months / 12))
        maturity = amount + estimated_interest
        product_payload.append({
            'product_id': product.id,
            'best_rate': float(best_rate),
            'estimated_interest': estimated_interest,
            'bank_name': product.bank_name,
            'product_type': product.product_type,
            '상품명': product.product_name,
            '은행명': product.bank_name,
            '유형': '예금' if product.product_type == 'deposit' else '적금',
            '기본금리(%)': float(base_rate),
            '최고금리(%)': float(best_rate),
            '예상이자(원)': estimated_interest,
            '만기수령액(원)': maturity,
        })

    if not product_payload:
        return []

    prompt = f"""당신은 금융상품 추천 전문가입니다. 아래 기준으로 각 상품에 점수(0~100)를 부여하고 추천 이유를 작성하세요.

## 투자 조건
- 투자 금액: {amount:,}원
- 투자 기간: {months}개월

## 채점 기준 (총 100점)
1. 금리 경쟁력 (40점): 동일 기간 내 최고 우대금리(best_rate) 기준 상위 상품에 높은 점수
2. 수익 절대액 (30점): 예상 이자 수익(estimated_interest)이 클수록 높은 점수
3. 상품 유형 적합성 (15점): 기간 {months}개월 → {'단기이므로 예금(deposit)이 더 적합' if months <= 6 else '장기이므로 적금(saving)이 더 적합'}
4. 은행 신뢰도 (15점): KB국민·신한·우리·하나·NH농협·IBK기업 등 시중은행 우선

## 상품 목록
{json.dumps(product_payload, ensure_ascii=False, indent=2)}

## 출력 형식
다음 JSON 배열만 반환하세요 (다른 텍스트 없이):
[{{"product_id": 숫자, "score": 숫자(0-100), "reason": "한국어 1문장 (30자 이내, 수치 직접 기재, 필드명 사용 금지)"}}, ...]"""

    try:
        ai_items = _call_gms(prompt)
    except Exception:
        ai_items = []

    valid_ids = {p['product_id'] for p in product_payload}
    if ai_items:
        normalized = _normalize_recommendations(ai_items, 'product_id', valid_ids)
        if normalized:
            return sorted(normalized, key=lambda x: x['score'], reverse=True)

    # Fallback: 알고리즘 직접 계산
    max_rate = max((p['best_rate'] for p in product_payload), default=1) or 1
    max_interest = max((p['estimated_interest'] for p in product_payload), default=1) or 1
    major_banks = {'KB국민', '신한', '우리', '하나', 'NH농협', 'IBK기업', '카카오뱅크', '토스뱅크'}

    def _score(p):
        rate_s = (p['best_rate'] / max_rate) * 40
        interest_s = (p['estimated_interest'] / max_interest) * 30
        type_pref = '예금' if months <= 6 else '적금'
        type_s = 15 if (type_pref == '예금' and p['product_type'] == 'deposit') or \
                       (type_pref == '적금' and p['product_type'] == 'saving') else 5
        bank_s = 15 if any(k in p['bank_name'] for k in major_banks) else 8
        return rate_s + interest_s + type_s + bank_s

    fallback = sorted(product_payload, key=_score, reverse=True)
    return [
        {
            'product_id': p['product_id'],
            'score': round(_score(p), 1),
            'reason': (
                f'{months}개월 기준 최고 금리 {p["best_rate"]}%, '
                f'만기 이자 {p["estimated_interest"]:,}원 예상. '
                f'{p["bank_name"]}의 {("예금" if p["product_type"] == "deposit" else "적금")} 상품입니다.'
            ),
        }
        for p in fallback
    ]


def _call_ai(prompt):
    gms_items = _call_gms(prompt)
    if gms_items:
        return gms_items
    return _call_gemini(prompt)


def _fallback_product_recommendations(test, products):
    results = []
    for product in products:
        options = list(product.financialproductoption_set.all())
        max_rate = max(
            [option.max_interest_rate or option.interest_rate or 0 for option in options],
            default=0,
        )
        base_rate = min(
            [option.interest_rate or 0 for option in options if option.interest_rate],
            default=0,
        )
        best_trm = max([o.save_trm for o in options], default=0) if options else 0
        stability_bonus = 8 if product.product_type == 'deposit' and test.score <= 50 else 0
        growth_bonus = 8 if product.product_type == 'saving' and test.score > 50 else 0
        score = min(100, 55 + float(max_rate) * 6 + stability_bonus + growth_bonus)

        results.append({
            'product_id': product.id,
            'score': round(score, 2),
            'bank_name': product.bank_name,
            'product_type': product.product_type,
            'max_rate': max_rate,
            'base_rate': base_rate,
            'best_trm': best_trm,
            'target_user': product.target_user or '',
            'join_way': product.join_way or '',
        })

    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)

    # 순위별 다른 관점으로 이유 생성 (중복 방지)
    def _angle0(p): return f"최고금리 {p['max_rate']}% — 동 기간 상위 수익률 상품."
    def _angle1(p): return f"기본금리 {p['base_rate']}%에 최고 {p['max_rate']}% 우대 가능."
    def _angle2(p):
        if p['product_type'] == 'deposit':
            return "예금자 보호 5천만원 적용 안전 상품."
        return f"최대 {p['best_trm']}개월 적립으로 목돈 마련 가능."
    def _angle3(p):
        t = '예금' if p['product_type'] == 'deposit' else '적금'
        return f"가입 제한 없는 {p['bank_name']} {t}, 금리 {p['max_rate']}%."
    def _angle4(p): return f"{p['bank_name']} 대표 상품, 최고 {p['max_rate']}% 금리 제공."
    ANGLES = [_angle0, _angle1, _angle2, _angle3, _angle4]

    final = []
    for rank, item in enumerate(sorted_results):
        angle = ANGLES[rank % len(ANGLES)]
        final.append({
            'product_id': item['product_id'],
            'score': item['score'],
            'reason': angle(item),
        })
    return final


_SECTOR_REASON = {
    '금융': '배당이 안정적인 금융주로, 보수적 포트폴리오의 핵심 자산입니다.',
    '반도체': '글로벌 반도체 사이클 회복 수혜주로, 높은 성장 잠재력을 보유하고 있습니다.',
    'IT': '인터넷·플랫폼 성장 섹터로, AI·클라우드 확장에 따른 수혜가 기대됩니다.',
    '바이오': '신약 파이프라인 기반의 성장주로, 임상 결과에 따른 고수익 가능성이 있습니다.',
    '자동차': '글로벌 전기차 전환 수혜주로, 안정적 매출과 성장성을 동시에 갖추고 있습니다.',
    '소재': '배터리·이차전지 소재 섹터로, 전기차 시장 확대에 따른 수요 성장이 예상됩니다.',
    '방산': '방산 수출 증가와 지정학적 수혜로 실적 성장이 기대되는 안정 성장주입니다.',
    '건설': '국내 인프라 투자 확대와 해외 플랜트 수주로 실적 개선이 예상됩니다.',
    '엔터': 'K-POP·K-콘텐츠 글로벌 확산의 직접 수혜주로, 해외 매출 비중이 확대되고 있습니다.',
    '통신': '5G 인프라 안정화로 배당 수익률이 높은 경기 방어적 가치주입니다.',
    '게임': '글로벌 IP 확장과 신작 출시로 성장 모멘텀을 가진 콘텐츠 성장주입니다.',
    '화장품': 'K-뷰티 글로벌 확산의 수혜주로, 중국·북미 수출 회복이 기대됩니다.',
    '식품': '내수 안정성과 해외 수출 확대로 꾸준한 실적을 유지하는 경기 방어주입니다.',
}

def _fallback_stock_recommendations(test, stocks):
    from stocks.constants import SECTOR_MAP
    base = 65 if test.score <= 50 else 72
    results = []
    for index, stock in enumerate(stocks):
        sector = SECTOR_MAP.get(stock.stock_code, '기타')
        sector_reason = _SECTOR_REASON.get(sector, f'{sector} 섹터의 대표 종목입니다.')
        if test.score <= 45:
            intro = f'안정형 투자자에게 적합한 {stock.stock_name}({sector}).'
        elif test.score <= 60:
            intro = f'균형 포트폴리오 구성에 적합한 {stock.stock_name}({sector}).'
        else:
            intro = f'성장 잠재력이 높은 {stock.stock_name}({sector}).'
        results.append({
            'stock_id': stock.id,
            'score': max(0, min(100, base - index)),
            'reason': f'{intro} {sector_reason}',
        })
    return results


_SCORE_TO_CATEGORY = [
    (30,  '안정형 투자자',     '원금 보존 최우선. 예금·적금 중심. 주식 비중 최소화.'),
    (45,  '안정추구형 투자자', '안정성 우선, 소폭 수익 추구. 단기 예금·저위험 적금 선호.'),
    (60,  '위험중립형 투자자', '안정성과 수익 균형. 중기 적금·배당주 병행 가능.'),
    (75,  '적극투자형 투자자', '높은 수익 추구. 장기 적금·성장주·ETF 적합.'),
    (100, '공격투자형 투자자', '고위험·고수익 추구. 성장주·테마주·장기 고금리 상품 적합.'),
]


def _score_context(score):
    for threshold, name, desc in _SCORE_TO_CATEGORY:
        if score <= threshold:
            return name, desc
    return _SCORE_TO_CATEGORY[-1][1], _SCORE_TO_CATEGORY[-1][2]


def recommend_cards_by_habits_with_gms(habits, cards):
    """소비 습관 기반 카드 추천.

    채점 기준 (100점):
      - 소비 카테고리 혜택 매칭 (40점): 선택한 습관과 카드 혜택 일치도
      - 혜택 수 및 질      (30점): 혜택 항목 수와 할인율
      - 연회비 효율성      (20점): 연회비 대비 예상 혜택 가치
      - 전월 실적 허들     (10점): 낮을수록 이용하기 쉬움
    """
    card_payload = []
    for card in cards:
        benefits = list(card.cardbenefit_set.all())
        matched_count = sum(
            1 for b in benefits
            if any(h in (b.benefit_category or '') or h in (b.benefit_detail or '') for h in habits)
        )
        card_payload.append({
            'card_id': card.id,
            'card_name': card.card_name,
            'company': card.company,
            'card_type': card.card_type,
            'annual_fee': card.annual_fee,
            'min_performance': card.min_performance,
            'matched_benefit_count': matched_count,
            'total_benefit_count': len(benefits),
            'benefits': [
                {'category': b.benefit_category, 'detail': (b.benefit_detail or '')[:80]}
                for b in benefits[:5]
            ],
        })

    habits_str = ', '.join(habits)
    prompt = f"""당신은 카드 추천 전문가입니다. 사용자의 소비 습관에 맞는 카드를 채점·추천하세요.

## 사용자 소비 습관 (비중이 높은 항목)
{habits_str}

## 채점 기준 (총 100점)
1. 소비 카테고리 혜택 매칭 (40점): matched_benefit_count 높을수록, 선택한 소비 항목과 혜택이 일치할수록 높은 점수
2. 혜택 수 및 질 (30점): total_benefit_count 많을수록, 혜택 내용이 구체적이고 실용적일수록 높은 점수
3. 연회비 효율성 (20점): annual_fee가 낮거나 없을수록(0 또는 None) 높은 점수
4. 전월 실적 (10점): min_performance가 낮거나 없을수록 높은 점수

## 카드 목록
{json.dumps(card_payload, ensure_ascii=False, indent=2)}

다음 JSON 배열만 반환 (다른 텍스트 없이):
[{{"card_id": 숫자, "score": 숫자(0-100), "reason": "한국어 추천 이유 2문장 — 어떤 소비 습관과 어떤 혜택이 왜 맞는지 설명"}}, ...]"""

    try:
        ai_items = _call_gms(prompt)
    except Exception:
        ai_items = []

    valid_ids = {c.id for c in cards}

    if ai_items:
        normalized = []
        for item in ai_items:
            if not isinstance(item, dict):
                continue
            raw_id = item.get('card_id')
            if raw_id is None:
                continue
            try:
                cid = int(raw_id)
                score = float(item.get('score', 0))
            except (TypeError, ValueError):
                continue
            if cid not in valid_ids:
                continue
            normalized.append({
                'card_id': cid,
                'score': max(0, min(score, 100)),
                'reason': str(item.get('reason', '')).strip() or '소비 습관과 혜택을 종합적으로 고려한 추천입니다.',
                'score_breakdown': {},
            })
        if normalized:
            return sorted(normalized, key=lambda x: x['score'], reverse=True)

    # Fallback: 알고리즘 직접 계산
    max_match = max((c['matched_benefit_count'] for c in card_payload), default=1) or 1
    max_benefits = max((c['total_benefit_count'] for c in card_payload), default=1) or 1
    max_perf = max((c['min_performance'] or 0 for c in card_payload), default=1) or 1

    def _score(c):
        match_s = (c['matched_benefit_count'] / max_match) * 40
        benefit_s = (c['total_benefit_count'] / max_benefits) * 30
        fee = c['annual_fee'] or 0
        fee_s = 20 if fee == 0 else max(0, 20 - fee / 10000)
        perf = c['min_performance'] or 0
        perf_s = 10 if perf == 0 else max(0, 10 - perf / 100000)
        return match_s + benefit_s + fee_s + perf_s

    fallback = sorted(card_payload, key=_score, reverse=True)
    return [
        {
            'card_id': c['card_id'],
            'score': round(_score(c), 1),
            'reason': (
                f'선택한 소비 항목 중 {c["matched_benefit_count"]}개 혜택 매칭. '
                f'총 {c["total_benefit_count"]}개 혜택 보유'
                + (f', 연회비 {c["annual_fee"]:,}원' if c["annual_fee"] else ', 연회비 없음')
                + '.'
            ),
            'score_breakdown': {
                'match_score': round((c['matched_benefit_count'] / max_match) * 40, 1),
                'benefit_score': round((c['total_benefit_count'] / max_benefits) * 30, 1),
                'fee_score': round(20 if (c['annual_fee'] or 0) == 0 else max(0, 20 - (c['annual_fee'] or 0) / 10000), 1),
                'perf_score': round(10 if (c['min_performance'] or 0) == 0 else max(0, 10 - (c['min_performance'] or 0) / 100000), 1),
            },
        }
        for c in fallback
    ]


def _get_nearby_bank_names(address):
    """카카오 로컬 API로 주소 주변 은행 이름 목록 반환."""
    if not address:
        return set()
    import os
    kakao_key = (
        getattr(settings, 'KAKAO_REST_API_KEY', '')
        or os.environ.get('KAKAO_REST_API_KEY', '')
    )
    if not kakao_key:
        return set()
    try:
        # 1. 주소 → 좌표
        geo = requests.get(
            'https://dapi.kakao.com/v2/local/search/address.json',
            headers={'Authorization': f'KakaoAK {kakao_key}'},
            params={'query': address}, timeout=5,
        ).json()
        docs = geo.get('documents', [])
        if not docs:
            return set()
        x = docs[0].get('x') or docs[0].get('address', {}).get('x')
        y = docs[0].get('y') or docs[0].get('address', {}).get('y')
        if not x or not y:
            return set()
        # 2. 반경 1km 내 은행 검색
        result = requests.get(
            'https://dapi.kakao.com/v2/local/search/category.json',
            headers={'Authorization': f'KakaoAK {kakao_key}'},
            params={'category_group_code': 'BK9', 'x': x, 'y': y, 'radius': 1000, 'size': 15},
            timeout=5,
        ).json()
        names = set()
        for place in result.get('documents', []):
            names.add(place.get('place_name', ''))
        return names
    except Exception:
        return set()


def _address_bank_bonus(bank_name, nearby_names):
    """주변에 해당 은행 지점이 있으면 True."""
    if not nearby_names:
        return False
    return any(bank_name in n or n.split()[0] in bank_name for n in nearby_names)


def recommend_products_with_ai(test, products):
    """성향 점수 기반 + GMS 알고리즘으로 금융상품 추천.

    채점 기준:
      - 성향 적합도 (40점): 안정형→예금 단기, 공격형→적금 장기 고금리
      - 금리 경쟁력 (35점): 최고 우대금리 기준
      - 접근성·조건 (25점): 가입 방법, 대상 제한 없는지
    """
    _, score_desc = _score_context(test.score)
    product_payload = []
    for product in products:
        options = [
            {'기간(개월)': o.save_trm, '기본금리': o.interest_rate, '최고금리': o.max_interest_rate}
            for o in product.financialproductoption_set.all()
        ]
        best_rate = max((o['최고금리'] or o['기본금리'] or 0 for o in options), default=0)
        product_payload.append({
            'product_id': product.id,
            '상품명': product.product_name,
            '은행명': product.bank_name,
            '유형': '예금' if product.product_type == 'deposit' else '적금',
            '가입대상': product.target_user or '제한 없음',
            '금리옵션': options,
            '최고금리(%)': float(best_rate),
        })

    prompt = f"""당신은 금융 상품 추천 전문가입니다. 사용자 금융성향에 맞게 상품을 채점·추천하세요.

## 사용자 금융성향
- 성향 유형: {test.result_type} (점수 {test.score}/100)
- 성향 설명: {score_desc}

## 채점 기준 (총 100점)
1. 성향 적합도 (40점)
   - 점수 ≤45: 예금(deposit) + 단기(1~6개월) 상품에 높은 점수
   - 점수 46~60: 예금·적금 균형, 6~12개월 상품 우대
   - 점수 ≥61: 적금(saving) + 장기(12개월 이상) + 고금리 상품에 높은 점수
2. 금리 경쟁력 (35점): best_rate 높을수록 높은 점수
3. 접근성 (25점): 가입 대상 제한이 적을수록 높은 점수

## 상품 목록
{json.dumps(product_payload, ensure_ascii=False, indent=2)}

다음 JSON 배열만 반환 (다른 텍스트 없이):
[{{"product_id": 숫자, "score": 숫자(0-100), "reason": "한국어 추천 이유 1문장 (30자 이내, 수치 직접 기재, 필드명 사용 금지)"}}, ...]"""

    try:
        ai_items = _call_ai(prompt)
    except requests.RequestException:
        ai_items = []

    valid_ids = {product.id for product in products}
    normalized = _normalize_recommendations(ai_items, 'product_id', valid_ids)
    result = normalized or _fallback_product_recommendations(test, products)
    # 같은 은행 중복 방지: 상위 결과에서 동일 은행은 1개만 유지
    product_map = {p.id: p for p in products}
    seen_banks = set()
    diverse = []
    rest = []
    for item in result:
        p = product_map.get(item['product_id'])
        bank = p.bank_name if p else ''
        if bank not in seen_banks:
            seen_banks.add(bank)
            diverse.append(item)
        else:
            rest.append(item)
    return diverse + rest


def recommend_stocks_with_ai(test, stocks):
    """성향 점수 기반 + GMS 알고리즘으로 주식 추천.

    채점 기준:
      - 성향 적합도 (45점): 안정형→배당주·금융주, 공격형→성장주·반도체·IT
      - 섹터 분산 (30점): 포트폴리오 다양성 고려
      - 시가총액 안정성 (25점): 안정형일수록 대형주 우선
    """
    _, score_desc = _score_context(test.score)
    stock_payload = [
        {
            'stock_id': stock.id,
            'stock_code': stock.stock_code,
            'stock_name': stock.stock_name,
            'description': stock.description[:100] if stock.description else '',
        }
        for stock in stocks
    ]

    prompt = f"""당신은 주식 추천 전문가입니다. 사용자 금융성향에 맞게 종목을 채점·추천하세요.

## 사용자 금융성향
- 성향 유형: {test.result_type} (점수 {test.score}/100)
- 성향 설명: {score_desc}

## 채점 기준 (총 100점)
1. 성향 적합도 (45점)
   - 점수 ≤45 (안정형): 금융주(KB금융·신한지주·하나금융), 배당주, LG·SK 등 지주사에 높은 점수
   - 점수 46~60 (중립형): 현대차·기아 등 제조업, LG화학·포스코 등 소재 우대
   - 점수 ≥61 (적극형): 삼성전자·SK하이닉스 등 반도체, NAVER·카카오 등 IT, 셀트리온 등 바이오에 높은 점수
2. 섹터 분산 (30점): 추천 목록 내 서로 다른 업종 분포 고려
3. 시가총액 안정성 (25점): 점수 낮을수록 대형주(삼성전자·SK하이닉스 등) 우선

## 종목 목록
{json.dumps(stock_payload, ensure_ascii=False, indent=2)}

다음 JSON 배열만 반환 (다른 텍스트 없이):
[{{"stock_id": 숫자, "score": 숫자(0-100), "reason": "한국어 1문장 (30자 이내, 필드명 사용 금지)"}}, ...]"""

    try:
        ai_items = _call_ai(prompt)
    except requests.RequestException:
        ai_items = []

    valid_ids = {stock.id for stock in stocks}
    normalized = _normalize_recommendations(ai_items, 'stock_id', valid_ids)
    return normalized or _fallback_stock_recommendations(test, stocks)
