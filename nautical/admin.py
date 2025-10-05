
from django.contrib import admin
from . import models

@admin.register(models.CrewMember)
class CrewAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role', 'contact', 'has_license')
    list_filter = ('role', 'has_license')
    search_fields = ('full_name', 'contact')

class MaintenanceInline(admin.TabularInline):
    model = models.MaintenanceRecord
    extra = 0

class MediaAssetInline(admin.TabularInline):
    model = models.MediaAsset
    extra = 0

@admin.register(models.LogbookEntry)
class LogbookAdmin(admin.ModelAdmin):
    list_display = ('start_datetime', 'departure_port', 'arrival_port', 'distance_nm', 'engine_hours')
    list_filter = ('departure_port', 'arrival_port')
    search_fields = ('departure_port', 'arrival_port', 'notes')
    filter_horizontal = ('crew',)
    inlines = [MaintenanceInline, MediaAssetInline]

@admin.register(models.MaintenanceRecord)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'equipment', 'voyage', 'cost_eur', 'next_due_date')
    list_filter = ('equipment',)
    search_fields = ('description',)

class ChecklistItemInline(admin.TabularInline):
    model = models.ChecklistItem
    extra = 1
    fields = ('label', 'required', 'action')
    readonly_fields = ()

@admin.register(models.Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')
    inlines = [ChecklistItemInline]

@admin.register(models.ChecklistRun)
class ChecklistRunAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'voyage', 'created_at')
    autocomplete_fields = ('checklist', 'voyage')

@admin.register(models.ChecklistItemRun)
class ChecklistItemRunAdmin(admin.ModelAdmin):
    list_display = ('run', 'item', 'checked', 'note')
    list_filter = ('checked',)
    search_fields = ('item__label', 'note')

@admin.register(models.MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('voyage', 'kind', 'caption', 'created_at')
    list_filter = ('kind',)
    search_fields = ('caption', 'voyage__departure_port', 'voyage__arrival_port')

@admin.register(models.Consumable)
class ConsumableAdmin(admin.ModelAdmin):
    list_display = ("name", "origin", "reference", "quantity", "price_eur")
    list_filter = ("origin",)
    search_fields = ("name", "reference", "remark")


@admin.register(models.Chronology)
class ChronologyAdmin(admin.ModelAdmin):
    list_display = ('date', 'time', 'performer', 'description')
    list_filter = ('performer',)
    search_fields = ('description', 'action_realisee')
