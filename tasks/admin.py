from django.contrib import admin

from .models import Invitation

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'workspace', 'invited_by', 'accepted', 'created_at')
    search_fields = ('email', 'workspace__name')
