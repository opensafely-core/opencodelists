from datetime import UTC

from django.contrib import admin
from django.http import HttpRequest
from django.utils import timezone
from django.utils.formats import date_format
from rest_framework.authtoken.admin import TokenAdmin as DRFTokenAdmin
from rest_framework.authtoken.models import TokenProxy

from .models import Membership, Organisation, User


class MembershipInline(admin.TabularInline):
    model = Membership
    raw_id_fields = ("organisation", "user")
    verbose_name = "Organisation Membership"
    view_on_site = False
    extra = 1


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = ["username", "name", "email", "is_admin"]
    readonly_fields = ["username"]
    list_display = ["username", "name", "email", "is_admin", "get_organisations"]
    search_fields = ["username", "name"]
    inlines = [MembershipInline]

    @admin.display(description="Organisations")
    def get_organisations(self, obj):
        return ", ".join(obj.memberships.values_list("organisation__name", flat=True))


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ["organisation", "member_count"]
    inlines = [MembershipInline]

    @admin.display(description="No. of Users")
    def member_count(self, obj):
        return obj.users.count()


# DRF registers TokenProxy with its own admin class. Replace that registration
# so we can customise the screen while retaining DRF’s behaviour.
admin.site.unregister(TokenProxy)


@admin.register(TokenProxy)
class TokenAdmin(DRFTokenAdmin):
    """
    Custom formatting for the token admin interface allowing tokens to be
    created, read, and deleted, but not updated.
    """

    list_display = ("user", "created_at_formatted")
    fields = ("user", "key", "created_at_formatted")
    readonly_fields = ("key", "created_at_formatted")
    list_select_related = ("user",)

    # Key and created are generated when the token is saved, so only show the
    # user field on the add form.
    def get_fields(
        self, request: HttpRequest, obj: TokenProxy | None = None
    ) -> tuple[str, ...]:
        if obj is None:
            return ("user",)

        return self.fields

    # Django handles add and change permissions separately, allowing tokens to be
    # created while keeping existing tokens read-only.
    def has_change_permission(
        self, request: HttpRequest, obj: TokenProxy | None = None
    ) -> bool:
        return False

    @admin.display(
        description="Created at",
        ordering="created",
    )
    def created_at_formatted(self, obj: TokenProxy) -> str:
        if obj.created is None:
            return "-"

        # Always show the timestamp in UTC, independently of the active timezone.
        created_at = timezone.localtime(obj.created, UTC)
        formatted_date = date_format(created_at, r"j M Y \a\t H:i")

        return f"{formatted_date} UTC"
