
from django.db import models

class CrewRole(models.TextChoices):
    SKIPPER = 'Skipper', 'Skipper'
    EQUIPIER = 'Équipier', 'Équipier'
    INVITE = 'Invité', 'Invité'

class EquipmentType(models.TextChoices):
    MOTEUR = 'Moteur', 'Moteur'
    GREEMENT = 'Gréement', 'Gréement'
    ELECTRONIQUE = 'Électronique', 'Électronique'
    VOILES = 'Voiles', 'Voiles'
    COQUE = 'Coque', 'Coque'
    DIVERS = 'Divers', 'Divers'

class CrewMember(models.Model):
    full_name = models.CharField('Nom / Prénom', max_length=120)
    role = models.CharField('Rôle', max_length=30, choices=CrewRole.choices, default=CrewRole.EQUIPIER)
    contact = models.CharField('Téléphone / Email', max_length=200, blank=True)
    has_license = models.BooleanField('Licence FFV / Assur.', default=False)
    notes = models.TextField('Remarques', blank=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = "Membre d'équipage"
        verbose_name_plural = 'Équipage'

    def __str__(self):
        return self.full_name

class LogbookEntry(models.Model):
    start_datetime = models.DateTimeField('Date de départ')
    end_datetime = models.DateTimeField('Date d’arrivée', null=True, blank=True)
    departure_port = models.CharField('Port / Mouillage départ', max_length=120)
    arrival_port = models.CharField('Port / Mouillage arrivée', max_length=120, blank=True)
    start_position = models.CharField('Position départ', max_length=80, blank=True, help_text="Ex: 17°32'S / 149°34'W")
    end_position = models.CharField('Position arrivée', max_length=80, blank=True)
    distance_nm = models.DecimalField('Distance parcourue (NM)', max_digits=7, decimal_places=2, null=True, blank=True)
    avg_speed_kn = models.DecimalField('Vitesse moyenne (kn)', max_digits=5, decimal_places=2, null=True, blank=True)
    weather = models.CharField('Conditions météo', max_length=120, blank=True)
    wind = models.CharField('Vent (dir/force)', max_length=80, blank=True)
    sea_state = models.CharField('État de la mer / houle', max_length=80, blank=True)
    tide_current = models.CharField('Marée / Courant', max_length=80, blank=True)
    avg_course = models.IntegerField('Cap moyen suivi', null=True, blank=True)
    engine_hours = models.DecimalField('Moteur – heures de marche', max_digits=6, decimal_places=1, null=True, blank=True)
    fuel_liters = models.DecimalField('Carburant consommé (L)', max_digits=7, decimal_places=2, null=True, blank=True)
    crew = models.ManyToManyField(CrewMember, verbose_name='Équipage', related_name='voyages', blank=True)
    notes = models.TextField('Incidents / Notes', blank=True)
    photos_url = models.URLField('Photos / Vidéos (URL)', blank=True)
    cover_photo = models.ImageField('Photo de couverture', upload_to='voyages/covers/', blank=True, null=True)

    class Meta:
        ordering = ['-start_datetime']
        verbose_name = 'Voyage'
        verbose_name_plural = 'Logbook (Voyages)'

    def __str__(self):
        return f"{self.departure_port} → {self.arrival_port or '—'} ({self.start_datetime.date()})"

class MaintenanceRecord(models.Model):
    date = models.DateField('Date intervention')
    equipment = models.CharField('Équipement concerné', max_length=30, choices=EquipmentType.choices, default=EquipmentType.DIVERS)
    description = models.TextField('Description')
    cost_eur = models.DecimalField('Coût (€)', max_digits=9, decimal_places=2, null=True, blank=True)
    engine_hours_at_time = models.IntegerField('Heure moteur liée', null=True, blank=True)
    voyage = models.ForeignKey(LogbookEntry, verbose_name='Lien voyage', on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance')
    next_due_date = models.DateField('Prochaine échéance', null=True, blank=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Maintenance'
        verbose_name_plural = 'Maintenance'

    def __str__(self):
        return f"{self.get_equipment_display()} – {self.date}"

class Checklist(models.Model):
    name = models.CharField('Nom checklist', max_length=120)
    description = models.TextField('Description', blank=True)

    class Meta:
        verbose_name = 'Checklist'
        verbose_name_plural = 'Checklists'

    def __str__(self):
        return self.name

class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items', verbose_name='Checklist')
    label = models.CharField('Élément', max_length=200)
    required = models.BooleanField('Obligatoire', default=False)

    class Meta:
        ordering = ['id']
        verbose_name = 'Élément de checklist'
        verbose_name_plural = 'Éléments de checklist'

    def __str__(self):
        return self.label

class ChecklistRun(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='runs', verbose_name='Checklist')
    voyage = models.ForeignKey(LogbookEntry, on_delete=models.CASCADE, related_name='checklist_runs', verbose_name='Voyage')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('checklist', 'voyage')
        verbose_name = 'Checklist (instance)'
        verbose_name_plural = 'Checklists (instances)'

    def __str__(self):
        return f"{self.checklist.name} – {self.voyage}"

class ChecklistItemRun(models.Model):
    run = models.ForeignKey(ChecklistRun, on_delete=models.CASCADE, related_name='item_runs', verbose_name='Instance')
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='runs', verbose_name='Élément')
    checked = models.BooleanField('Coché', default=False)
    note = models.CharField('Note', max_length=200, blank=True)

    class Meta:
        unique_together = ('run', 'item')
        verbose_name = 'Élément coché'
        verbose_name_plural = 'Éléments cochés'

    def __str__(self):
        return f"{self.item.label} ({'OK' if self.checked else 'À faire'})"

class MediaKind(models.TextChoices):
    PHOTO = 'photo', 'Photo'
    VIDEO = 'video', 'Vidéo'

class MediaAsset(models.Model):
    voyage = models.ForeignKey(LogbookEntry, on_delete=models.CASCADE, related_name='media_assets', verbose_name='Voyage')
    kind = models.CharField('Type', max_length=10, choices=MediaKind.choices, default=MediaKind.PHOTO)
    image = models.ImageField('Image', upload_to='voyages/photos/', blank=True, null=True)
    file = models.FileField('Fichier', upload_to='voyages/files/', blank=True, null=True)
    caption = models.CharField('Légende', max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media'
        verbose_name_plural = 'Médias'

    def __str__(self):
        return f"{self.get_kind_display()} – {self.voyage}"

from django.core.validators import FileExtensionValidator

class ConsumableOrigin(models.TextChoices):
    MOTEUR = 'moteur', 'Moteur'
    ELECTRICITE = 'electricite', 'Électricité'
    ELECTRONIQUE = 'electronique', 'Électronique'
    ACCASTILLAGE = 'accastillage', 'Accastillage'
    NAVIGATION = 'navigation', 'Navigation'
    OSMOSEUR = 'osmoseur', 'Osmoseur'
    DIVERS = 'divers', 'Divers'

class Consumable(models.Model):
    name = models.CharField("Nom du consommable", max_length=150)
    origin = models.CharField("Origine", max_length=20, choices=ConsumableOrigin.choices, default=ConsumableOrigin.DIVERS)
    reference = models.CharField("Référence", max_length=150, blank=True)
    # On accepte JPG/JPEG/PNG en aperçu, et DNG en téléchargement (pas d’aperçu navigateur)
    image = models.FileField(
        "Image (jpg/jpeg/png) ou DNG",
        upload_to="consommables/",
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "dng"])],
        help_text="Formats acceptés : jpg, jpeg, png, dng"
    )
    remark = models.TextField("Remarque", blank=True)
    quantity = models.PositiveIntegerField("Quantité", default=0)
    price_eur = models.DecimalField("Prix (€)", max_digits=9, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Consommable"
        verbose_name_plural = "Consommables"
        constraints = [
            models.UniqueConstraint(fields=["name", "origin", "reference"], name="uniq_consumable_name_origin_ref")
        ]

    def __str__(self):
        ref = f" ({self.reference})" if self.reference else ""
        return f"{self.name}{ref}"
