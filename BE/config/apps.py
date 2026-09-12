import os
from django.apps import AppConfig


class ConfigAppConfig(AppConfig):
    name = 'config'

    def ready(self):
        # runserver 는 reloader 때문에 프로세스가 둘이라 자식(RUN_MAIN='true')에서만 켠다.
        # gunicorn 에는 RUN_MAIN 이 없으므로 여기서는 켜지지 않고,
        # 운영에서는 sched 컨테이너가 manage.py run_scheduler 로 직접 띄운다.
        from django.conf import settings

        if not getattr(settings, 'RUN_SCHEDULER', False):
            return
        if os.environ.get('RUN_MAIN') != 'true':
            return

        from config import scheduler
        scheduler.start()
