import datetime
import html
import re
import time

import feedparser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import make_aware
from rest_framework.decorators import api_view, permission_classes
from config.pagination import StandardPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import News, WeeklyBriefing
from .serializers import NewsSerializer

# 금융 관련 키워드 — 하나라도 포함되면 통과
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


_FINANCE_KEYWORDS_LOWER = {kw.lower() for kw in FINANCE_KEYWORDS}


def _is_finance_related(title, summary=''):
    text = (title + ' ' + summary).lower()
    return any(kw in text for kw in _FINANCE_KEYWORDS_LOWER)


# 한국 금융/경제 뉴스 RSS 피드 목록 (API 키 불필요)
# 진짜 경제/증권/재테크 섹션만 사용 — '전체뉴스' 등 잡다한 카테고리 피드는 제외
FINANCE_RSS_FEEDS = [
    ('한국경제',  'https://www.hankyung.com/feed/economy'),
    ('한국경제',  'https://www.hankyung.com/feed/finance'),
    ('매일경제',  'https://www.mk.co.kr/rss/30100041/'),   # 경제
    ('매일경제',  'https://www.mk.co.kr/rss/50200011/'),   # 증권
    ('매일경제',  'https://www.mk.co.kr/rss/40200003/'),   # 머니 앤 리치스(재테크)
    ('연합뉴스',  'https://www.yna.co.kr/rss/economy.xml'),
    ('연합뉴스',  'https://www.yna.co.kr/rss/market.xml'),
]

# 일부 언론사는 기본 User-Agent 요청을 403으로 차단하므로 브라우저로 위장
RSS_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'
)


def _parse_struct_time(st):
    """feedparser struct_time → timezone-aware datetime (Asia/Seoul)"""
    if not st:
        return None
    try:
        naive = datetime.datetime.fromtimestamp(time.mktime(st))
        return make_aware(naive)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def import_news(request):
    """한국 금융/경제 RSS 피드에서 뉴스를 수집합니다."""
    created = updated = skipped = 0
    errors = []

    feeds = FINANCE_RSS_FEEDS

    for publisher, feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url, request_headers={'User-Agent': RSS_USER_AGENT})
        except Exception as exc:
            errors.append(f'{publisher}: {exc}')
            continue

        for entry in parsed.entries:
            title = html.unescape((getattr(entry, 'title', '') or '').strip())
            if not title:
                skipped += 1
                continue

            link = getattr(entry, 'link', '') or ''
            summary = (
                getattr(entry, 'summary', '')
                or getattr(entry, 'description', '')
                or ''
            ).strip()
            summary = html.unescape(re.sub(r'<[^>]+>', '', summary))[:500]

            # 금융 관련 기사만 저장
            if not _is_finance_related(title, summary):
                skipped += 1
                continue

            published_at = _parse_struct_time(getattr(entry, 'published_parsed', None))
            if not published_at:
                published_at = _parse_struct_time(getattr(entry, 'updated_parsed', None))

            if link:
                obj, flag = News.objects.update_or_create(
                    url=link,
                    defaults={
                        'title': title[:255],
                        'summary': summary,
                        'publisher': publisher,
                        'published_at': published_at,
                    }
                )
            else:
                obj, flag = News.objects.update_or_create(
                    title=title[:255],
                    defaults={
                        'summary': summary,
                        'url': link,
                        'publisher': publisher,
                        'published_at': published_at,
                    }
                )

            if flag:
                created += 1
            else:
                updated += 1

    return Response({
        'feeds_processed': len(feeds),
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'errors': errors,
    })


@api_view(['GET'])
def news_list(request):
    items = News.objects.all().order_by('-published_at')
    paginator = StandardPagination()
    page = paginator.paginate_queryset(items, request)
    serializer = NewsSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def news_detail(request, news_id):
    item = get_object_or_404(News, pk=news_id)
    serializer = NewsSerializer(item)
    return Response(serializer.data)


@api_view(['GET'])
def weekly_briefing(request):
    """이번 주 AI 브리핑 반환. 로그인 사용자는 성향 맞춤, 비로그인은 일반."""
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())  # 이번 주 월요일

    financial_type = ''
    if request.user.is_authenticated:
        financial_type = getattr(request.user, 'financial_type', '') or ''

    briefing = (
        WeeklyBriefing.objects.filter(week_start=week_start, financial_type=financial_type).first()
        or WeeklyBriefing.objects.filter(week_start=week_start, financial_type='').first()
    )

    if not briefing:
        return Response(None)

    return Response({
        'week_start': briefing.week_start,
        'financial_type': briefing.financial_type or '일반',
        'economy_summary': briefing.economy_summary,
        'actions': briefing.actions,
        'tip': briefing.tip,
        'created_at': briefing.created_at,
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def generate_briefing(request):
    """관리자 전용 — 이번 주 AI 브리핑 즉시 생성 (월요일 아니어도 강제 실행)."""
    from config.scheduler import _generate_weekly_briefing
    import datetime
    from .models import WeeklyBriefing

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())

    force = request.data.get('force', False)
    if force:
        WeeklyBriefing.objects.filter(week_start=week_start).delete()

    try:
        _generate_weekly_briefing()
        count = WeeklyBriefing.objects.filter(week_start=week_start).count()
        return Response({'status': 'ok', 'week_start': str(week_start), 'created': count})
    except Exception as e:
        return Response({'status': 'error', 'detail': str(e)}, status=500)
