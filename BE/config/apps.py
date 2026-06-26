import os
from django.apps import AppConfig


class ConfigAppConfig(AppConfig):
    name = 'config'

    def ready(self):
        # runserver가 --noreload 없이 실행될 때 reloader가 두 번 호출하는 것을 방지
        if os.environ.get('RUN_MAIN') != 'true':
            return
        from config import scheduler
        scheduler.start()
