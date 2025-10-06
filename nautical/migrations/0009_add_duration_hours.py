from django.db import migrations, models
import decimal

class Migration(migrations.Migration):

    dependencies = [
        ('nautical', '0008_merge_0007'),
    ]

    operations = [
        migrations.AddField(
            model_name='logbookentry',
            name='duration_hours',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, verbose_name='Durée du trajet (heures)'),
        ),
    ]
