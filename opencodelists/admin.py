from django.contrib import admin

from .models import Organisation, User

admin.site.register(User)
admin.site.register(Organisation)
