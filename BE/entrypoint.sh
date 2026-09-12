#!/bin/sh
set -e

# depends_on 은 컨테이너 기동까지만 보장하므로 접속 가능해질 때까지 따로 기다린다.
python - <<'PY'
import os, sys, time
import psycopg

if not os.environ.get('POSTGRES_DB'):
    sys.exit(0)

dsn = (
    f"host={os.environ.get('POSTGRES_HOST', 'db')} "
    f"port={os.environ.get('POSTGRES_PORT', '5432')} "
    f"dbname={os.environ['POSTGRES_DB']} "
    f"user={os.environ.get('POSTGRES_USER', 'finfit')} "
    f"password={os.environ.get('POSTGRES_PASSWORD', '')}"
)

for attempt in range(1, 31):
    try:
        with psycopg.connect(dsn, connect_timeout=3):
            sys.exit(0)
    except Exception as exc:
        print(f"DB 대기 {attempt}/30: {exc}")
        time.sleep(2)

print("DB 접속 실패")
sys.exit(1)
PY

# 초기화는 web 컨테이너만 담당한다. sched 까지 migrate 를 돌리면 서로 충돌한다.
if [ "$SKIP_INIT" != "1" ]; then
  python manage.py migrate --noinput
  # --clear 를 쓰면 nginx 가 같은 볼륨을 읽는 동안 정적 파일이 잠깐 사라진다.
  python manage.py collectstatic --noinput
fi

exec "$@"
