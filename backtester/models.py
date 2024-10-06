from django.db import models
from django.db.models import JSONField
from django.contrib.auth import get_user_model

User = get_user_model()


class Strategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="strategies")
    prompt = models.TextField()
    strategy_code = models.TextField()
    parameters = JSONField()

    def __str__(self):
        return f"Strategy for {self.user.username}"
