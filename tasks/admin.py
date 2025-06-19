from django.contrib import admin
from .models import Task
from .models import Invitation

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'workspace', 'invited_by', 'accepted', 'created_at')
    search_fields = ('email', 'workspace__name')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'reminder_date', 'due_date', 'status']
    list_filter = ['status', 'reminder_date']