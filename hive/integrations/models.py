from django.db import models


# Create your models here.
class Integration(models.Model):
    name = models.CharField(max_length=255)
    config = models.JSONField(default=dict)

    def __str__(self):
        return self.name
