# make_data.py — 랜덤 더미 유저 데이터를 생성해 fixture JSON으로 저장하는 스크립트
#
# 사용법:
#   python make_data.py
#
# 실행 전 루트 .env 에 FINLIFE_API_KEY 가 설정돼 있어야 합니다.
# (금융상품 코드 목록을 FSS Finlife API 로 가져옵니다.)

import json
import os
import random
from collections import OrderedDict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')


first_name_samples = "김이박최정강조윤장임"
middle_name_samples = "민서예지도하주윤채현지"
last_name_samples = "준윤우원호후서연아은진"


def random_name():
    return (
        random.choice(first_name_samples)
        + random.choice(middle_name_samples)
        + random.choice(last_name_samples)
        + str(random.randint(1, 100))
    )


def fetch_product_codes(api_key):
    import requests

    DP_URL = 'http://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json'
    SP_URL = 'http://finlife.fss.or.kr/finlifeapi/savingProductsSearch.json'
    params = {'auth': api_key, 'topFinGrpNo': '020000', 'pageNo': 1}

    codes = []
    for url in (DP_URL, SP_URL):
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        base_list = resp.json().get('result', {}).get('baseList', [])
        codes.extend(p['fin_prdt_cd'] for p in base_list)
    return codes


def generate_fixture(api_key, n=10000):
    financial_products = fetch_product_codes(api_key)
    if not financial_products:
        raise ValueError('금융 상품 목록을 가져올 수 없습니다. FINLIFE_API_KEY를 확인하세요.')

    username_set = set()
    username_list = []
    while len(username_list) < n:
        name = random_name()
        if name not in username_set:
            username_set.add(name)
            username_list.append(name)

    save_path = Path(__file__).parent / 'BE' / 'accounts' / 'fixtures' / 'accounts' / 'user_data.json'
    save_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for i, username in enumerate(username_list):
        record = OrderedDict()
        record['model'] = 'accounts.User'
        record['pk'] = i + 1
        record['fields'] = {
            'username': username,
            'financial_products': ','.join(
                random.choice(financial_products)
                for _ in range(random.randint(0, 5))
            ),
            'age': random.randint(18, 65),
            'money': random.randrange(0, 100_000_000, 100_000),
            'salary': random.randrange(0, 1_500_000_000, 1_000_000),
            'password': '1234',
            'nickname': None,
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
        }
        records.append(record)

    with save_path.open('w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent='\t')

    print(f'데이터 생성 완료 / 저장 위치: {save_path}')


if __name__ == '__main__':
    api_key = os.environ.get('FINLIFE_API_KEY', '')
    if not api_key:
        print('ERROR: FINLIFE_API_KEY 환경변수가 설정되지 않았습니다.')
        raise SystemExit(1)
    generate_fixture(api_key)
