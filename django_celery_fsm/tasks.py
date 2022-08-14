import importlib
import logging
from functools import lru_cache

import celery
from django.apps import apps
from django.db import transaction

logger = logging.getLogger("fsm")


class BaseTask(celery.Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = f"{self.__class__.__module__}.{self.__class__.__qualname__}"

    @lru_cache
    def get_object(self, id: int, app_label: str, model_name: str):
        model = apps.get_model(app_label=app_label, model_name=model_name)
        self._object_instance = model.objects.select_for_update(nowait=True).get(pk=id)
        return self._object_instance

    def handler(self, instance, *args, **kwargs):
        raise NotImplementedError

    def get_fsm(self, **kwargs):
        fsm = kwargs.get("fsm")
        if not fsm:
            raise ValueError("Incorrect task payload. Lost fsm.")
        module, class_name = fsm.rsplit(".", 1)
        module = importlib.import_module(module)
        fsm = getattr(module, class_name)
        return fsm

    def on_success(self, retval, task_id, args, kwargs):
        fsm = self.get_fsm(**kwargs)
        fsm().step_callback(instance_id=kwargs["id"], current_name=kwargs["step"])
        fsm().task_success(instance_id=kwargs["id"], name=kwargs["step"])
        fsm().run_next_step(instance_id=kwargs["id"], current_name=kwargs["step"])

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        fsm = self.get_fsm(**kwargs)
        object = self.get_object(
            **{
                "id": kwargs["id"],
                "app_label": kwargs["app_label"],
                "model_name": kwargs["model_name"],
            },
        )
        msg = f"{einfo.exc_info[1].__class__.__name__}: {einfo.exception}"
        object.set_processing_error(status=kwargs["status"], msg=msg)
        object.save()
        fsm().fail_task(instance_id=kwargs["id"], name=kwargs["step"], exc=exc, einfo=einfo)

    def run(self, *args, **kwargs):
        with transaction.atomic():
            object = self.get_object(
                **{
                    "id": kwargs["id"],
                    "app_label": kwargs["app_label"],
                    "model_name": kwargs["model_name"],
                },
            )
            self.handler(instance=object)
