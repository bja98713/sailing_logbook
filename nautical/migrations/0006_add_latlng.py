from django.db import migrations, models
import re


def parse_coord(text):
    if not text:
        return None
    # try to find decimal lat,lng
    m = re.search(r"([-+]?\d+\.\d+)[ ,/]+([-+]?\d+\.\d+)", text)
    if m:
        return float(m.group(1)), float(m.group(2))
    # fallback: no parse
    return None


def forwards(apps, schema_editor):
    LogbookEntry = apps.get_model('nautical', 'LogbookEntry')
    for entry in LogbookEntry.objects.all():
        s = parse_coord(entry.start_position)
        if s:
            entry.start_lat = round(s[0], 6)
            entry.start_lng = round(s[1], 6)
        e = parse_coord(entry.end_position)
        if e:
            entry.end_lat = round(e[0], 6)
            entry.end_lng = round(e[1], 6)
        entry.save()


def backwards(apps, schema_editor):
    # nothing to do on reverse (we keep the numeric fields)
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('nautical', '0005_chronology'),
    ]

    operations = [
        migrations.AddField(
            model_name='logbookentry',
            name='start_lat',
            field=models.DecimalField(decimal_places=6, max_digits=9, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='logbookentry',
            name='start_lng',
            field=models.DecimalField(decimal_places=6, max_digits=9, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='logbookentry',
            name='end_lat',
            field=models.DecimalField(decimal_places=6, max_digits=9, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='logbookentry',
            name='end_lng',
            field=models.DecimalField(decimal_places=6, max_digits=9, null=True, blank=True),
        ),
        migrations.RunPython(forwards, backwards),
    ]
