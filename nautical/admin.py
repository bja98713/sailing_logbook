
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


class VoyageEventInline(admin.TabularInline):
    model = models.VoyageEvent
    extra = 0
    fields = ('timestamp', 'latitude', 'longitude', 'description', 'weather', 'distance_from_prev_nm', 'elapsed_hours_since_prev', 'avg_speed_since_prev_kn')
    readonly_fields = ('distance_from_prev_nm', 'elapsed_hours_since_prev', 'avg_speed_since_prev_kn')

@admin.register(models.LogbookEntry)
class LogbookAdmin(admin.ModelAdmin):
    list_display = ('start_datetime', 'departure_port', 'arrival_port', 'distance_nm', 'engine_hours')
    list_filter = ('departure_port', 'arrival_port')
    search_fields = ('departure_port', 'arrival_port', 'notes')
    filter_horizontal = ('crew',)
    inlines = [MaintenanceInline, MediaAssetInline, VoyageEventInline]

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


# === ADMINISTRATION NOUVEAU SYSTÈME DE LIVRE DE BORD ===

class LogEntryInline(admin.TabularInline):
    model = models.LogEntry
    extra = 0
    fields = ('date', 'heure', 'evenements', 'position', 'vent_force', 'allure')

class VoyageCrewMemberInline(admin.TabularInline):
    model = models.VoyageCrewMember
    extra = 0
    fields = ('nom', 'prenom', 'role')

class WeatherConditionInline(admin.StackedInline):
    model = models.WeatherCondition
    extra = 0
    fields = ('datetime', 'type_bulletin', 'situation_generale')

@admin.register(models.VoyageLog)
class VoyageLogAdmin(admin.ModelAdmin):
    list_display = ('sujet_voyage_ou_bateau', 'skipper', 'port_depart', 'port_arrivee', 'date_debut', 'statut')
    list_filter = ('statut', 'date_debut', 'skipper')
    search_fields = ('sujet_voyage', 'bateau', 'skipper', 'port_depart', 'port_arrivee')
    date_hierarchy = 'date_debut'
    
    inlines = [LogEntryInline, VoyageCrewMemberInline, WeatherConditionInline]
    
    fieldsets = (
        ('Informations du voyage', {
            'fields': ('sujet_voyage', 'bateau', 'skipper', 'immatriculation')
        }),
        ('Navigation', {
            'fields': ('date_debut', 'date_fin', 'port_depart', 'port_arrivee')
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
    )
    
    def sujet_voyage_ou_bateau(self, obj):
        return obj.sujet_voyage if obj.sujet_voyage else obj.bateau
    sujet_voyage_ou_bateau.short_description = 'Voyage'

@admin.register(models.LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('voyage', 'date', 'heure', 'evenements_short', 'position', 'vent_display')
    list_filter = ('voyage', 'date', 'allure', 'origine_position')
    search_fields = ('evenements', 'position', 'vent_force')
    date_hierarchy = 'date'
    
    def evenements_short(self, obj):
        return obj.evenements[:50] + '...' if len(obj.evenements) > 50 else obj.evenements
    evenements_short.short_description = 'Événements'
    
    def vent_display(self, obj):
        if obj.vent_force and obj.vent_direction:
            return f"{obj.vent_force} {obj.vent_direction}"
        return obj.vent_force or '-'
    vent_display.short_description = 'Vent'

@admin.register(models.WeatherCondition)
class WeatherConditionAdmin(admin.ModelAdmin):
    list_display = ('voyage', 'datetime', 'type_bulletin', 'situation_generale_short')
    list_filter = ('voyage', 'datetime', 'type_bulletin')
    search_fields = ('situation_generale', 'type_bulletin')
    date_hierarchy = 'datetime'
    
    def situation_generale_short(self, obj):
        return obj.situation_generale[:50] + '...' if len(obj.situation_generale) > 50 else obj.situation_generale
    situation_generale_short.short_description = 'Situation'

@admin.register(models.VoyageCrewMember)
class VoyageCrewMemberAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'voyage', 'role', 'contact_telephone')
    list_filter = ('role', 'voyage')
    search_fields = ('nom', 'prenom', 'contact_telephone')
    
    def nom_complet(self, obj):
        return f"{obj.prenom} {obj.nom}"
    nom_complet.short_description = 'Nom'

@admin.register(models.VoyageIncident)
class VoyageIncidentAdmin(admin.ModelAdmin):
    list_display = ('voyage', 'datetime', 'type_incident', 'gravite', 'description_short')
    list_filter = ('type_incident', 'gravite', 'voyage', 'datetime')
    search_fields = ('description', 'actions_prises')
    date_hierarchy = 'datetime'
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
