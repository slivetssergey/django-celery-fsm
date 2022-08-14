from django.db import models


class BaseFSMModel(models.Model):
    status = models.CharField(choices=[], max_length=255, db_index=True)
    processing_error = models.JSONField(default=dict)

    def set_processing_error(self, status: str, msg: str):
        self.processing_error = {
            "status": status,
            "msg": msg,
        }

    class Meta:
        abstract = True
