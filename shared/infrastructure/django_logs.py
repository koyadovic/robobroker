from django.db import models


class DSystemLog(models.Model):
    instant = models.DateTimeField(auto_now_add=True)
    log_type = models.CharField(max_length=255, db_index=True)
    text = models.TextField(blank=False, null=False, default='')
