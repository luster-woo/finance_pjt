from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'FINLIFE API에서 예금·적금 상품을 가져와 DB에 저장합니다.'

    def handle(self, *args, **options):
        from products.views import _fetch_finlife, _upsert_products

        api_key = settings.FINLIFE_API_KEY
        if not api_key:
            self.stderr.write(self.style.ERROR('FINLIFE_API_KEY가 .env에 설정되어 있지 않습니다.'))
            return

        self.stdout.write('=== 금융 상품 임포트 시작 ===\n')

        deposit_url = (
            f'https://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json'
            f'?auth={api_key}&topFinGrpNo=020000&pageNo=1'
        )
        base_list, option_list, error = _fetch_finlife(deposit_url)
        if error:
            self.stderr.write(self.style.ERROR(f'예금 API 호출 실패: {error}'))
        else:
            created, updated, options_cnt = _upsert_products(base_list, option_list, 'deposit')
            self.stdout.write(self.style.SUCCESS(
                f'예금: {created}개 신규 / {updated}개 업데이트 / 옵션 {options_cnt}개'
            ))

        saving_url = (
            f'https://finlife.fss.or.kr/finlifeapi/savingProductsSearch.json'
            f'?auth={api_key}&topFinGrpNo=020000&pageNo=1'
        )
        base_list, option_list, error = _fetch_finlife(saving_url)
        if error:
            self.stderr.write(self.style.ERROR(f'적금 API 호출 실패: {error}'))
        else:
            created, updated, options_cnt = _upsert_products(base_list, option_list, 'saving')
            self.stdout.write(self.style.SUCCESS(
                f'적금: {created}개 신규 / {updated}개 업데이트 / 옵션 {options_cnt}개'
            ))

        self.stdout.write(self.style.SUCCESS('\n=== 완료 ==='))
