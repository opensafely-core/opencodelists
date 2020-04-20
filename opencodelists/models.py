from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.text import slugify


class User(AbstractBaseUser):
    username = models.SlugField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(
        verbose_name="email address", max_length=255, unique=True,
    )
    organisation = models.ForeignKey(
        "Organisation", on_delete=models.CASCADE, related_name="users"
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = BaseUserManager()
    USERNAME_FIELD = "username"

    def save(self, *args, **kwargs):
        self.username = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True


class Organisation(models.Model):
    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Project(models.Model):
    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=255)
    organisations = models.ManyToManyField("Organisation", related_name="projects")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
