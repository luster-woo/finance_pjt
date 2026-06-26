from django.shortcuts import get_object_or_404
from django.utils import timezone
import requests

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import FinancialProduct, FinancialProductOption
from .serializers import FinancialProductSerializer
from favorites.models import Favorite, SubscribedProduct, RecentProduct


@api_view(['GET'])
def product_list(request):
    product_type = request.GET.get('type')
    products = FinancialProduct.objects.all()

    if product_type:
        products = products.filter(product_type=product_type)

    serializer = FinancialProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def product_detail(request, product_id):
    product = get_object_or_404(FinancialProduct, pk=product_id)
    serializer = FinancialProductSerializer(product)
    return Response(serializer.data)


@api_view(['GET'])
def product_search(request):
    keyword = request.GET.get('keyword', '')
    products = FinancialProduct.objects.filter(product_name__icontains=keyword)
    serializer = FinancialProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def product_compare(request):
    raw_ids = request.GET.get('ids', '')
    try:
        product_ids = [
            int(product_id)
            for product_id in raw_ids.split(',')
            if product_id.strip()
        ]
    except ValueError:
        return Response({'detail': 'ids는 쉼표로 구분된 숫자여야 합니다.'}, status=400)

    if not product_ids:
        return Response({'detail': 'ids 쿼리 파라미터가 필요합니다.'}, status=400)

    products = (
        FinancialProduct.objects
        .filter(id__in=product_ids)
        .prefetch_related('financialproductoption_set')
    )
    product_map = {product.id: product for product in products}

    result = []
    for product_id in product_ids:
        product = product_map.get(product_id)
        if not product:
            continue

        options = list(product.financialproductoption_set.all())
        interest_rates = [option.interest_rate for option in options if option.interest_rate is not None]
        max_rates = [option.max_interest_rate for option in options if option.max_interest_rate is not None]
        periods = [option.save_trm for option in options]

        result.append({
            'id': product.id,
            'product_name': product.product_name,
            'bank_name': product.bank_name,
            'interest_rate': max(interest_rates, default=None),
            'max_interest_rate': max(max_rates, default=None),
            'periods': sorted(periods),
        })

    return Response(result)


@api_view(['POST'])
def product_calculate(request):
    try:
        amount = float(request.data.get('amount'))
        rate = float(request.data.get('rate'))
        months = int(request.data.get('months'))
    except (TypeError, ValueError):
        return Response({'detail': 'amount, rate, months는 숫자여야 합니다.'}, status=400)

    if amount <= 0 or rate < 0 or months <= 0:
        return Response({'detail': 'amount와 months는 양수, rate는 0 이상이어야 합니다.'}, status=400)

    interest = round(amount * (rate / 100) * (months / 12))
    principal = round(amount)

    return Response({
        'principal': principal,
        'interest': interest,
        'total': principal + interest,
    })


def _fetch_finlife(url):
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:
        return None, None, str(exc)
    except ValueError:
        return None, None, 'API 응답이 JSON이 아닙니다.'

    result = payload.get('result', {})
    base_list = result.get('baseList', [])
    option_list = result.get('optionList', [])
    if not isinstance(base_list, list):
        return None, None, f'예상치 못한 응답 형태: {list(result.keys())}'
    return base_list, option_list, None


def _upsert_products(base_list, option_list, product_type):
    created = updated = 0
    for item in base_list:
        _, flag = FinancialProduct.objects.update_or_create(
            fin_prdt_cd=item.get('fin_prdt_cd', ''),
            defaults={
                'bank_code': item.get('fin_co_no', ''),
                'product_type': product_type,
                'bank_name': item.get('kor_co_nm', ''),
                'product_name': item.get('fin_prdt_nm', ''),
                'join_way': item.get('join_way', ''),
                'target_user': item.get('join_member', ''),
                'description': item.get('etc_note', ''),
                'special_condition': item.get('spcl_cnd', ''),
            }
        )
        if flag:
            created += 1
        else:
            updated += 1

    options_created = 0
    for option in option_list:
        try:
            product = FinancialProduct.objects.get(fin_prdt_cd=option['fin_prdt_cd'])
        except FinancialProduct.DoesNotExist:
            continue
        save_trm = option.get('save_trm')
        if save_trm is None:
            continue
        try:
            save_trm = int(save_trm)
        except (ValueError, TypeError):
            continue
        FinancialProductOption.objects.update_or_create(
            product=product,
            save_trm=save_trm,
            defaults={
                'interest_rate': option.get('intr_rate'),
                'max_interest_rate': option.get('intr_rate2'),
            }
        )
        options_created += 1

    return created, updated, options_created


@api_view(['GET'])
@permission_classes([IsAdminUser])
def save_financial_products(request):
    if not settings.FINLIFE_API_KEY:
        return Response({'detail': 'FINLIFE_API_KEY가 설정되어 있지 않습니다.'}, status=500)

    url = (
        'https://finlife.fss.or.kr/finlifeapi/'
        f'depositProductsSearch.json?auth={settings.FINLIFE_API_KEY}'
        '&topFinGrpNo=020000&pageNo=1'
    )
    base_list, option_list, error = _fetch_finlife(url)
    if error:
        return Response({'detail': f'API 호출 실패: {error}'}, status=500)

    created, updated, options = _upsert_products(base_list, option_list, 'deposit')
    return Response({'message': '예금 저장 완료', 'created': created, 'updated': updated, 'options': options})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def save_saving_products(request):
    if not settings.FINLIFE_API_KEY:
        return Response({'detail': 'FINLIFE_API_KEY가 설정되어 있지 않습니다.'}, status=500)

    url = (
        'https://finlife.fss.or.kr/finlifeapi/'
        f'savingProductsSearch.json?auth={settings.FINLIFE_API_KEY}'
        '&topFinGrpNo=020000&pageNo=1'
    )
    base_list, option_list, error = _fetch_finlife(url)
    if error:
        return Response({'detail': f'API 호출 실패: {error}'}, status=500)

    created, updated, options = _upsert_products(base_list, option_list, 'saving')
    return Response({'message': '적금 저장 완료', 'created': created, 'updated': updated, 'options': options})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_status(request, product_id):
    product = get_object_or_404(FinancialProduct, pk=product_id)
    return Response({
        'is_favorite':   Favorite.objects.filter(user=request.user, product=product).exists(),
        'is_subscribed': SubscribedProduct.objects.filter(user=request.user, product=product).exists(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def favorite_toggle(request, product_id):
    product = get_object_or_404(FinancialProduct, pk=product_id)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        favorite.delete()
        return Response({'is_favorite': False, 'message': '관심상품 삭제'})

    return Response({'is_favorite': True, 'message': '관심상품 추가'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_toggle(request, product_id):
    product = get_object_or_404(FinancialProduct, pk=product_id)
    subscription, created = SubscribedProduct.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        subscription.delete()
        return Response({'is_subscribed': False, 'message': '가입상품 취소'})

    return Response({'is_subscribed': True, 'message': '가입상품 등록'})


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def recent_product(request, product_id):
    product = get_object_or_404(FinancialProduct, pk=product_id)
    if request.method == 'DELETE':
        RecentProduct.objects.filter(user=request.user, product=product).delete()
        return Response({'message': '최근 본 상품 삭제'})
    RecentProduct.objects.update_or_create(
        user=request.user,
        product=product,
        defaults={'viewed_at': timezone.now()}
    )
    return Response({'message': '최근 본 상품에 추가되었습니다.'})

