# 트러블슈팅

개발하면서 실제로 막혔던 문제들을 정리했습니다.

---

## 1. GMS API 응답 파싱 오류 & Gemini 폴백 구현

뉴스 제목 번역이랑 추천 결과 만드는 데 GMS API를 쓰고 있었는데, 테스트하다 보니 GMS가 가끔 응답을 안 주는 경우가 있었어요. 그 상태에서 추천 탭 열면 500이 그냥 올라왔습니다.

파싱 쪽에서도 문제가 하나 있었는데, 번역된 제목을 JSON 배열로 돌려달라고 프롬프트를 짰는데 모델이 가끔 ` ```json ` 코드블록으로 감싸서 주더라고요. `json.loads()`가 당연히 실패하고, 그러면 번역 없이 영문 제목이 그대로 노출됐습니다.

GMS 장애 대비로는 Gemini 1.5 Flash를 폴백으로 연결했습니다. GMS는 OpenAI 호환 형식이라 구조가 비슷하긴 한데, Gemini는 요청 포맷이 달라서 `api_url`에 `generativelanguage`나 `gemini`가 있으면 분기하도록 처리했어요.

```python
is_gemini = 'generativelanguage' in api_url or 'gemini' in api_url.lower()
```

파싱 문제는 응답에서 마크다운 코드블록을 정규식으로 제거한 다음에 파싱하도록 했고, 그래도 실패하면 그냥 원문 쓰도록 예외 처리했습니다. 어떤 상황에서도 500은 안 올라오도록 방지하였습니다. 

```python
text = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`').strip()
```

---

## 2. yfinance 응답 구조 변경

종목 상세 페이지에서 관련 뉴스를 보여주는데, 어느 날 갑자기 뉴스 제목이 전부 비어서 표시됐습니다. 프론트 문제인가 싶어서 API 응답을 먼저 확인했는데 문제가 없었습니다. 파싱쪽을 확인 해보니 `stock.news`로 받아온 데이터를 그대로 찍어봤습니다.

```python
print(stock.news[0])  # 구조 확인
```

출력 결과를 보니까 `title` 키는 있는데 값이 빈 문자열이고, 대신 `content`라는 키 안에 `title`, `provider` 같은 필드들이 들어가 있었습니다. 기존에 잘 쓰던 `item['title']`이 항상 `''`를 반환하여 비어서 표시되었습니다. 

```python
# 기존 코드 — content 구조 변경 이후로 항상 ''
title = item.get('title', '')
```

`content` 키가 있으면 거기서 꺼내고, 없으면 기존 방식으로 폴백하도록 수정했습니다.

```python
content = item.get('content') or {}
title = content.get('title') or item.get('title') or ''
publisher = (content.get('provider') or {}).get('displayName') or item.get('publisher') or ''
```


---

## 3. timezone-naive datetime으로 인한 DB 저장 오류

`USE_TZ = True` 설정에서 Django ORM은 timezone-aware datetime만 받습니다. 근데 yfinance에서 받은 날짜, 엑셀에서 파싱한 날짜, feedparser RSS 날짜가 전부 timezone 정보가 없는 naive datetime이었어요. DB에 넣으려는 순간 `RuntimeWarning: DateTimeField received a naive datetime`이 뜨면서 저장이 안 됐습니다.

`USE_TZ = False`로 그냥 끄는 것도 잠깐 생각했는데, 그렇게 하면 서버 타임존이랑 DB 저장값이 뒤섞여서 더 큰 문제를 일으킨다고 판단하여 사용하지 않았습니다. 
결국 `django.utils.timezone.make_aware()`로 나오는 날짜를 전부 Asia/Seoul 기준으로 변환해서 저장하는 방식으로 통일했어요.

```python
from django.utils.timezone import make_aware

# yfinance 날짜
raw_dt = date.to_pydatetime() if hasattr(date, 'to_pydatetime') else date
if isinstance(raw_dt, datetime.datetime) and raw_dt.tzinfo is None:
    recorded_at = make_aware(raw_dt)

# 엑셀 날짜
def _parse_xlsx_date(value):
    if isinstance(value, datetime.datetime):
        return make_aware(value.replace(tzinfo=None))
    if isinstance(value, str):
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d'):
            try:
                return make_aware(datetime.datetime.strptime(value, fmt))
            except ValueError:
                continue
    return None
```

feedparser의 `struct_time`은 `time.mktime()`으로 timestamp 변환하고 `make_aware()` 적용했습니다.

---

## 4. FSS Finlife API 실시간 호출 불가

처음 설계할 때 상품 목록 조회할 때마다 FSS API를 실시간으로 부르려고 했습니다. 실제로 연결해보니 응답이 3~5초씩 걸렸고, 페이지 로딩이 확 느려지는 게 체감됐어요. 거기다 API 자체에서 필터링이나 정렬을 지원하지 않아서, "12개월짜리 금리 높은 순" 같은 걸 하려면 전체 데이터를 다 받아서 코드에서 직접 처리해야 했습니다.

관리자 전용 엔드포인트(`/products/save-products/`)를 따로 만들어서, 데이터 수집은 필요할 때 한 번만 하고 이후 서비스는 전부 DB에서 처리하는 방식으로 바꿨습니다. `update_or_create`로 중복 없이 upsert 처리하고, 이후 조회는 ORM으로 자유롭게 필터·정렬하면 됩니다.

```python
FinancialProduct.objects.update_or_create(
    fin_prdt_cd=item.get('fin_prdt_cd', ''),
    defaults={ 'bank_name': ..., 'product_name': ..., ... }
)
```

---

## 5. JWT 로그아웃 후 토큰 재사용 문제

처음에 로그아웃을 프론트에서 localStorage 지우는 것만으로 처리했습니다. 
이미 발급된 Access 토큰은 서버 입장에선 여전히 유효하기 때문에, 탈취된 토큰이 있으면 로그아웃 후에도 API를 계속 쓸 수 있는 상태가 됩니다.

SimpleJWT의 Token Blacklist를 적용해서 로그아웃 시 Refresh 토큰을 블랙리스트에 올리도록 했습니다. Refresh가 막히면 Access가 만료된 이후에 갱신이 안 되고, Access 토큰 자체는 유효기간을 2시간으로 짧게 잡아서 노출 리스크를 최대한 줄였습니다.

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception as e:
        logger.warning('logout blacklist 실패 (user=%s): %s', request.user.id, e)
    return Response({'message': '로그아웃 되었습니다.'})
```

블랙리스트 등록이 실패해도 로그아웃 응답은 200으로 주고 로그만 남겨 개발자에게 문제 발생상황을 공유합니다. 

---

## 6. APScheduler 개발 서버에서 중복 실행

`AppConfig.ready()`에 APScheduler를 등록했는데, Django의 `runserver`가 개발 환경에서 자동 reload를 위해 프로세스를 두 번 띄웁니다. 그러면 스케줄러도 두 번 등록돼서 뉴스 브리핑 생성 잡이 중복으로 실행되는 상황이 생겼어요.

`AppConfig.ready()` 진입할 때 `RUN_MAIN` 환경변수를 확인해서, reload용 서브 프로세스에서는 스케줄러를 등록하지 않도록 처리했습니다.

```python
import os

class NewsConfig(AppConfig):
    def ready(self):
        if os.environ.get('RUN_MAIN') != 'true':
            return
        from config.scheduler import start
        start()
```
