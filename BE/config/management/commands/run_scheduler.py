"""
스케줄러 전용 프로세스.

gunicorn 워커가 여러 개라 AppConfig.ready() 에서 켜면 같은 작업이 워커 수만큼
중복 실행된다. 운영에서는 이 명령을 실행하는 컨테이너 하나에서만 돌린다.
"""

import signal
import threading

from django.core.management.base import BaseCommand

from config import scheduler


class Command(BaseCommand):
    help = 'APScheduler 를 전용 프로세스로 실행한다.'

    def handle(self, *args, **options):
        stop_event = threading.Event()

        def _shutdown(signum, frame):
            stop_event.set()

        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGINT, _shutdown)

        scheduler.start()
        stop_event.wait()
        scheduler.stop()
