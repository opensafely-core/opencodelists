from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import Signer
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify

from codelists.models import Codelist

SET_PASSWORD_SALT = "set-password"


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
    username = models.SlugField(
        primary_key=True,
        error_messages={"unique": "A user with this username already exists."},
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
        error_messages={"unique": "A user with this email address already exists."},
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

    @cached_property
    def signed_username(self):
        return Signer(salt=SET_PASSWORD_SALT).sign(self.username)

    def get_set_password_url(self):
        return reverse("user-set-password", kwargs={"token": self.signed_username})

    def full_set_password_url(self):
        return settings.ALLOWED_HOSTS[0] + self.get_set_password_url()

    def get_organisation_membership(self, organisation):
        try:
            return self.memberships.get(organisation=organisation)
        except Membership.DoesNotExist:
            return None

    def is_member(self, organisation):
        return bool(self.get_organisation_membership(organisation))

    def is_admin_member(self, organisation):
        membership = self.get_organisation_membership(organisation)
        return membership and membership.is_admin

    @property
    def codelists(self):
        return Codelist.objects.filter(handles__user=self)

    def get_codelist_create_url(self):
        return reverse("codelists:user_codelist_create", kwargs=self.url_kwargs)

    def get_codelists_api_url(self):
        return reverse("codelists_api:user_codelists", kwargs=self.url_kwargs)

    @property
    def url_kwargs(self):
        return {"username": self.username}

    @property
    def api_token(self):
        try:
            return self.auth_token.key
        except ObjectDoesNotExist:
            return

    @staticmethod
    def unsign_username(token):
        return Signer(salt=SET_PASSWORD_SALT).unsign(token)


class Organisation(models.Model):
    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=255)
    url = models.URLField()
    users = models.ManyToManyField(
        "User", through="Membership", related_name="organisations"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def organisation(self):
        # Required for duck-typing in codelists.views.decorators.require_permission.
        return self

    @property
    def codelists(self):
        return Codelist.objects.filter(handles__organisation=self)

    def get_codelist_create_url(self):
        return reverse("codelists:organisation_codelist_create", kwargs=self.url_kwargs)

    @property
    def url_kwargs(self):
        return {"organisation_slug": self.slug}

    def get_user_membership(self, user):
        try:
            return self.memberships.get(user=user)
        except Membership.DoesNotExist:
            return None


class Membership(models.Model):
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="memberships"
    )
    organisation = models.ForeignKey(
        "Organisation", on_delete=models.CASCADE, related_name="memberships"
    )
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateField()

    class Meta:
        unique_together = ("user", "organisation")
