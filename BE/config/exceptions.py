import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    DRF 기본 핸들러를 먼저 실행하고,
    처리되지 않은 예외(500)는 로그를 남긴 뒤 일관된 JSON으로 응답합니다.
    """
    response = exception_handler(exc, context)

    if response is None:
        view = context.get('view', '')
        logger.error(
            'Unhandled exception in %s: %s',
            view.__class__.__name__ if view else '?',
            exc,
            exc_info=True,
        )
        return Response(
            {'detail': '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'},
            status=500,
        )

    return response
