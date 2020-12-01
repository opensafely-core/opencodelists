from django.contrib import admin

from .models import Organisation, User


class UserAdmin(admin.ModelAdmin):
    fields = ["username", "name", "email", "is_admin", "full_set_password_url"]
    readonly_fields = ["username", "full_set_password_url"]


admin.site.register(User, UserAdmin)
admin.site.register(Organisation)
