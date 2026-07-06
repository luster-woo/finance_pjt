import datetime
from decimal import Decimal

import requests
import yfinance as yf
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from config.pagination import StandardPagination


def _translate_to_korean(company_name, en_text):
    """GMS(Claude)를 이용해 영문 회사 설명을 한국어 2문장으로 요약·번역."""
    api_key = getattr(settings, 'GMS_API_KEY', '')
    api_url = getattr(settings, 'GMS_API_URL', '')
    model = getattr(settings, 'GMS_MODEL', 'gpt-5.4-mini')
    if not api_key or not api_url:
        return ''

    prompt = (
        f'다음은 "{company_name}"에 대한 영문 설명입니다. '
        f'이를 한국어 2문장으로 간결하게 요약해주세요. '
        f'JSON 없이 순수 텍스트로만 답하세요.\n\n{en_text[:800]}'
    )

    try:
        # SSAFY GMS (OpenAI 호환)
        resp = requests.post(
            api_url,
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': model, 'max_completion_tokens': 256, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0.3},
            timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json()
        choices = payload.get('choices')
        if isinstance(choices, list) and choices:
            return choices[0].get('message', {}).get('content', '').strip()
    except Exception:
        pass
    return ''

from .models import Stock, StockPrice, StockFavorite
from .serializers import StockSerializer, StockPriceSerializer


# 주요 KOSPI/KOSDAQ 종목 — 섹터별 다양화
MAJOR_STOCKS = [
    # ── 반도체/IT ──────────────────────────────
    ('005930', '삼성전자',           'IT/전자 분야 글로벌 선도 기업, 반도체·스마트폰·가전 제조'),
    ('000660', 'SK하이닉스',         '메모리 반도체(D램·낸드플래시) 세계 2위 기업'),
    ('058470', '리노공업',           '반도체 테스트 소켓 전문 기업, 고부가 반도체 부품 제조'),
    ('042700', '한미반도체',         '반도체 패키징 장비 및 TC 본더 세계 1위 기업'),
    ('000990', 'DB하이텍',           '파운드리(반도체 수탁 생산) 전문 기업'),

    # ── 인터넷/플랫폼 ──────────────────────────
    ('035420', 'NAVER',              '국내 최대 인터넷 플랫폼 기업, 검색·광고·커머스·클라우드'),
    ('035720', '카카오',             '모바일 메신저 기반 IT 플랫폼 기업'),
    ('323410', '카카오뱅크',         '카카오 계열 인터넷 전문 은행, 비대면 금융 서비스 선도'),

    # ── 게임 ───────────────────────────────────
    ('293490', '카카오게임즈',       '카카오 계열 모바일·PC 게임 전문 기업'),
    ('259960', '크래프톤',           '배틀그라운드(PUBG) 개발·운영 글로벌 게임사'),
    ('036570', '엔씨소프트',         '리니지·블레이드&소울 등 MMORPG 대표 게임사'),
    ('251270', '넷마블',             '세계 5위권 모바일 게임사, 다수 글로벌 IP 보유'),
    ('263750', '펄어비스',           '검은사막 개발·서비스 글로벌 게임사'),

    # ── 자동차/모빌리티 ────────────────────────
    ('005380', '현대차',             '국내 1위 완성차 제조 기업'),
    ('000270', '기아',               '글로벌 자동차 제조 기업, 현대차그룹 계열'),
    ('012330', '현대모비스',         '현대차그룹 핵심 부품·모듈 계열사, 자율주행 부품 개발'),
    ('241560', '두산밥캣',           '소형 건설기계·산업차량 글로벌 브랜드'),

    # ── 배터리/소재 ────────────────────────────
    ('051910', 'LG화학',             '배터리·석유화학·첨단소재 분야 글로벌 기업'),
    ('006400', '삼성SDI',            '이차전지(EV배터리)·전자재료 전문 기업'),
    ('003670', '포스코퓨처엠',       '양극재·음극재 배터리 소재 전문 기업'),
    ('096770', 'SK이노베이션',       '에너지·화학·배터리 전문 SK그룹 계열사'),
    ('247540', '에코프로비엠',       '양극재 전문 이차전지 소재 기업, KOSDAQ 대형주'),
    ('086520', '에코프로',           '에코프로비엠 지주사, 이차전지 소재 그룹'),

    # ── 바이오/제약/헬스케어 ───────────────────
    ('068270', '셀트리온',           '항체 바이오시밀러 전문 제약·바이오 기업'),
    ('207940', '삼성바이오로직스',   '바이오의약품 위탁생산(CDMO) 세계 1위 기업'),
    ('196170', '알테오젠',           '피하주사 변환 플랫폼 기술 보유 바이오 기업'),
    ('145020', '휴젤',               '보툴리눔 톡신·히알루론산 필러 글로벌 수출 기업'),
    ('000100', '유한양행',           '국내 최대 제약사 중 하나, 항암제·만성질환 신약 개발'),
    ('128940', '한미약품',           '의약품 수출 강자, 글로벌 기술수출 성과 다수'),
    ('048260', '오스템임플란트',     '치과용 임플란트 국내 1위·글로벌 3위 의료기기 기업'),

    # ── 방산/항공우주 ──────────────────────────
    ('012450', '한화에어로스페이스', '항공기 엔진·방산 무기체계 국내 1위 방산 기업'),
    ('079550', 'LIG넥스원',          '유도무기·레이더 등 첨단 방산 전자 시스템 전문 기업'),
    ('047810', '한국항공우주',       '군용기·항공기 기체 제조 국내 유일 완성기 업체(KAI)'),
    ('064350', '현대로템',           '철도차량·방산 장갑차 제조, 수소 트램 등 미래 모빌리티'),

    # ── 건설/인프라 ────────────────────────────
    ('000720', '현대건설',           '국내 최대 건설사, 해외 플랜트·인프라 수주 강자'),
    ('006360', 'GS건설',             '아파트·플랜트·해외 건설 복합 건설사'),
    ('028050', '삼성엔지니어링',     '화공 플랜트·환경 에너지 EPC 전문 엔지니어링 기업'),

    # ── 철강/소재/화학 ─────────────────────────
    ('005490', '포스코홀딩스',       '국내 최대 철강사, 이차전지소재·수소 신사업 추진'),
    ('004020', '현대제철',           '현대차그룹 계열 철강 전문 기업'),
    ('010130', '고려아연',           '아연·납·금·은 제련 세계 1위 비철금속 기업'),

    # ── 금융/증권 ──────────────────────────────
    ('105560', 'KB금융',             'KB국민은행 등을 보유한 국내 최대 금융 지주'),
    ('055550', '신한지주',           '신한은행·신한카드 등 종합 금융 지주 회사'),
    ('086790', '하나금융지주',       '하나은행 등을 보유한 금융 지주 회사'),
    ('032830', '삼성생명',           '국내 최대 생명보험사'),
    ('006800', '미래에셋증권',       '국내 최대 증권사, 해외 투자·ETF 운용 선도'),
    ('039490', '키움증권',           '온라인 주식거래 시장점유율 1위 증권사'),

    # ── 통신 ───────────────────────────────────
    ('017670', 'SK텔레콤',           '국내 1위 이동통신사, AI·메타버스·클라우드 사업 확장'),
    ('030200', 'KT',                 '국내 2위 통신사, AI·데이터센터·미디어 사업 운영'),
    ('032640', 'LG유플러스',         'LG그룹 계열 통신사, 5G·IPTV·IDC 서비스 제공'),

    # ── 에너지 ─────────────────────────────────
    ('010950', 'S-Oil',              '사우디 아람코 계열 정유·석유화학 기업'),
    ('015760', '한국전력',           '국가 전력 공급 독점 공기업, 신재생에너지 전환 추진'),

    # ── 엔터/미디어 ────────────────────────────
    ('352820', '하이브',             '방탄소년단(BTS) 소속 글로벌 엔터테인먼트 기업'),
    ('041510', 'SM엔터테인먼트',     'K-POP 아티스트 기획·제작 선도 엔터 기업'),
    ('041960', 'JYP엔터테인먼트',   'TWICE·있지·스키즈 소속 K-POP 엔터사'),
    ('035760', 'CJ ENM',             '케이블TV·OTT·음악·영화 등 미디어 콘텐츠 복합 기업'),

    # ── 화장품/뷰티 ────────────────────────────
    ('090430', '아모레퍼시픽',       '설화수·이니스프리 등 K-뷰티 글로벌 화장품 기업'),
    ('051900', 'LG생활건강',         '화장품·음료·생활용품 복합 소비재 기업'),
    ('161890', '한국콜마',           '화장품 OEM/ODM 국내 1위, 북미·중국 글로벌 생산 거점'),
    ('192820', '코스맥스',           '화장품 ODM 세계 1위, 80개국 수출 K-뷰티 제조 기업'),

    # ── 식품/음료 ──────────────────────────────
    ('097950', 'CJ제일제당',         '식품·바이오·물류 복합 CJ그룹 핵심 계열사'),
    ('271560', '오리온',             '초코파이 등 과자·스낵 한·중·러·베트남 4개국 생산'),
    ('004370', '농심',               '신라면 등 라면·스낵 글로벌 수출 식품 기업'),

    # ── 유통/물류/여행 ─────────────────────────
    ('139480', '이마트',             '국내 최대 대형마트 운영사, SSG닷컴 이커머스 운영'),
    ('000120', 'CJ대한통운',         '국내 1위 종합 물류사, 글로벌 계약물류 사업 확대'),
    ('011200', 'HMM',                '국내 최대 컨테이너 해운사, 글로벌 물류 네트워크 운영'),
    ('003490', '대한항공',           '국내 최대 항공사, 아시아나항공 인수 합병 진행 중'),
    ('008770', '호텔신라',           '신라호텔·신라면세점 운영, 여행·면세 복합 기업'),

    # ── 지주/복합 ──────────────────────────────
    ('028260', '삼성물산',           '건설·상사·패션·리조트 복합 대기업, 삼성그룹 지주격'),
    ('066570', 'LG전자',             '가전·TV·모바일 분야 글로벌 전자 기업'),
    ('034220', 'LG디스플레이',       'OLED 디스플레이 세계 1위, TV·스마트폰 패널 공급'),
    ('034730', 'SK',                 'SK그룹 지주회사, SK하이닉스·SK텔레콤 등 계열사 보유'),
    ('003550', 'LG',                 'LG그룹 지주회사, LG전자·LG화학·LG에너지솔루션 보유'),
]

# KOSDAQ 종목 코드 세트
_KOSDAQ_CODES = {
    '247540', '086520', '196170', '145020',
    '293490', '263750', '058470',
    '048260',
}


def _yf_ticker(stock_code):
    """종목코드 → Yahoo Finance 티커 (KOSPI는 .KS, KOSDAQ은 .KQ)"""
    suffix = '.KQ' if stock_code in _KOSDAQ_CODES else '.KS'
    return f'{stock_code}{suffix}'


@api_view(['GET'])
def stock_list(request):
    from django.db.models import OuterRef, Subquery
    latest_price_qs = StockPrice.objects.filter(stock=OuterRef('pk')).order_by('-recorded_at')
    stocks = Stock.objects.annotate(
        latest_price=Subquery(latest_price_qs.values('price')[:1]),
        latest_change_rate=Subquery(latest_price_qs.values('change_rate')[:1]),
    )
    paginator = StandardPagination()
    page = paginator.paginate_queryset(stocks, request)
    serializer = StockSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def stock_detail(request, stock_id):
    stock = get_object_or_404(Stock, pk=stock_id)
    serializer = StockSerializer(stock)
    return Response(serializer.data)


@api_view(['GET'])
def stock_latest_price(request, stock_id):
    """DB에 캐시된 최신 시세 반환. 없으면 yfinance에서 실시간 조회."""
    stock = get_object_or_404(Stock, pk=stock_id)
    price = StockPrice.objects.filter(stock=stock).order_by('-recorded_at').first()

    if price:
        serializer = StockPriceSerializer(price)
        return Response(serializer.data)

    # DB에 없으면 yfinance로 실시간 조회
    try:
        ticker = _yf_ticker(stock.stock_code)
        info = yf.Ticker(ticker).fast_info
        current_price = getattr(info, 'last_price', None)
        prev_close = getattr(info, 'previous_close', None)
        if current_price and prev_close and prev_close != 0:
            change_rate = round((current_price - prev_close) / prev_close * 100, 2)
        else:
            change_rate = None
        return Response({
            'id': None,
            'stock': stock.id,
            'price': str(round(current_price)) if current_price else None,
            'change_rate': str(change_rate) if change_rate is not None else None,
            'volume': None,
            'recorded_at': timezone.now().isoformat(),
        })
    except Exception as exc:
        return Response({'detail': f'시세 조회 실패: {exc}'}, status=404)


@api_view(['GET'])
def stock_prices(request, stock_id):
    prices = StockPrice.objects.filter(stock_id=stock_id).order_by('-recorded_at')
    serializer = StockPriceSerializer(prices, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def import_stock_issues(request):
    """
    주요 한국 주식 종목 정보를 yfinance에서 가져와 DB에 저장합니다.
    ?codes=005930,000660 으로 특정 종목만 지정 가능.
    """
    codes_param = request.GET.get('codes', '')
    if codes_param:
        target_codes = [c.strip() for c in codes_param.split(',') if c.strip()]
        targets = [(code, name, desc) for code, name, desc in MAJOR_STOCKS if code in target_codes]
        if not targets:
            return Response({'detail': '유효한 종목 코드가 없습니다.'}, status=400)
    else:
        targets = MAJOR_STOCKS

    created = updated = 0
    errors = []

    for stock_code, default_name, default_desc in targets:
        ticker_sym = _yf_ticker(stock_code)
        # 한국어 기본명·기본 설명 우선 사용 (yfinance는 영문 반환)
        name = default_name
        desc = default_desc
        try:
            ticker = yf.Ticker(ticker_sym)
            info = ticker.info
            # yfinance에서 영문 설명이 있으면 GMS로 한국어 요약 시도
            en_summary = info.get('longBusinessSummary', '')
            if en_summary and len(en_summary) > 50:
                translated = _translate_to_korean(default_name, en_summary)
                if translated:
                    desc = translated
        except Exception:
            pass

        stock, flag = Stock.objects.update_or_create(
            stock_code=stock_code,
            defaults={'stock_name': name, 'description': desc},
        )
        if flag:
            created += 1
        else:
            updated += 1

    return Response({
        'imported': len(targets),
        'created': created,
        'updated': updated,
        'errors': errors,
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def import_stock_prices(request):
    """
    yfinance로 특정 종목의 최근 가격 이력을 가져와 DB에 저장합니다.
    ?stock_code=005930&period=1mo (기본 1개월)
    period 옵션: 1d, 5d, 1mo, 3mo, 6mo, 1y
    """
    stock_code = request.GET.get('stock_code')
    if not stock_code:
        return Response({'detail': 'stock_code query parameter is required.'}, status=400)

    period = request.GET.get('period', '1mo')
    valid_periods = {'1d', '5d', '1mo', '3mo', '6mo', '1y', '2y'}
    if period not in valid_periods:
        return Response({'detail': f'period는 {valid_periods} 중 하나여야 합니다.'}, status=400)

    ticker_sym = _yf_ticker(stock_code)
    try:
        df = yf.Ticker(ticker_sym).history(period=period)
    except Exception as exc:
        return Response({'detail': f'yfinance 조회 실패: {exc}'}, status=500)

    if df.empty:
        return Response({'detail': f'{stock_code} 가격 데이터가 없습니다.'}, status=404)

    stock, _ = Stock.objects.get_or_create(
        stock_code=stock_code,
        defaults={'stock_name': stock_code, 'description': ''},
    )

    saved = 0
    prev_close = None
    for date, row in df.iterrows():
        close = row.get('Close')
        try:
            import math as _math
            if close is None or _math.isnan(float(close)):
                prev_close = None
                continue
        except (TypeError, ValueError):
            prev_close = None
            continue
        change_rate = None
        if prev_close is not None and prev_close != 0:
            change_rate = round((float(close) - prev_close) / prev_close * 100, 2)
        prev_close = float(close)

        recorded_at = date.to_pydatetime().replace(tzinfo=None) if hasattr(date, 'to_pydatetime') else date

        _, created_flag = StockPrice.objects.get_or_create(
            stock=stock,
            recorded_at=recorded_at,
            defaults={
                'price': Decimal(str(round(float(close), 2))),
                'change_rate': Decimal(str(change_rate)) if change_rate is not None else None,
                'volume': int(row.get('Volume', 0) or 0),
            }
        )
        if created_flag:
            saved += 1

    return Response({
        'stock_code': stock_code,
        'period': period,
        'rows_in_response': len(df),
        'saved': saved,
    })


@api_view(['GET'])
def stock_news(request, stock_id):
    """yfinance로 해당 종목의 최신 뉴스를 가져옵니다."""
    stock = get_object_or_404(Stock, pk=stock_id)
    ticker_sym = _yf_ticker(stock.stock_code)
    try:
        ticker = yf.Ticker(ticker_sym)
        raw_news = ticker.news or []
    except Exception as exc:
        return Response({'detail': f'뉴스 조회 실패: {exc}'}, status=500)

    raw_articles = []
    for item in raw_news[:10]:
        content = item.get('content') or {}
        title = content.get('title') or item.get('title') or ''
        if not title:
            continue
        summary = content.get('summary') or item.get('summary') or ''
        provider = content.get('provider')
        provider = provider if isinstance(provider, dict) else {}
        publisher = provider.get('displayName') or item.get('publisher') or ''
        canonical = content.get('canonicalUrl')
        canonical = canonical if isinstance(canonical, dict) else {}
        link = canonical.get('url') or item.get('link') or item.get('url') or ''
        pub_ts = content.get('pubDate') or item.get('providerPublishTime')
        if isinstance(pub_ts, (int, float)):
            published_at = datetime.datetime.fromtimestamp(pub_ts).isoformat()
        elif pub_ts:
            published_at = str(pub_ts)
        else:
            published_at = None
        raw_articles.append({
            'title': title,
            'summary': summary,
            'url': link,
            'publisher': publisher,
            'published_at': published_at,
        })

    # 제목 일괄 번역 (GMS 1회 호출)
    titles_en = [a['title'] for a in raw_articles]
    titles_ko = _translate_news_batch(titles_en)

    articles = []
    for i, a in enumerate(raw_articles):
        ko_title = titles_ko[i] if i < len(titles_ko) else a['title']
        articles.append({
            'title': ko_title or a['title'],
            'title_en': a['title'],
            'summary': a['summary'],
            'url': a['url'],
            'publisher': a['publisher'],
            'published_at': a['published_at'],
        })

    return Response(articles)


def _translate_news_batch(titles):
    """영문 뉴스 제목 목록을 한 번의 GMS 호출로 일괄 한국어 번역.
    반환: 동일 순서의 번역 제목 리스트 (실패 시 원문 유지)"""
    if not titles:
        return titles
    api_key = getattr(settings, 'GMS_API_KEY', '')
    api_url = getattr(settings, 'GMS_API_URL', '')
    model = getattr(settings, 'GMS_MODEL', 'gpt-4o-mini')
    if not api_key or not api_url:
        return titles

    prompt = (
        '다음 영문 뉴스 제목들을 한국어로 번역하여 JSON 배열로만 반환하세요. '
        '배열 외 다른 텍스트, 설명, 마크다운은 절대 포함하지 마세요.\n\n'
        '제목 목록:\n' +
        '\n'.join(f'{i+1}. {t}' for i, t in enumerate(titles)) +
        '\n\n출력 형식 예시: ["번역1", "번역2", "번역3"]'
    )
    try:
        api_key = api_key.strip()
        is_gemini = 'generativelanguage' in api_url or 'gemini' in api_url.lower()
        if is_gemini:
            resp = requests.post(
                api_url,
                params={'key': api_key},
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [{'parts': [{'text': prompt}]}],
                    'generationConfig': {
                        'temperature': 0.1,
                        'maxOutputTokens': 4096,
                        'responseMimeType': 'application/json',
                    },
                },
                timeout=15,
            )
        else:
            resp = requests.post(
                api_url,
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={
                    'model': model,
                    'max_completion_tokens': 512,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.1,
                },
                timeout=15,
            )
        resp.raise_for_status()
        data = resp.json()
        if is_gemini:
            cands = data.get('candidates', [])
            text = cands[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip() if cands else ''
        else:
            choices = data.get('choices')
            text = choices[0].get('message', {}).get('content', '').strip() if choices else ''

        # JSON 배열 파싱
        import json as _json, re
        # 마크다운 코드블록 제거
        text = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`').strip()
        parsed_arr = _json.loads(text)
        if isinstance(parsed_arr, list):
            result = list(titles)
            for i, ko in enumerate(parsed_arr[:len(result)]):
                if ko and isinstance(ko, str):
                    result[i] = ko
            return result
    except Exception as _e:
        import logging
        logging.getLogger(__name__).warning('번역 실패: %s', _e)
    return titles


def _translate_news(title, summary=''):
    """단일 뉴스 번역 (하위 호환용 — 배치 함수 래핑)."""
    result = _translate_news_batch([title])
    return result[0] if result else ''


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def stock_favorite_toggle(request, stock_id):
    stock = get_object_or_404(Stock, pk=stock_id)

    if request.method == 'GET':
        is_fav = StockFavorite.objects.filter(user=request.user, stock=stock).exists()
        return Response({'is_favorite': is_fav})

    favorite, created = StockFavorite.objects.get_or_create(user=request.user, stock=stock)
    if not created:
        favorite.delete()
        return Response({'message': '관심종목 삭제', 'is_favorite': False})
    return Response({'message': '관심종목 추가', 'is_favorite': True})
