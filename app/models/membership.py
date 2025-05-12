from django.db import models
from .user import User


class Plan(models.Model):
    name = models.CharField( max_length=50)
    price = models.IntegerField()
    storage_limit = models.BigIntegerField()
    features = models.JSONField()

    def __str__(self) -> str:
        return self.name

class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    is_active = models.BooleanField()
    purchase_date = models.DateField(auto_now=False, auto_now_add=False)
    expiry_date = models.DateField(auto_now=False, auto_now_add=False)
    auto_renew = models.BooleanField(default=False)

