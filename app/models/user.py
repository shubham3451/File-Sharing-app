from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from phonenumber_field import modelfields
from django.utils import timezone


# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, username, email, phone, password=None, **extra_fields):
        if not email:
            raise ValueError("email is required")
        if not username:
            raise ValueError("email is required")
        if not phone:
            raise ValueError("value is required")
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            phone=phone,
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
        
    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username=username, password=password, **extra_fields)

class User(AbstractBaseUser):
    username = models.CharField( max_length=50, unique=True)
    email = models.EmailField(max_length=50, unique=True)
    phone = modelfields.PhoneNumberField(unique=True)
    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default = False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    is_2fa_enabled = models.BooleanField(default=False)
    two_fa_secret = models.CharField(max_length=255, blank=True, null=True)
    used_storage = models.BigIntegerField(default=0)
    REQUIRED_FIELDS = ['email', 'phone']
    USERNAME_FIELD = 'username' 
    objects  = UserManager()
    
    def __str__(self):
        return self.username
    
    def has_perm(self, perm, obj=None):
        """
        Checks whether the user has a specific permission.
        """
        return True
    
    def has_module_perms(self, app_label):
        return True
    
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return (timezone.now() - self.created_at).seconds > 300  # 5 minutes
    
    def __str__(self) -> str:
        return str(self.otp)