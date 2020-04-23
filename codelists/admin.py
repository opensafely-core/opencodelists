from django.contrib import admin

from .models import Codelist, Reference, SignOff


class SignOffInline(admin.TabularInline):
    model = SignOff


class ReferenceInline(admin.TabularInline):
    model = Reference


class CodelistAdmin(admin.ModelAdmin):
    model = Codelist
    exclude = ["slug"]
    inlines = [ReferenceInline, SignOffInline]
    ordering = ["name"]


admin.site.register(Codelist, CodelistAdmin)
