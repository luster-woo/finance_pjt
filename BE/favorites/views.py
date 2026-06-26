from rest_framework.response import Response

from products.models import FinancialProduct
from .models import Favorite
from rest_framework.decorators import (
    api_view,
    permission_classes
)
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favorite_list(request):

    favorites = Favorite.objects.filter(
        user=request.user
    )

    result = []

    for favorite in favorites:

        result.append({
            'id': favorite.product.id,
            'name': favorite.product.product_name,
            'bank': favorite.product.bank_name,
        })

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def favorite_toggle(request, product_id):

    product = FinancialProduct.objects.get(
        pk=product_id
    )

    favorite = Favorite.objects.filter(
        user=request.user,
        product=product
    )

    if favorite.exists():

        favorite.delete()

        return Response({
            'message': '관심상품 삭제'
        })

    Favorite.objects.create(
        user=request.user,
        product=product
    )

    return Response({
        'message': '관심상품 추가'
    })