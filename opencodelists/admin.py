from django.contrib import admin
from django.db.models import Exists, OuterRef, Q
from rest_framework.authtoken.admin import TokenAdmin

from codelists.models import CodelistVersion, Handle

from .models import Membership, Organisation, User


class MembershipInline(admin.TabularInline):
    model = Membership
    raw_id_fields = ("organisation", "user")
    verbose_name = "Organisation Membership"
    view_on_site = False
    extra = 1


class AdminStatusFilter(admin.SimpleListFilter):
    title = "admin status"
    parameter_name = "admin_status"

    def lookups(self, request, model_admin):
        return [("admin", "Admin"), ("non_admin", "Non-admin")]

    def queryset(self, request, queryset):
        if self.value() == "admin":
            return queryset.filter(is_admin=True)
        if self.value() == "non_admin":
            return queryset.filter(is_admin=False)
        return queryset


class HasCodelistsFilter(admin.SimpleListFilter):
    title = "codelist activity"
    parameter_name = "has_codelists"

    def lookups(self, request, model_admin):
        return [("yes", "Has codelists"), ("no", "No codelists")]

    def queryset(self, request, queryset):
        # Include historical ownership and authorship, including draft versions.
        condition = Q(Exists(Handle.objects.filter(user=OuterRef("pk")))) | Q(
            Exists(CodelistVersion.objects.filter(author=OuterRef("pk")))
        )
        if self.value() == "yes":
            return queryset.filter(condition)
        if self.value() == "no":
            return queryset.exclude(condition)
        return queryset


class OrganisationMemberFilter(admin.SimpleListFilter):
    title = "organisation membership"
    parameter_name = "organisation_member"

    def lookups(self, request, model_admin):
        return [("yes", "Member"), ("no", "Not a member")]

    def queryset(self, request, queryset):
        condition = Exists(Membership.objects.filter(user=OuterRef("pk")))
        if self.value() == "yes":
            return queryset.filter(condition)
        if self.value() == "no":
            return queryset.exclude(condition)
        return queryset


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = ["username", "name", "email", "is_admin"]
    readonly_fields = ["username"]
    list_display = [
        "username",
        "name",
        "email",
        "is_admin",
        "get_organisations",
    ]
    search_fields = ["username", "name"]
    list_filter = [
        AdminStatusFilter,
        HasCodelistsFilter,
        OrganisationMemberFilter,
    ]
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


TokenAdmin.list_display = ["user", "created"]
TokenAdmin.fields = ["user", "created"]
TokenAdmin.readonly_fields = ["created"]
