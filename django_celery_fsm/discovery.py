import importlib
import inspect

import django
from django.apps import apps

from django_celery_fsm.tasks import BaseTask


class FSMTasksDiscovery:
    def __init__(self):
        self._fsm_tasks = self.discovery()

    def discovery(self):
        result = []
        django.setup()
        for app in apps.get_app_configs():
            try:
                f = f'{app.name}.fsms'
                fsms = importlib.import_module(f)
                for name, obj in inspect.getmembers(fsms):
                    if inspect.isclass(obj) and issubclass(obj, BaseTask) and obj is not BaseTask:
                        result.append(obj)
            except ImportError:
                continue
        return result

    @property
    def tasks(self) -> list:
        return self._fsm_tasks
