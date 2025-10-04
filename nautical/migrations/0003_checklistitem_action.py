"""Add action FileField to ChecklistItem

Revision ID: 0003_checklistitem_action
Revises: 0002_consumable_and_more
Create Date: 2025-10-03
"""
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('nautical', '0002_consumable_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='checklistitem',
            name='action',
            field=models.FileField(blank=True, null=True, upload_to='checklists/actions/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])], verbose_name='Fichier action (PDF)', help_text='Télécharger un fichier PDF décrivant l’action ou procédure.'),
        ),
    ]