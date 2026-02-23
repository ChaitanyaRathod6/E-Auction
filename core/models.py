from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, Email=None, password=None, **extra_fields):
        # Accept either `Email` (as Django will pass when USERNAME_FIELD is 'Email')
        # or `email` if provided elsewhere.
        email = Email or extra_fields.get('Email') or extra_fields.get('email')
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        # Create the model instance using the model's field name (`Email`)
        user = self.model(Email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, Email=None, password=None, **extra_fields):
        extra_fields.setdefault('Is_staff', True)
        extra_fields.setdefault('Is_Admin', True)

        if extra_fields.get('Is_staff') is not True:
            raise ValueError('Superuser must have Is_staff=True.')
        if extra_fields.get('Is_Admin') is not True:
            raise ValueError('Superuser must have Is_Admin=True.')

        return self.create_user(Email=Email, password=password, **extra_fields)

# Create your models here.
class User(AbstractBaseUser):
    @property
    def is_staff(self):
        return self.Is_staff

    @property
    def is_active(self):
        return self.Is_active

    @property
    def is_superuser(self):
        return self.Is_Admin

    def has_perm(self, perm, obj=None):
        return self.Is_Admin

    def has_module_perms(self, app_label):
        return self.Is_Admin
    
    Email = models.EmailField(unique=True)
    Rolechoice = (
        ('Admin', 'Admin'),
        ('Seller', 'Seller'),
        ('Buyer', 'Buyer'),
    )
    Role = models.CharField(max_length=10, choices=Rolechoice)
    Is_active = models.BooleanField(default=True)
    Is_staff = models.BooleanField(default=False)
    Is_Admin = models.BooleanField(default=False)
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'Email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.Email