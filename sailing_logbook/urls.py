
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from nautical import views, api

router = routers.DefaultRouter()
router.register(r'crew', api.CrewMemberViewSet)
router.register(r'voyages', api.LogbookEntryViewSet)
router.register(r'maintenance', api.MaintenanceRecordViewSet)
router.register(r'checklists', api.ChecklistViewSet)
router.register(r'checklist-items', api.ChecklistItemViewSet)
router.register(r'media', api.MediaAssetViewSet)
router.register(r'consommables', api.ConsumableViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('voyages/', views.LogbookListView.as_view(), name='voyage_list'),
    path('voyages/new/', views.LogbookCreateView.as_view(), name='voyage_create'),
    path('voyages/<int:pk>/', views.LogbookDetailView.as_view(), name='voyage_detail'),
    path('voyages/<int:pk>/upload/', views.MediaUploadView.as_view(), name='voyage_media_upload'),
    path('equipage/', views.CrewListView.as_view(), name='crew_list'),
    path('maintenance/', views.MaintenanceListView.as_view(), name='maintenance_list'),
    path('checklists/', views.ChecklistListView.as_view(), name='checklist_list'),
    path('api/', include(router.urls)),
    path('voyages/<int:pk>/edit/', views.LogbookUpdateView.as_view(), name='voyage_edit'),
    path('voyages/<int:pk>/delete/', views.LogbookDeleteView.as_view(), name='voyage_delete'),
    # Consommables
    path('consommables/', views.ConsumableListView.as_view(), name='consumable_list'),
    path('consommables/new/', views.ConsumableCreateView.as_view(), name='consumable_create'),
    path('consommables/<int:pk>/edit/', views.ConsumableUpdateView.as_view(), name='consumable_edit'),
    path('consommables/<int:pk>/delete/', views.ConsumableDeleteView.as_view(), name='consumable_delete'),
    path('consommables/export/pdf/', views.ConsumablePdfView.as_view(), name='consumable_export_pdf'),
    # Frontend React (build statique)
    path('frontend/consommables/', lambda req: __import__('django.shortcuts').shortcuts.render(req, 'nautical/consumable_frontend.html'), name='consumable_frontend'),

] + (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else [])
