
from rest_framework import serializers, viewsets
from .models import CrewMember, LogbookEntry, MaintenanceRecord, Checklist, ChecklistItem, MediaAsset

class CrewMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewMember
        fields = '__all__'

class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = ['id', 'voyage', 'kind', 'image', 'file', 'caption', 'created_at']

class LogbookEntrySerializer(serializers.ModelSerializer):
    crew = CrewMemberSerializer(many=True, read_only=True)
    media_assets = MediaAssetSerializer(many=True, read_only=True)

    class Meta:
        model = LogbookEntry
        fields = '__all__'

class MaintenanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRecord
        fields = '__all__'

class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        # expose the new action file field
        fields = '__all__'

class ChecklistSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True, read_only=True)
    class Meta:
        model = Checklist
        fields = ['id', 'name', 'description', 'items']

class CrewMemberViewSet(viewsets.ModelViewSet):
    queryset = CrewMember.objects.all()
    serializer_class = CrewMemberSerializer

class LogbookEntryViewSet(viewsets.ModelViewSet):
    queryset = LogbookEntry.objects.all().prefetch_related('crew', 'media_assets')
    serializer_class = LogbookEntrySerializer

class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.all()
    serializer_class = MaintenanceRecordSerializer

class ChecklistItemViewSet(viewsets.ModelViewSet):
    queryset = ChecklistItem.objects.all()
    serializer_class = ChecklistItemSerializer

class ChecklistViewSet(viewsets.ModelViewSet):
    queryset = Checklist.objects.all()
    serializer_class = ChecklistSerializer

class MediaAssetViewSet(viewsets.ModelViewSet):
    queryset = MediaAsset.objects.all()
    serializer_class = MediaAssetSerializer

from .models import Consumable
from rest_framework import serializers, viewsets

class ConsumableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumable
        fields = "__all__"

class ConsumableViewSet(viewsets.ModelViewSet):
    queryset = Consumable.objects.all()
    serializer_class = ConsumableSerializer


from .models import VoyageEvent
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class VoyageEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoyageEvent
        fields = '__all__'

class VoyageEventViewSet(viewsets.ModelViewSet):
    queryset = VoyageEvent.objects.all().select_related('voyage')
    serializer_class = VoyageEventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        voyage_id = self.request.query_params.get('voyage')
        if voyage_id:
            return qs.filter(voyage_id=voyage_id).order_by('timestamp')
        return qs.order_by('-timestamp')
