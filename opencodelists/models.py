from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.text import slugify


class UserManager(BaseUserManager):
    """
    Custom User Model Manager

    This builds on top Django's BaseUserManager to add the methods required to
    make createsuperuser work.
    """

    def create_user(self, username, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The Email must be set")

        org = Organisation.objects.first()
        if not org:
            org = Organisation.objects.create(
                name="DataLab", slug="datalab", url="https://ebmdatalab.net/"
            )

        email = self.normalize_email(email)
        user = self.model(
            username=username, email=email, organisation=org, **extra_fields
        )
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, username, email, password, **extra_fields):
        """Create and save an Admin with the given email and password."""
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_admin") is not True:
            raise ValueError("Superuser must have is_admin=True.")

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser):
    username = models.SlugField(primary_key=True)
    name = models.TextField()
    email = models.EmailField(
        verbose_name="email address", max_length=255, unique=True,
    )
    organisation = models.ForeignKey(
        "Organisation", on_delete=models.CASCADE, related_name="users"
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def save(self, *args, **kwargs):
        if not self.username:
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
    name = models.TextField()
    url = models.URLField()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Project(models.Model):
    slug = models.SlugField(primary_key=True)
    name = models.TextField()
    organisations = models.ManyToManyField("Organisation", related_name="projects")
    details = models.TextField()
    url = models.URLField()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
