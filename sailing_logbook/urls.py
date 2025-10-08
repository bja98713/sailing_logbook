
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from nautical import views, api
from nautical import views_new

router = routers.DefaultRouter()
router.register(r'crew', api.CrewMemberViewSet)
router.register(r'voyages', api.LogbookEntryViewSet)
router.register(r'maintenance', api.MaintenanceRecordViewSet)
router.register(r'checklists', api.ChecklistViewSet)
router.register(r'checklist-items', api.ChecklistItemViewSet)
router.register(r'media', api.MediaAssetViewSet)
router.register(r'consommables', api.ConsumableViewSet)
router.register(r'events', api.VoyageEventViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('equipage/', views.CrewListView.as_view(), name='crew_list'),
    path('maintenance/', views.MaintenanceListView.as_view(), name='maintenance_list'),
    path('checklists/', views.ChecklistListView.as_view(), name='checklist_list'),
    path('checklists/new/', views.ChecklistCreateView.as_view(), name='checklist_create'),
    path('checklists/<int:pk>/edit/', views.ChecklistUpdateView.as_view(), name='checklist_edit'),
    path('checklists/<int:pk>/delete/', views.ChecklistDeleteView.as_view(), name='checklist_delete'),
    path('chronologie/', views.ChronologyListView.as_view(), name='chronology_list'),
    path('chronologie/new/', views.ChronologyCreateView.as_view(), name='chronology_create'),
    path('chronologie/<int:pk>/edit/', views.ChronologyUpdateView.as_view(), name='chronology_edit'),
    path('chronologie/<int:pk>/delete/', views.ChronologyDeleteView.as_view(), name='chronology_delete'),
    path('api/', include(router.urls)),
    # Consommables
    path('consommables/', views.ConsumableListView.as_view(), name='consumable_list'),
    path('consommables/new/', views.ConsumableCreateView.as_view(), name='consumable_create'),
    path('consommables/<int:pk>/edit/', views.ConsumableUpdateView.as_view(), name='consumable_edit'),
    path('consommables/<int:pk>/delete/', views.ConsumableDeleteView.as_view(), name='consumable_delete'),
    path('consommables/export/pdf/', views.ConsumablePdfView.as_view(), name='consumable_export_pdf'),
    # Frontend React (build statique)
    path('frontend/consommables/', lambda req: __import__('django.shortcuts').shortcuts.render(req, 'nautical/consumable_frontend.html'), name='consumable_frontend'),
    
    # === NOUVEAU SYSTÈME DE LIVRE DE BORD ===
    # Import des vues du nouveau système
    path('livres-de-bord/', views_new.VoyageLogListView.as_view(), name='voyage_log_list'),
    path('livres-de-bord/nouveau/', views_new.VoyageLogCreateView.as_view(), name='voyage_log_create'),
    path('livres-de-bord/<int:pk>/', views_new.VoyageLogDetailView.as_view(), name='voyage_log_detail'),
    path('livres-de-bord/<int:pk>/edit/', views_new.VoyageLogUpdateView.as_view(), name='voyage_log_update'),
    path('livres-de-bord/<int:pk>/delete/', views_new.voyage_log_delete_view, name='voyage_log_delete'),
    path('livres-de-bord/<int:pk>/live/', views_new.voyage_log_live_view, name='voyage_log_live'),
    path('livres-de-bord/<int:pk>/export/pdf/', views_new.export_voyage_pdf, name='export_voyage_pdf'),
    
    # Entrées de log
    path('livres-de-bord/<int:voyage_pk>/log/nouveau/', views_new.add_log_entry, name='add_log_entry'),
    path('livres-de-bord/<int:voyage_pk>/log/<int:entry_pk>/edit/', views_new.edit_log_entry, name='edit_log_entry'),
    
    # Météo
    path('livres-de-bord/<int:voyage_pk>/meteo/nouveau/', views_new.add_weather_condition, name='add_weather_condition'),
    
    # Équipage
    path('livres-de-bord/<int:voyage_pk>/equipage/nouveau/', views_new.add_crew_member, name='add_crew_member'),
    
    # Incidents
    path('livres-de-bord/<int:voyage_pk>/incident/nouveau/', views_new.add_incident, name='add_incident'),
    
    # API pour mode live
    path('livres-de-bord/<int:pk>/api/entries/', views_new.voyage_log_api_entries, name='voyage_log_api_entries'),
    
    # Dashboard
    path('dashboard/', views_new.voyage_dashboard, name='voyage_dashboard'),

] + (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else [])
