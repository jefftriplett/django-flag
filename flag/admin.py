from django.contrib import admin

from .models import FlaggedContent, FlagInstance


class InlineFlagInstance(admin.TabularInline):
    model = FlagInstance
    extra = 0
    raw_id_fields = ['user']


class FlaggedContentAdmin(admin.ModelAdmin):
    inlines = [InlineFlagInstance]
    raw_id_fields = ['creator', 'moderator']


admin.site.register(FlaggedContent, FlaggedContentAdmin)
