from django.db import migrations
from decimal import Decimal, ROUND_HALF_UP
import math


def compute_distance_nm(lat1, lon1, lat2, lon2):
    # haversine
    rlat1 = math.radians(lat1)
    rlon1 = math.radians(lon1)
    rlat2 = math.radians(lat2)
    rlon2 = math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat/2)**2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    R = 6371000.0
    meters = R * c
    nm = meters / 1852.0
    return Decimal(str(nm)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def forwards(apps, schema_editor):
    LogbookEntry = apps.get_model('nautical', 'LogbookEntry')
    for entry in LogbookEntry.objects.all():
        try:
            if entry.start_lat is not None and entry.start_lng is not None and entry.end_lat is not None and entry.end_lng is not None:
                entry.distance_nm = compute_distance_nm(float(entry.start_lat), float(entry.start_lng), float(entry.end_lat), float(entry.end_lng))
                entry.save()
        except Exception:
            continue


def backwards(apps, schema_editor):
    # nothing to undo
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('nautical', '0006_add_latlng'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
