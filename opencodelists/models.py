from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_slug
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from codelists.models import Codelist, Status


def validate_username(username):
    validate_slug(username)
    if User.objects.filter(username__iexact=username).exists():
        raise ValidationError("A user with this username already exists.")


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
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
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
        validators=[validate_username],
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

    class Meta:
        ordering = (models.functions.Lower("username"),)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = slugify(self.name)
        # Explicitly validate the username on first save.  This means that the validators will be run
        # when creating a model instance outside of a form, e.g. in a shell with User.objects.create_user(...)
        # As the username is a primary key, not enforcing the validators means that we
        # can overwrite an existing user
        if self._state.adding:
            validate_username(self.username)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def owner_identifier(self):
        return f"user:{self.pk}"

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

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
        """Codelists owned by user"""
        return Codelist.objects.filter(handles__is_current=True, handles__user=self)

    @property
    def drafts(self):
        """Codelist versions authored by user and in draft"""
        return self.versions.filter(status=Status.DRAFT)

    @property
    def versions_under_review(self):
        """Codelist versions authored by user and under review"""
        return self.versions.filter(status=Status.UNDER_REVIEW)

    @property
    def authored_for_organisation(self):
        """Codelist versions authored by user but owned by an organisation"""
        return Codelist.objects.filter(
            versions__author=self,
            handles__user__isnull=True,
            versions__status=Status.PUBLISHED,
        )

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
    def owner_identifier(self):
        return f"organisation:{self.pk}"

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

    def get_absolute_url(self):
        return reverse("organisation", args=(self.organisation.slug,))
