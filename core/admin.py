from django.contrib import admin
from .models import Playbook, Action, Trigger, ExecutionLog

class ActionInline(admin.TabularInline):
    model = Action
    extra = 1

@admin.register(Playbook)
class PlaybookAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    inlines = [ActionInline]

@admin.register(Trigger)
class TriggerAdmin(admin.ModelAdmin):
    list_display = ("event_type", "threshold", "playbook")

@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "playbook", "action", "status")
    list_filter = ("status", "action", "timestamp")
    ordering = ("-timestamp",)
