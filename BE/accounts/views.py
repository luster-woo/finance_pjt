from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import SignupSerializer, ProfileSerializer
from financial_tests.models import FinancialTest
from favorites.models import Favorite, SubscribedProduct, RecentProduct
from stocks.models import StockFavorite
from reviews.models import Review
from cards.models import CardReview
from community.models import CommunityPost, Comment


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': ProfileSerializer(user, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    if request.method == 'GET':
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    serializer = ProfileSerializer(request.user, data=request.data, partial=True, context={'request': request})

    if serializer.is_valid():
        serializer.save()
        return Response(ProfileSerializer(request.user, context={'request': request}).data)

    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass
    return Response({'message': '로그아웃 되었습니다.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mypage(request):
    last_test = FinancialTest.objects.filter(user=request.user).order_by('-created_at').first()

    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'nickname': request.user.nickname,
        'email': request.user.email,
        'financial_type': request.user.financial_type,
        'profile_image': request.build_absolute_uri(request.user.profile_image.url)
        if request.user.profile_image and request.user.profile_image.name else None,
        'bio': request.user.bio,
        'favorites_count': Favorite.objects.filter(user=request.user).count(),
        'subscriptions_count': SubscribedProduct.objects.filter(user=request.user).count(),
        'recent_count': RecentProduct.objects.filter(user=request.user).count(),
        'stock_favorites_count': StockFavorite.objects.filter(user=request.user).count(),
        'product_reviews_count': Review.objects.filter(user=request.user).count(),
        'card_reviews_count': CardReview.objects.filter(user=request.user).count(),
        'latest_test_result': {
            'score': last_test.score,
            'result_type': last_test.result_type,
        } if last_test else None,
        'address': request.user.address or '',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mypage_product_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    return Response([
        {
            'id': favorite.product.id,
            'product_name': favorite.product.product_name,
            'bank_name': favorite.product.bank_name,
            'created_at': favorite.created_at,
        }
        for favorite in favorites
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mypage_product_subscriptions(request):
    subscriptions = SubscribedProduct.objects.filter(user=request.user).select_related('product')
    result = []
    for sub in subscriptions:
        p = sub.product
        # 최고 우대금리 기준 옵션
        best = p.financialproductoption_set.order_by('-max_interest_rate').first()
        result.append({
            'id': p.id,
            'product_name': p.product_name,
            'bank_name': p.bank_name,
            'product_type': p.product_type,
            'subscribed_at': sub.subscribed_at,
            'interest_rate': float(best.interest_rate) if best and best.interest_rate is not None else None,
            'max_interest_rate': float(best.max_interest_rate) if best and best.max_interest_rate is not None else None,
            'save_trm': best.save_trm if best else None,
        })
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mypage_product_recent(request):
    recent_products = RecentProduct.objects.filter(user=request.user).select_related('product').order_by('-viewed_at')
    return Response([
        {
            'id': recent.product.id,
            'product_name': recent.product.product_name,
            'bank_name': recent.product.bank_name,
            'viewed_at': recent.viewed_at,
        }
        for recent in recent_products
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mypage_stock_favorites(request):
    favorites = StockFavorite.objects.filter(user=request.user)
    return Response([
        {
            'id': favorite.stock.id,
            'stock_code': favorite.stock.stock_code,
            'stock_name': favorite.stock.stock_name,
            'created_at': favorite.created_at,
        }
        for favorite in favorites
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mypage_reviews(request):
    product_reviews = Review.objects.filter(user=request.user)
    card_reviews = CardReview.objects.filter(user=request.user)

    return Response({
        'product_reviews': [
            {
                'id': review.id,
                'product_id': review.product.id,
                'rating': review.rating,
                'content': review.content,
                'created_at': review.created_at,
            }
            for review in product_reviews
        ],
        'card_reviews': [
            {
                'id': review.id,
                'card_id': review.card.id,
                'rating': review.rating,
                'content': review.content,
                'created_at': review.created_at,
            }
            for review in card_reviews
        ],
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mypage_community(request):
    posts = CommunityPost.objects.filter(user=request.user).order_by('-created_at')
    comments = Comment.objects.filter(user=request.user).order_by('-created_at')
    return Response({
        'posts': [
            {
                'id': p.id,
                'title': p.title,
                'content': p.content[:100],
                'stock': p.stock_id,
                'likes_count': p.likes_count,
                'created_at': p.created_at,
            }
            for p in posts
        ],
        'comments': [
            {
                'id': c.id,
                'content': c.content[:80],
                'post_id': c.post_id,
                'likes_count': c.likes_count,
                'created_at': c.created_at,
            }
            for c in comments
        ],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    current = request.data.get('current_password', '')
    new_pw = request.data.get('new_password', '')
    if not current or not new_pw:
        return Response({'detail': '현재 비밀번호와 새 비밀번호를 입력해주세요.'}, status=400)
    if not request.user.check_password(current):
        return Response({'detail': '현재 비밀번호가 올바르지 않습니다.'}, status=400)
    if len(new_pw) < 8:
        return Response({'detail': '새 비밀번호는 8자 이상이어야 합니다.'}, status=400)
    request.user.set_password(new_pw)
    request.user.save()
    return Response({'message': '비밀번호가 변경됐습니다. 다시 로그인해주세요.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mypage_test_result(request):
    test = FinancialTest.objects.filter(user=request.user).order_by('-created_at').first()
    if not test:
        return Response({'message': '테스트 결과 없음'}, status=404)

    return Response({
        'score': test.score,
        'result_type': test.result_type,
        'created_at': test.created_at,
    })
