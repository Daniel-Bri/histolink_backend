import random
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        app_label = 'LoginYAutenticacion'
        ordering = ['-created_at']

    @classmethod
    def create_for_user(cls, user):
        cls.objects.filter(user=user, used=False).delete()
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        return cls.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at
