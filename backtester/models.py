from django.db import models
from django.db.models import JSONField
from django.contrib.auth import get_user_model

User = get_user_model()


class Strategy(models.Model):
    name = models.CharField(max_length=255)
    prompt = models.TextField()
    strategy_code = models.TextField()
    parameters = JSONField()

    def __str__(self):
        return f"Strategy for {self.user.username}"
