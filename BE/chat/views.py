from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from financial_tests.services.recommendation_service import _gms_raw_call, _extract_text_from_response

SYSTEM_PROMPT = """당신은 FinFit의 AI 금융 상담사입니다.
사회초년생을 위한 친절하고 쉬운 금융 조언을 제공합니다.

답변 원칙:
- 한국어로 간결하게 (3~5문장 이내)
- 전문 용어는 쉽게 설명
- 구체적인 수치나 예시 포함
- 투자 권유보다는 중립적 정보 제공
- 불확실한 내용은 전문가 상담 권유

다룰 수 있는 주제: 예금·적금, 주식·ETF, 카드 혜택, 세금·절세, 연금, 청약, 환율, 금융 용어 설명 등"""


@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    """AI 금융 챗봇 — 자유 형식 질문에 답변"""
    message = request.data.get('message', '').strip()
    history = request.data.get('history', [])  # [{role, content}, ...]

    if not message:
        return Response({'detail': '메시지를 입력해주세요.'}, status=400)

    # 대화 히스토리 포함 프롬프트 구성
    conversation = SYSTEM_PROMPT + '\n\n'
    for h in history[-6:]:  # 최근 6턴만 포함 (토큰 절약)
        role = '사용자' if h.get('role') == 'user' else 'AI'
        conversation += f'{role}: {h.get("content", "")}\n'
    conversation += f'사용자: {message}\nAI:'

    try:
        payload = _gms_raw_call(conversation, max_tokens=512)
        reply = _extract_text_from_response(payload).strip()
        if not reply:
            reply = '죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요.'
    except Exception:
        reply = '죄송합니다. 현재 AI 서비스에 연결할 수 없습니다.'

    return Response({'reply': reply})
