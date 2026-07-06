"""
APScheduler 기반 주기적 데이터 수집 스케줄러.

등록된 작업:
  - collect_news          : 매 3시간마다  금융/경제 RSS 뉴스 수집
  - update_stock_prices   : 매일 오후 5시  주요 종목 시세 업데이트 (장 마감 후)
  - update_commodities    : 매일 오전 8시  금·은 시세 업데이트
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler = None


# ──────────────────────────────────────────────
#  작업 함수
# ──────────────────────────────────────────────

def _collect_news():
    """RSS 피드에서 최신 금융 뉴스 수집."""
    try:
        import time
        import re
        import html
        import feedparser
        from news.models import News

        FINANCE_RSS_FEEDS = [
            ('한국경제',      'https://www.hankyung.com/feed/economy'),
            ('한국경제',      'https://www.hankyung.com/feed/finance'),
            ('매일경제',      'https://www.mk.co.kr/rss/30100041/'),   # 경제
            ('매일경제',      'https://www.mk.co.kr/rss/50200011/'),   # 증권
            ('매일경제',      'https://www.mk.co.kr/rss/40200003/'),   # 머니 앤 리치스(재테크)
            ('연합뉴스',      'https://www.yna.co.kr/rss/economy.xml'),
            ('연합뉴스',      'https://www.yna.co.kr/rss/market.xml'),
        ]

        # 일부 언론사는 기본 User-Agent 요청을 403으로 차단하므로 브라우저로 위장
        RSS_USER_AGENT = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'
        )

        import datetime
        from django.utils.timezone import make_aware

        def _parse_st(st):
            """feedparser struct_time → timezone-aware datetime (Asia/Seoul)."""
            if not st:
                return None
            try:
                naive = datetime.datetime.fromtimestamp(time.mktime(st))
                return make_aware(naive)
            except (TypeError, ValueError, OverflowError, OSError):
                return None

        FINANCE_KEYWORDS = {
            '주식', '코스피', '코스닥', '증시', '증권', '금리', '금융', '은행', '투자', '펀드',
            '채권', 'ETF', '환율', '경제', '물가', '인플레이션', '대출', '예금', '적금',
            '보험', '배당', '기업', '실적', '매출', '영업이익', 'IPO', '상장', '인수', '합병',
            '자산', 'GDP', '경기', '수출', '수입', '무역', '달러', '엔화', '위안', '유로',
            '유가', '원유', '나스닥', '다우', '기준금리', '한국은행', '연준', 'Fed', '재테크',
            '절세', '청약', '가상화폐', '비트코인', '블록체인', '코인', '긴축', '양적완화',
            '파생', '옵션', '공매도', '시가총액', '주가',
            '재무', '세금', '세율', '부채', '자본', '흑자', '적자', '무역수지',
        }

        def _is_finance(title, summary=''):
            text = title + ' ' + summary
            return any(kw in text for kw in FINANCE_KEYWORDS)

        created = 0
        for publisher, url in FINANCE_RSS_FEEDS:
            try:
                parsed = feedparser.parse(url, request_headers={'User-Agent': RSS_USER_AGENT})
            except Exception:
                continue
            for entry in parsed.entries:
                title = html.unescape((getattr(entry, 'title', '') or '').strip())
                if not title:
                    continue
                link = getattr(entry, 'link', '') or ''
                summary = html.unescape(re.sub(r'<[^>]+>', '', (
                    getattr(entry, 'summary', '') or getattr(entry, 'description', '') or ''
                ).strip()))[:500]
                if not _is_finance(title, summary):
                    continue
                published_at = _parse_st(getattr(entry, 'published_parsed', None))
                if link:
                    _, flag = News.objects.update_or_create(
                        url=link,
                        defaults={'title': title[:255], 'summary': summary,
                                  'publisher': publisher, 'published_at': published_at}
                    )
                else:
                    _, flag = News.objects.update_or_create(
                        title=title[:255],
                        defaults={'summary': summary, 'url': link,
                                  'publisher': publisher, 'published_at': published_at}
                    )
                if flag:
                    created += 1
        logger.info('[scheduler] 뉴스 수집 완료: %d개 신규', created)
    except Exception as exc:
        logger.error('[scheduler] 뉴스 수집 실패: %s', exc)


def _update_stock_prices():
    """주요 종목의 최신 시세를 yfinance로 업데이트 (최근 5일치)."""
    try:
        from decimal import Decimal
        import yfinance as yf
        from stocks.models import Stock, StockPrice

        KOSDAQ = {'035720', '035420', '068270', '207940', '003670', '096770'}

        def ticker(code):
            return f'{code}.{"KQ" if code in KOSDAQ else "KS"}'

        stocks = Stock.objects.all()
        total = 0
        for stock in stocks:
            try:
                df = yf.Ticker(ticker(stock.stock_code)).history(period='5d')
            except Exception:
                continue
            for date, row in df.iterrows():
                close = row.get('Close')
                if close is None:
                    continue
                open_p = row.get('Open')
                change_rate = None
                if open_p and open_p != 0:
                    change_rate = round((float(close) - float(open_p)) / float(open_p) * 100, 2)
                recorded_at = date.to_pydatetime().replace(tzinfo=None) if hasattr(date, 'to_pydatetime') else date
                _, flag = StockPrice.objects.get_or_create(
                    stock=stock,
                    recorded_at=recorded_at,
                    defaults={
                        'price': Decimal(str(round(float(close), 2))),
                        'change_rate': Decimal(str(change_rate)) if change_rate is not None else None,
                        'volume': int(row.get('Volume', 0) or 0),
                    }
                )
                if flag:
                    total += 1
        logger.info('[scheduler] 주식 시세 업데이트 완료: %d개 신규', total)
    except Exception as exc:
        logger.error('[scheduler] 주식 시세 업데이트 실패: %s', exc)


def _update_commodities():
    """금·은 최신 시세를 yfinance로 업데이트 (최근 7일치)."""
    try:
        from decimal import Decimal, InvalidOperation
        import yfinance as yf
        from commodities.models import CommodityPrice

        TICKERS = {'Gold': 'GC=F', 'Silver': 'SI=F'}
        total = 0
        for commodity_type, sym in TICKERS.items():
            try:
                df = yf.Ticker(sym).history(period='7d')
            except Exception:
                continue
            for date, row in df.iterrows():
                close = row.get('Close')
                if close is None:
                    continue
                try:
                    price = Decimal(str(round(float(close), 4)))
                except (InvalidOperation, ValueError):
                    continue
                recorded_at = date.to_pydatetime().replace(tzinfo=None) if hasattr(date, 'to_pydatetime') else date
                _, flag = CommodityPrice.objects.update_or_create(
                    commodity_type=commodity_type,
                    recorded_at=recorded_at,
                    defaults={'price': price},
                )
                if flag:
                    total += 1
        logger.info('[scheduler] 원자재 시세 업데이트 완료: %d개 신규', total)
    except Exception as exc:
        logger.error('[scheduler] 원자재 시세 업데이트 실패: %s', exc)


# ──────────────────────────────────────────────
#  스케줄러 시작 / 종료
# ──────────────────────────────────────────────

def start():
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone='Asia/Seoul')

    # 뉴스: 매 3시간
    _scheduler.add_job(
        _collect_news,
        trigger=IntervalTrigger(hours=3),
        id='collect_news',
        replace_existing=True,
        max_instances=1,
    )

    # 주식 시세: 평일 오후 5시 (장 마감 1시간 후)
    _scheduler.add_job(
        _update_stock_prices,
        trigger=CronTrigger(day_of_week='mon-fri', hour=17, minute=0, timezone='Asia/Seoul'),
        id='update_stock_prices',
        replace_existing=True,
        max_instances=1,
    )

    # 원자재 시세: 매일 오전 8시
    _scheduler.add_job(
        _update_commodities,
        trigger=CronTrigger(hour=8, minute=0, timezone='Asia/Seoul'),
        id='update_commodities',
        replace_existing=True,
        max_instances=1,
    )

    # 주간 브리핑: 매주 월요일 오전 9시
    _scheduler.add_job(
        _generate_weekly_briefing,
        trigger=CronTrigger(day_of_week='mon', hour=9, minute=0, timezone='Asia/Seoul'),
        id='generate_weekly_briefing',
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.start()
    logger.info('[scheduler] APScheduler 시작 — 뉴스(3h), 주식(평일 17:00), 원자재(08:00), 주간브리핑(월 09:00)')


FALLBACK_ACTIONS = {
    '안정형 투자자': [
        '원금 보장이 되는 정기예금·적금 위주로 여유자금을 배치하세요.',
        '금리가 높은 특판 상품이 있는지 이번 주 상품 목록에서 확인해보세요.',
        '투자 비중을 늘리기보다 비상금부터 3~6개월치 확보해두는 게 우선이에요.',
    ],
    '안정추구형 투자자': [
        '예·적금 비중을 유지하되 일부는 우량 채권형 상품으로 분산해보세요.',
        '고금리 적금 특판을 확인하고 만기 스케줄을 분산해 재예치하세요.',
        '변동성이 큰 개별 종목보다 안정적인 배당주·ETF를 소액으로 검토해보세요.',
    ],
    '위험중립형 투자자': [
        '예금과 ETF를 절반씩 섞어 변동성과 수익률의 균형을 맞춰보세요.',
        '이번 주 금리 동향을 보고 예금 만기를 6개월~1년으로 조정할지 점검하세요.',
        '분산 투자 원칙을 유지하면서 관심 섹터 비중만 소폭 조정해보세요.',
    ],
    '적극투자형 투자자': [
        '관심 섹터 조정이 오면 분할 매수 기회로 활용해보세요.',
        '성장주 비중을 유지하되 일부는 현금성 자산으로 남겨 변동성에 대비하세요.',
        '이번 주 발표된 실적·업황 뉴스를 참고해 포트폴리오 비중을 재점검하세요.',
    ],
    '공격투자형 투자자': [
        '변동성이 커진 구간은 매수 기회일 수 있으나 리스크 관리 목표가는 꼭 설정하세요.',
        '단기 테마보다 실적이 뒷받침되는 종목 위주로 압축하는 것을 고려해보세요.',
        '레버리지·단기 매매 비중이 과도하지 않은지 이번 주 점검해보세요.',
    ],
    '': [
        '아직 금융성향 검사를 하지 않으셨다면 1분 검사로 나에게 맞는 전략을 확인해보세요.',
        '이번 주 금리 높은 예·적금 상품을 비교해보세요.',
        '작은 금액부터 시작해 투자 경험을 쌓아보는 것을 추천드려요.',
    ],
}

FALLBACK_TIPS = [
    '복리의 마법: 연 4% 적금을 10년 유지하면 원금의 약 1.48배가 됩니다. 지금 시작하는 것이 가장 빠른 방법이에요.',
    'ISA 계좌를 활용하면 예금 이자·배당·매매차익까지 비과세 혜택을 받을 수 있어요.',
    '비상금은 최소 생활비 3~6개월치를 파킹통장 등 유동성 높은 곳에 따로 보관하세요.',
    '연금저축·IRP는 세액공제 한도(연 900만원)를 먼저 채우는 것이 확정 수익률이 가장 높은 절세 전략이에요.',
    '분산 투자는 수익을 낮추는 게 아니라 변동성을 낮춰 오래 버틸 수 있게 해주는 전략입니다.',
]

RATE_KEYWORDS = ['기준금리', '한국은행', '금리', '연준', 'Fed']
FX_KEYWORDS = ['환율', '원/달러', '달러', '엔화']
MARKET_KEYWORDS = ['코스피', '코스닥', '증시', '주가지수']


def _pick_news_title(news_qs, keywords, exclude_titles=()):
    """조건에 맞는 원본(미절삭) 제목을 반환. 이미 다른 카테고리에서 쓴 제목은 제외."""
    for n in news_qs:
        if n['title'] in exclude_titles:
            continue
        if any(kw in n['title'] for kw in keywords):
            return n['title']
    return None


def _truncate(title):
    return title[:60] + ('…' if len(title) > 60 else '')


def _build_fallback_economy_summary(recent_news):
    used_titles = set()

    rate_title = _pick_news_title(recent_news, RATE_KEYWORDS)
    if rate_title:
        used_titles.add(rate_title)
    rate_desc = _truncate(rate_title) if rate_title else '이번 주 뚜렷한 금리 관련 이슈는 없었어요.'

    fx_title = _pick_news_title(recent_news, FX_KEYWORDS, used_titles)
    if fx_title:
        used_titles.add(fx_title)
    fx_desc = _truncate(fx_title) if fx_title else '환율은 큰 변동 없이 안정적인 흐름을 보였어요.'

    market_title = _pick_news_title(recent_news, MARKET_KEYWORDS, used_titles)
    market_desc = _truncate(market_title) if market_title else '증시는 관망세 속 특별한 이슈 없이 마감했어요.'
    return [
        {'title': '금리', 'desc': rate_desc},
        {'title': '환율', 'desc': fx_desc},
        {'title': '증시', 'desc': market_desc},
    ]


def _generate_weekly_briefing():
    """월요일 오전 9시 — 성향별 주간 AI 브리핑 생성."""
    try:
        import datetime, json, random, requests
        from django.conf import settings
        from news.models import News, WeeklyBriefing

        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())

        # 이미 생성된 경우 스킵
        if WeeklyBriefing.objects.filter(week_start=week_start).exists():
            logger.info('[scheduler] 이번 주 브리핑 이미 생성됨, 스킵')
            return

        # 최신 뉴스 20건 수집 (GMS 프롬프트용 5건 + 폴백 키워드 매칭용)
        recent_news = list(News.objects.order_by('-published_at')[:20].values('title', 'summary'))
        news_text = '\n'.join(f"- {n['title']}" for n in recent_news[:5])

        api_key = (getattr(settings, 'GMS_API_KEY', '') or '').strip()
        api_url = getattr(settings, 'GMS_API_URL', '')
        model = getattr(settings, 'GMS_MODEL', 'gpt-4o-mini')
        is_gemini_url = 'generativelanguage' in api_url or 'gemini' in api_url.lower()

        FINANCIAL_TYPES = ['', '안정형 투자자', '안정추구형 투자자', '위험중립형 투자자', '적극투자형 투자자', '공격투자형 투자자']

        for ft in FINANCIAL_TYPES:
            label = ft or '일반(비회원)'
            if ft:
                persona = f"사용자 성향: {ft}"
                action_prompt = f"{ft} 성향에 맞는 이번 주 금융 행동 추천 3가지"
            else:
                persona = "일반 사용자 (성향 미분류)"
                action_prompt = "모든 투자자에게 유용한 이번 주 금융 행동 추천 3가지"

            prompt = f"""당신은 금융 전문 AI입니다. 다음 이번 주 금융 뉴스를 바탕으로 주간 브리핑을 생성해주세요.

