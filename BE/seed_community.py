# -*- coding: utf-8 -*-
"""시연용 커뮤니티 더미 데이터 생성 스크립트"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import random
from django.contrib.auth import get_user_model
from community.models import CommunityPost, Comment, PostLike, CommentLike
from stocks.models import Stock

User = get_user_model()

# ─── 닉네임 업데이트 ───────────────────────────────────────────────
NICKNAMES = [
    '주식왕김씨', '불곰투자자', '코스피지킴이', '배당주매니아', '반도체덕후',
    '이차전지고수', '장기투자이씨', '절약왕박씨', 'ETF전도사', '금융초보탈출',
    '성장주헌터', '재테크여신', '퀀트투자자', '가치투자최씨', '묻어두기달인',
    '단타왕입니다', '스윙트레이더', '해외주식러', '달러사냥꾼', '인플레방어자',
    '차트분석가K', '펀더멘털러', '배당귀족팬', 'KODEX전문가', '공매도반대',
    '개미연합회장', '우량주수집가', '포트폴리오신', '리밸런싱고수', '연금저축러',
    '테마주사냥꾼', '무지성장기투자', '분산투자신봉자', '손절못하는개미', '존버마스터',
]

users = list(User.objects.filter(nickname__isnull=True).order_by('id')[:35])
for i, u in enumerate(users):
    if i < len(NICKNAMES):
        u.nickname = NICKNAMES[i]
        u.save(update_fields=['nickname'])
print(f'[1] 닉네임 {len(users)}명 업데이트')

# ─── 주식 목록 ─────────────────────────────────────────────────────
stocks = list(Stock.objects.all()[:20])
named_users = list(User.objects.exclude(nickname__startswith='dummy').order_by('id')) + \
              [u for u in User.objects.filter(nickname__in=NICKNAMES)]

def rand_user():
    return random.choice(named_users) if named_users else User.objects.order_by('?').first()

# ─── 게시글 + 댓글 데이터 ──────────────────────────────────────────
POSTS = [
    {
        'stock': '삼성전자',
        'title': '삼성전자 지금 들어가도 될까요?',
        'content': '현재 주가가 많이 내려왔는데, 장기적으로 보면 지금이 매수 타이밍일 것 같기도 하고... 반도체 사이클 생각하면 아직 더 빠질 수도 있고. 여러분 의견 궁금합니다.',
        'comments': [
            ('불곰투자자', '저는 분할매수 중입니다. 한 번에 다 사지 말고 나눠서 사는 게 심리적으로 편해요.'),
            ('반도체덕후', 'HBM 수요가 계속 늘고 있어서 하반기엔 회복될 것 같아요. 실적이 뒷받침되면 오를 거라 봅니다.'),
            ('단타왕입니다', '단기는 모르겠는데 3년 이상 보면 지금 가격도 나쁘지 않다고 생각해요.'),
            ('금융초보탈출', '저도 궁금한데 PER이 얼마나 되나요?', True),  # 대댓글 표시
            ('차트분석가K', '기술적으로 보면 지지선에서 반등 시도 중입니다. 이번 주 종가가 중요할 것 같아요.'),
        ],
        'likes': 23,
    },
    {
        'stock': 'SK하이닉스',
        'title': 'SK하이닉스 HBM3E 수율 개선 소식, 어떻게 보세요?',
        'content': '오늘 뉴스에서 SK하이닉스 HBM3E 수율이 많이 개선됐다는 기사가 나왔던데, 엔비디아 공급 늘어나면 주가에 긍정적이지 않을까요? AI 서버 수요도 계속 증가 중이고.',
        'comments': [
            ('이차전지고수', 'AI 인프라 투자가 계속되는 한 HBM 수요는 꺾이지 않을 것 같아요. 장기 보유 중입니다.'),
            ('퀀트투자자', '수율 개선 + ASP 상승 두 가지 동시에 오면 이익이 폭발적으로 늘 수 있어요.'),
            ('재테크여신', '저도 SK하이닉스 조금 담고 있는데 요즘 마음이 편해요 ㅎㅎ'),
            ('주식왕김씨', '엔비디아 실적 발표 때까지 홀딩이 맞는 것 같아요.'),
            ('묻어두기달인', '저는 5년 보유 목표로 사두고 잊어버리기 전략입니다 ㅋㅋ'),
        ],
        'likes': 41,
    },
    {
        'stock': 'NAVER',
        'title': '네이버 지금 과매도 구간 아닌가요?',
        'content': '최근 많이 빠지면서 PBR이 역사적 저점 근처인데, AI 사업도 착실하게 진행되고 있고 하이퍼클로바X도 기업 B2B 시장에서 반응이 좋다던데. 저평가 구간인 것 같아서 담고 있는데 여러분은 어떻게 생각하세요?',
        'comments': [
            ('가치투자최씨', '저도 같은 생각입니다. 클라우드·AI 부문 성장성을 감안하면 지금 가격은 상당히 매력적이에요.'),
            ('해외주식러', '미국 빅테크랑 비교하면 밸류에이션 할인이 너무 큰 것 같긴 해요.'),
            ('ETF전도사', 'TIGER 미디어컨텐츠 ETF에도 담겨 있어서 간접적으로 보유 중이에요.'),
            ('스윙트레이더', '단기로 보면 70만원 지지 여부가 중요할 것 같아요.'),
        ],
        'likes': 17,
    },
    {
        'stock': '카카오',
        'title': '카카오 이번 주 급락 이유가 뭔가요?',
        'content': '뚜렷한 악재도 없는 것 같은데 갑자기 많이 빠졌네요. 제가 뭔가 놓친 소식이 있나요? 아니면 그냥 시장 전반적인 매도 분위기인가요?',
        'comments': [
            ('공매도반대', '공매도 세력이 많이 치고 있는 것 같아요. 기관 순매도 지속 중이에요.'),
            ('코스피지킴이', '카카오페이 지분 문제랑 SM엔터 관련 소송 이슈가 아직 완전히 해소 안 됐어요.'),
            ('배당주매니아', '저는 이미 손절했어요... 카카오는 주주환원 의지가 너무 부족해 보여서요.'),
            ('차트분석가K', '차트상 중장기 지지선이 무너졌어요. 반등 시도는 있겠지만 추세 전환에 시간이 걸릴 것 같아요.'),
            ('단타왕입니다', '오히려 이런 급락이 단타 기회일 수도 있는데, 변동성이 너무 크긴 해요.'),
        ],
        'likes': 29,
    },
    {
        'stock': '삼성SDI',
        'title': '이차전지 섹터 지금 바닥인가요? 삼성SDI 의견 부탁드려요',
        'content': '전기차 수요 둔화 이슈로 이차전지 주들이 많이 빠졌는데, 삼성SDI는 BMW, 스텔란티스 같은 프리미엄 고객사 위주라 상대적으로 안전하지 않을까요? 배터리 원가도 계속 낮아지고 있고.',
        'comments': [
            ('이차전지고수', '전고체 배터리 상용화 타임라인이 중요한 변수예요. 삼성SDI가 전고체 분야에서 앞서 있어서 저는 긍정적으로 보고 있어요.'),
            ('장기투자이씨', '5~10년 보고 투자하면 이차전지는 결국 오를 것 같아요. 지금 가격도 나쁘지 않다고 봐요.'),
            ('퀀트투자자', 'EV 침투율이 30% 넘어가는 시점부터 수요가 다시 폭발적으로 늘 겁니다. 2026-2027년 기대하고 있어요.'),
            ('절약왕박씨', '저는 이차전지 ETF로 분산투자 중이에요. 개별 종목은 변동성이 너무 커서...'),
        ],
        'likes': 35,
    },
    {
        'stock': None,
        'title': '사회초년생 첫 투자, 어디서 시작하면 좋을까요?',
        'content': '취업 후 첫 월급 받았는데 투자를 시작하고 싶어요. 예적금은 이미 하고 있고, 주식이나 ETF로 투자를 시작하려고 하는데 어디서 어떻게 시작해야 할지 막막합니다. 선배 투자자 분들의 조언 부탁드려요!',
        'comments': [
            ('ETF전도사', 'S&P500 ETF(Tiger 미국S&P500이나 ACE 미국S&P500)부터 시작하시는 걸 추천드려요. 개별 종목보다 훨씬 안정적이에요.'),
            ('장기투자이씨', '처음엔 무조건 분산투자입니다. 한 종목에 몰빵하면 멘탈 나가요 ㅋㅋ'),
            ('금융초보탈출', '저도 작년에 시작했는데 처음엔 작은 금액으로 먼저 경험 쌓는 게 좋아요.'),
            ('절약왕박씨', '월급의 10~20%만 투자하고 나머지는 비상금으로 두세요. 갑자기 돈 필요할 때 주식 손절하는 게 제일 아까워요.'),
            ('재테크여신', '연금저축펀드나 IRP로 세액공제 혜택 받으면서 ETF 담는 것도 강력 추천드려요!'),
            ('우량주수집가', '삼성전자, SK하이닉스 같은 국내 대형주로 시작해보는 것도 나쁘지 않아요. 익숙한 기업이라 공부하기도 편하거든요.'),
        ],
        'likes': 58,
    },
    {
        'stock': None,
        'title': '요즘 금리 인하 기대감에 어떤 섹터 준비하시나요?',
        'content': '연준 금리 인하 사이클이 시작되면 보통 어떤 섹터가 수혜를 받나요? 리츠나 채권 쪽이 먼저 반응한다는 얘기도 있고, 성장주 밸류에이션도 높아진다고 하는데. 다들 어떻게 준비 중이신지 궁금합니다.',
        'comments': [
            ('달러사냥꾼', '금리 인하 기대감이 생기면 원/달러 환율도 떨어지는 경향이 있어서 달러 비중 좀 줄이고 있어요.'),
            ('배당주매니아', '금리 인하 수혜주는 역시 리츠 아닐까요? 배당수익률이 매력적이라 자금 유입될 것 같아요.'),
            ('성장주헌터', '테크, 바이오 같은 성장주들이 할인율 낮아지면서 밸류 올라갑니다. 나스닥 ETF 비중 늘리고 있어요.'),
            ('인플레방어자', '금리 인하 초기엔 경기 침체 우려도 같이 오니까 너무 공격적으로 가기보다 헬스케어나 필수소비재도 섞어두세요.'),
            ('가치투자최씨', '섹터 로테이션 타이밍 맞추기가 정말 어렵더라고요. 그냥 전체 시장 인덱스로 버티는 게 제일 편한 것 같아요 ㅎㅎ'),
        ],
        'likes': 44,
    },
    {
        'stock': '현대차',
        'title': '현대차 미국 공장 투자 효과, 주가에 얼마나 반영될까요?',
        'content': '현대차가 미국에 대규모 공장 투자하고 IRA 혜택도 받게 되면서 미국 시장에서 경쟁력이 많이 올라갔잖아요. 지금 주가가 이런 기대감을 제대로 반영하고 있는 건지, 아니면 아직 저평가인지 궁금합니다.',
        'comments': [
            ('주식왕김씨', '현대차 PER이 글로벌 완성차 대비 여전히 낮아요. 코리아 디스카운트 포함해도 저평가 구간인 것 같아요.'),
            ('펀더멘털러', '제네시스 브랜드 고급화 전략이 마진율 개선에 크게 기여하고 있어요. 영업이익률이 꾸준히 올라가고 있다는 게 포인트입니다.'),
            ('해외주식러', '토요타, BMW 대비 PER 디스카운트가 너무 크긴 해요. 전기차 전환 속도만 빨라지면 리레이팅 가능성 충분히 있다고 봐요.'),
            ('묻어두기달인', '배당도 꾸준히 주고 자사주도 사주고 있어서 주주환원 측면에서도 좋아지고 있어요.'),
        ],
        'likes': 31,
    },
    {
        'stock': 'LG화학',
        'title': 'LG화학 주가 너무 많이 빠진 것 같은데 저만 그런가요?',
        'content': 'LG에너지솔루션 상장 이후로 계속 소외받는 것 같아서... 화학 본업도 업황이 안 좋긴 한데, 이 정도면 너무 싸지 않나요? 자회사 가치만 봐도 할인이 심한 것 같아요.',
        'comments': [
            ('이차전지고수', 'LG에너지솔루션 지분 가치랑 화학 사업 감안하면 NAV 대비 엄청난 할인이죠. 지주사 할인이 너무 심해요.'),
            ('퀀트투자자', '화학 사이클이 돌아오면 같이 오를 텐데, 언제 돌아올지가 문제예요. 인내심 게임입니다.'),
            ('배당귀족팬', '배당이 약한 게 아쉽지만... 밸류에이션만 보면 진짜 저평가인 건 맞아요.'),
        ],
        'likes': 19,
    },
    {
        'stock': None,
        'title': '분산투자 vs 집중투자, 여러분은 어떤 스타일인가요?',
        'content': '워런 버핏처럼 잘 아는 종목 몇 개에 집중하는 게 맞는지, 아니면 ETF처럼 최대한 분산하는 게 맞는지 항상 고민이에요. 개인투자자 입장에서 어떤 전략이 더 현실적일까요?',
        'comments': [
            ('포트폴리오신', '개인투자자가 워런 버핏처럼 하기는 정보 비대칭 때문에 현실적으로 어렵다고 생각해요. 코어는 ETF, 일부만 개별주 가는 게 현실적이에요.'),
            ('리밸런싱고수', '저는 코어-새틀라이트 전략입니다. 70%는 인덱스 ETF, 30%는 확신 있는 개별주로 운용해요.'),
            ('연금저축러', '경험이 쌓이면서 자연스럽게 분산 쪽으로 가게 되더라고요. 집중투자는 멘탈 관리가 너무 힘들어요.'),
            ('테마주사냥꾼', '저는 반대로 확신 있는 테마에 집중하는 편이에요. 분산하면 수익도 분산되거든요 ㅋㅋ'),
            ('무지성장기투자', '그냥 S&P500이랑 코스피200 매달 적립식으로 사는 게 제일 스트레스 없어요 ㅎ'),
            ('분산투자신봉자', '1년에 한 번 리밸런싱하면서 비중 맞추는 것만 해도 꽤 좋은 성과 나오더라고요.'),
        ],
        'likes': 62,
    },
]

# ─── 기존 더미 게시글 삭제 후 새로 생성 ───────────────────────────
CommunityPost.objects.filter(title__in=[p['title'] for p in POSTS]).delete()

created_posts = 0
created_comments = 0

# 닉네임→User 맵
nick_map = {u.nickname: u for u in User.objects.exclude(nickname__isnull=True).exclude(nickname='')}
all_users = list(User.objects.order_by('?')[:50])

stock_map = {s.stock_name: s for s in Stock.objects.all()}

for pd in POSTS:
    # 게시글 작성자 랜덤 배정
    author = random.choice(all_users)

    stock_obj = None
    if pd['stock']:
        # 주식명으로 찾기
        for sn, so in stock_map.items():
            if pd['stock'] in sn:
                stock_obj = so
                break

    post = CommunityPost.objects.create(
        user=author,
        stock=stock_obj,
        category='토론',
        title=pd['title'],
        content=pd['content'],
        likes_count=pd['likes'],
        view_count=random.randint(pd['likes'] * 2, pd['likes'] * 8),
    )

    # 좋아요 실제 PostLike 생성
    like_users = random.sample(all_users, min(pd['likes'], len(all_users)))
    PostLike.objects.bulk_create(
        [PostLike(user=u, post=post) for u in like_users],
        ignore_conflicts=True,
    )

    created_posts += 1

    # 댓글 생성
    for cidx, cdata in enumerate(pd['comments']):
        is_reply = len(cdata) == 3 and cdata[2] is True
        nick = cdata[0]
        content = cdata[1]

        comment_user = nick_map.get(nick, random.choice(all_users))

        if is_reply and created_comments > 0:
            # 마지막 댓글에 대댓글
            parent_comment = Comment.objects.filter(post=post).last()
            c = Comment.objects.create(
                post=post, user=comment_user, parent=parent_comment, content=content
            )
        else:
            c = Comment.objects.create(
                post=post, user=comment_user, parent=None, content=content
            )

        # 댓글 좋아요 (2~8개)
        n_likes = random.randint(2, 8)
        like_users_c = random.sample(all_users, min(n_likes, len(all_users)))
        CommentLike.objects.bulk_create(
            [CommentLike(user=u, comment=c) for u in like_users_c],
            ignore_conflicts=True,
        )
        c.likes_count = n_likes
        c.save(update_fields=['likes_count'])

        created_comments += 1

print(f'[2] 게시글 {created_posts}개 생성')
print(f'[3] 댓글 {created_comments}개 생성')
print('완료!')
