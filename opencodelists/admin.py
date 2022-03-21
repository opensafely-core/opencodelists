from django.contrib import admin

from .models import Organisation, User


class UserAdmin(admin.ModelAdmin):
    fields = ["username", "name", "email", "is_admin"]
    readonly_fields = ["username"]


admin.site.register(User, UserAdmin)
admin.site.register(Organisation)