{persona}

## 이번 주 주요 뉴스
{news_text}

## 생성 내용 (JSON 형식으로만 출력):
{{
  "economy_summary": [
    {{"title": "금리", "desc": "한 줄 요약"}},
    {{"title": "환율", "desc": "한 줄 요약"}},
    {{"title": "증시", "desc": "한 줄 요약"}}
  ],
  "actions": [
    "{action_prompt} — 각 1문장",
    "두 번째 행동",
    "세 번째 행동"
  ],
  "tip": "이번 주 금융 TIP 1가지 (2문장 이내)"
}}"""

            try:
                if api_key and api_url:
                    if is_gemini_url:
                        resp = requests.post(
                            api_url,
                            params={'key': api_key},
                            headers={'Content-Type': 'application/json'},
                            json={
                                'contents': [{'parts': [{'text': prompt}]}],
                                'generationConfig': {'temperature': 0.4, 'maxOutputTokens': 512},
                            },
                            timeout=20,
                        )
                    else:
                        resp = requests.post(
                            api_url,
                            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                            json={'model': model, 'max_completion_tokens': 512,
                                  'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0.4},
                            timeout=20,
                        )
                    resp.raise_for_status()
                    payload = resp.json()
                    if is_gemini_url:
                        cands = payload.get('candidates', [])
                        parts = cands[0].get('content', {}).get('parts', [{}]) if cands else [{}]
                        text = parts[0].get('text', '') if parts else ''
                    else:
                        choices = payload.get('choices', [{}])
                        text = choices[0].get('message', {}).get('content', '') if choices else ''
                    # JSON 추출
                    import re
                    m = re.search(r'\{.*\}', text, re.DOTALL)
                    data = json.loads(m.group(0)) if m else {}
                else:
                    data = {}
            except Exception as e:
                logger.warning('[scheduler] 브리핑 GMS 호출 실패 (%s): %s', label, e)
                data = {}

            WeeklyBriefing.objects.update_or_create(
                week_start=week_start,
                financial_type=ft,
                defaults={
                    'economy_summary': data.get('economy_summary') or _build_fallback_economy_summary(recent_news),
                    'actions': data.get('actions') or FALLBACK_ACTIONS.get(ft, FALLBACK_ACTIONS['']),
                    'tip': data.get('tip') or random.choice(FALLBACK_TIPS),
                }
            )
            logger.info('[scheduler] 브리핑 생성 완료: %s', label)

        logger.info('[scheduler] 주간 브리핑 전체 생성 완료 (week_start=%s)', week_start)
    except Exception as exc:
        logger.error('[scheduler] 주간 브리핑 생성 실패: %s', exc)


def stop():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info('[scheduler] APScheduler 종료')
