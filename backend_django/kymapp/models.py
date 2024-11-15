from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Entry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    createdAt = models.DateTimeField(auto_now_add=True)
    value = models.IntegerField(default=0)

    def __str__(self):
        return self.title + " " + self.value
