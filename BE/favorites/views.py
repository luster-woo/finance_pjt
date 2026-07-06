from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from products.models import FinancialProduct
from .models import Favorite


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    result = [
        {
            'id': favorite.product.id,
            'name': favorite.product.product_name,
            'bank': favorite.product.bank_name,
        }
        for favorite in favorites
    ]
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def favorite_toggle(request, product_id):
    product = get_object_or_404(FinancialProduct, pk=product_id)
    favorite_qs = Favorite.objects.filter(user=request.user, product=product)

    if favorite_qs.exists():
        favorite_qs.delete()
        return Response({'message': '관심상품 삭제', 'is_favorite': False})

    Favorite.objects.create(user=request.user, product=product)
    return Response({'message': '관심상품 추가', 'is_favorite': True}, status=201)
