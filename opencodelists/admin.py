from django.contrib import admin

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
