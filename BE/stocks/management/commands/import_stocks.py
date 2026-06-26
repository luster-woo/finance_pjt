from decimal import Decimal

import yfinance as yf
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '주요 한국 주식 종목 정보와 가격 이력을 yfinance에서 가져와 DB에 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period', default='1mo',
            help='가격 이력 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y). 기본값: 1mo',
        )
        parser.add_argument(
            '--no-prices', action='store_true',
            help='가격 이력 저장 생략 (종목 정보만 저장)',
        )

    def handle(self, *args, **options):
        from stocks.models import Stock, StockPrice
        from stocks.views import MAJOR_STOCKS, _yf_ticker, _translate_to_korean

        period = options['period']
        load_prices = not options['no_prices']

        self.stdout.write('=== 주식 종목 임포트 시작 ===\n')

        created_stocks = updated_stocks = 0
        for stock_code, default_name, default_desc in MAJOR_STOCKS:
            ticker_sym = _yf_ticker(stock_code)
            name = default_name
            desc = default_desc
            try:
                info = yf.Ticker(ticker_sym).info
                en_summary = info.get('longBusinessSummary', '')
                if en_summary and len(en_summary) > 50:
                    translated = _translate_to_korean(default_name, en_summary)
                    if translated:
                        desc = translated
            except Exception:
                pass

            _, flag = Stock.objects.update_or_create(
                stock_code=stock_code,
                defaults={'stock_name': name, 'description': desc},
            )
            if flag:
                created_stocks += 1
            else:
                updated_stocks += 1
            self.stdout.write(f'  [{stock_code}] {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\n종목: {created_stocks}개 신규 / {updated_stocks}개 업데이트'
        ))

        if not load_prices:
            self.stdout.write(self.style.SUCCESS('\n=== 완료 ==='))
            return

        self.stdout.write(f'\n가격 이력 저장 중 (기간: {period})...')
        total_prices = 0
        for stock_code, _, _ in MAJOR_STOCKS:
            ticker_sym = _yf_ticker(stock_code)
            try:
                df = yf.Ticker(ticker_sym).history(period=period)
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'  {stock_code}: 조회 실패 - {exc}'))
                continue

            if df.empty:
                continue

            stock = Stock.objects.get(stock_code=stock_code)
            saved = 0
            for date, row in df.iterrows():
                close = row.get('Close')
                if close is None:
                    continue
                open_price = row.get('Open')
                change_rate = None
                if open_price and open_price != 0:
                    change_rate = round(
                        (float(close) - float(open_price)) / float(open_price) * 100, 2
                    )
                recorded_at = (
                    date.to_pydatetime().replace(tzinfo=None)
                    if hasattr(date, 'to_pydatetime') else date
                )
                _, created_flag = StockPrice.objects.get_or_create(
                    stock=stock,
                    recorded_at=recorded_at,
                    defaults={
                        'price': Decimal(str(round(float(close), 2))),
                        'change_rate': Decimal(str(change_rate)) if change_rate is not None else None,
                        'volume': int(row.get('Volume', 0) or 0),
                    }
                )
                if created_flag:
                    saved += 1
            total_prices += saved
            self.stdout.write(f'  {stock_code}: {saved}개')

        self.stdout.write(self.style.SUCCESS(f'\n가격 이력: 총 {total_prices}개 저장 완료'))
        self.stdout.write(self.style.SUCCESS('\n=== 완료 ==='))
