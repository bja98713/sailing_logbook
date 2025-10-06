"""Backfill voyage totals (distance, duration, avg speed) from VoyageEvent records.

This migration calls the runtime model method `recalculate_from_events()` for
each LogbookEntry. It imports the live model to run the helper which contains
the up-to-date logic. The operation is idempotent.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    # Import the runtime model (not the historical apps.get_model) because we
    # want to use the helper method implemented on the class.
    try:
        from nautical.models import LogbookEntry
    except Exception as e:
        # If import fails, skip silently (migration should not crash in unusual envs)
        print('Could not import LogbookEntry for backfill:', e)
        return

    qs = LogbookEntry.objects.all()
    total = qs.count()
    print(f'Recalculating voyage totals from events for {total} voyages...')
    for i, v in enumerate(qs, 1):
        try:
            v.recalculate_from_events()
        except Exception as exc:
            # continue on error but report to stdout
            print(f'Error recalculating voyage {v.pk}:', exc)


def reverse(apps, schema_editor):
    # no-op reverse
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('nautical', '0010_voyageevent'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=reverse),
    ]
