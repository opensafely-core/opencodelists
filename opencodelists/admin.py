from django.contrib import admin

from .models import Organisation, Project, User

admin.site.register(User)
admin.site.register(Organisation)
admin.site.register(Project)
