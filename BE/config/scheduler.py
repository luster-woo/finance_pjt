"""
APScheduler 기반 주기적 데이터 수집 스케줄러.

등록된 작업:
  - collect_news          : 매 6시간마다  금융/경제 RSS 뉴스 수집
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
        import feedparser
        from news.models import News

        FINANCE_RSS_FEEDS = [
            ('한국경제',      'https://www.hankyung.com/feed/finance'),
            ('한국경제',      'https://www.hankyung.com/feed/stock'),
            ('매일경제',      'https://www.mk.co.kr/rss/50100032/'),
            ('매일경제',      'https://www.mk.co.kr/rss/40300001/'),
            ('연합뉴스',      'https://www.yna.co.kr/RSS/economy.xml'),
            ('연합뉴스',      'https://www.yna.co.kr/RSS/market.xml'),
            ('이데일리',      'https://rss.edaily.co.kr/edaily/section/economy.xml'),
            ('파이낸셜뉴스',  'https://www.fnnews.com/rss/fn_realnews_010100.xml'),
        ]

        import datetime

        def _parse_st(st):
            if not st:
                return None
            try:
                return datetime.datetime.fromtimestamp(time.mktime(st))
            except Exception:
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
                parsed = feedparser.parse(url)
            except Exception:
                continue
            for entry in parsed.entries:
                title = (getattr(entry, 'title', '') or '').strip()
                if not title:
                    continue
                link = getattr(entry, 'link', '') or ''
                summary = re.sub(r'<[^>]+>', '', (
                    getattr(entry, 'summary', '') or getattr(entry, 'description', '') or ''
                ).strip())[:500]
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

    # 뉴스: 매 6시간 (00:00, 06:00, 12:00, 18:00 KST)
    _scheduler.add_job(
        _collect_news,
        trigger=IntervalTrigger(hours=6),
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
    logger.info('[scheduler] APScheduler 시작 — 뉴스(6h), 주식(평일 17:00), 원자재(08:00), 주간브리핑(월 09:00)')


def _generate_weekly_briefing():
    """월요일 오전 9시 — 성향별 주간 AI 브리핑 생성."""
    try:
        import datetime, json, requests
        from django.conf import settings
        from news.models import News, WeeklyBriefing

        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())

        # 이미 생성된 경우 스킵
        if WeeklyBriefing.objects.filter(week_start=week_start).exists():
            logger.info('[scheduler] 이번 주 브리핑 이미 생성됨, 스킵')
            return

        # 최신 뉴스 5건 수집
        recent_news = list(News.objects.order_by('-published_at')[:5].values('title', 'summary'))
        news_text = '\n'.join(f"- {n['title']}" for n in recent_news)

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
                    'economy_summary': data.get('economy_summary', [
                        {'title': '금리', 'desc': '이번 주 금리 동향 정보를 불러오는 중입니다.'},
                        {'title': '환율', 'desc': '환율 정보를 준비 중입니다.'},
                        {'title': '증시', 'desc': '증시 정보를 준비 중입니다.'},
                    ]),
                    'actions': data.get('actions', ['최신 뉴스를 확인하고 투자 계획을 점검해보세요.']),
                    'tip': data.get('tip', '꾸준한 소액 투자가 장기적으로 가장 안전한 자산 형성 방법입니다.'),
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
