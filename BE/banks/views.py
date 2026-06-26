import requests as http_requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.db.models import Q
from .models import Bank
from .serializers import BankSerializer


@api_view(['GET'])
def bank_list(request):
    banks = Bank.objects.all()
    serializer = BankSerializer(banks, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def route_to_bank(request):
    """Kakao Mobility API 프록시 - 멀티캠퍼스 역삼 → 선택 은행 경로"""
    dest_lat = request.GET.get('dest_lat')
    dest_lng = request.GET.get('dest_lng')
    origin_lat = request.GET.get('origin_lat', '37.5012743')
    origin_lng = request.GET.get('origin_lng', '127.039585')

    if not dest_lat or not dest_lng:
        return Response({'error': '목적지 좌표(dest_lat, dest_lng)가 필요합니다.'}, status=400)

    kakao_key = settings.KAKAO_REST_API_KEY
    headers = {'Authorization': f'KakaoAK {kakao_key}'}
    params = {
        'origin': f'{origin_lng},{origin_lat}',
        'destination': f'{dest_lng},{dest_lat}',
        'priority': 'RECOMMEND',
    }

    try:
        resp = http_requests.get(
            'https://apis-navi.kakaomobility.com/v1/directions',
            headers=headers,
            params=params,
            timeout=10,
        )
    except Exception as e:
        return Response({'error': f'경로 요청 실패: {e}'}, status=503)

    if resp.status_code != 200:
        return Response({'error': f'Kakao Mobility 오류 ({resp.status_code})'}, status=502)

    data = resp.json()
    routes = data.get('routes', [])
    if not routes or routes[0].get('result_code') != 0:
        return Response({'vertices': [], 'distance': 0, 'duration': 0,
                         'error': routes[0].get('result_msg', '경로 없음') if routes else '경로 없음'})

    vertices = []
    for section in routes[0].get('sections', []):
        for road in section.get('roads', []):
            v = road.get('vertexes', [])
            for i in range(0, len(v) - 1, 2):
                vertices.append({'lng': v[i], 'lat': v[i + 1]})

    summary = routes[0].get('summary', {})
    return Response({
        'vertices': vertices,
        'distance': summary.get('distance', 0),   # 미터
        'duration': summary.get('duration', 0),   # 초
    })


@api_view(['GET'])
def bank_nearby(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    if lat is None or lng is None:
        return Response({'detail': 'lat 및 lng 파라미터가 필요합니다.'}, status=400)

    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return Response({'detail': 'lat 및 lng는 숫자여야 합니다.'}, status=400)

    radius = 0.05
    banks = Bank.objects.filter(
        latitude__gte=lat-radius,
        latitude__lte=lat+radius,
        longitude__gte=lng-radius,
        longitude__lte=lng+radius,
    )
    serializer = BankSerializer(banks, many=True)
    return Response(serializer.data)
