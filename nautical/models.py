
from django.db import models
import math
from decimal import Decimal, ROUND_HALF_UP
from django.core.validators import FileExtensionValidator

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
    # Numeric latitude/longitude for precise storage and calculations
    start_lat = models.DecimalField('Latitude départ', max_digits=9, decimal_places=6, null=True, blank=True)
    start_lng = models.DecimalField('Longitude départ', max_digits=9, decimal_places=6, null=True, blank=True)
    end_lat = models.DecimalField('Latitude arrivée', max_digits=9, decimal_places=6, null=True, blank=True)
    end_lng = models.DecimalField('Longitude arrivée', max_digits=9, decimal_places=6, null=True, blank=True)
    distance_nm = models.DecimalField('Distance parcourue (NM)', max_digits=7, decimal_places=2, null=True, blank=True)
    # Duration of the trip in hours (computed from start/end datetime)
    duration_hours = models.DecimalField('Durée du trajet (heures)', max_digits=6, decimal_places=2, null=True, blank=True)
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

    def save(self, *args, **kwargs):
        """
        If numeric start/end lat/lng are present, compute great-circle distance
        and store it in `distance_nm` (nautical miles) rounded to 2 decimals.
        """
        try:
            if self.start_lat is not None and self.start_lng is not None and self.end_lat is not None and self.end_lng is not None:
                # haversine formula
                lat1 = float(self.start_lat)
                lon1 = float(self.start_lng)
                lat2 = float(self.end_lat)
                lon2 = float(self.end_lng)
                # convert degrees to radians
                rlat1 = math.radians(lat1)
                rlon1 = math.radians(lon1)
                rlat2 = math.radians(lat2)
                rlon2 = math.radians(lon2)
                dlat = rlat2 - rlat1
                dlon = rlon2 - rlon1
                a = math.sin(dlat/2)**2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                # Earth's radius in meters (mean)
                R = 6371000.0
                meters = R * c
                # convert to nautical miles (1 NM = 1852 meters)
                nm = meters / 1852.0
                # round to 2 decimals using Decimal for consistent DB storage
                self.distance_nm = Decimal(str(nm)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            # compute duration in hours if datetimes present
            if self.start_datetime and self.end_datetime:
                try:
                    delta = (self.end_datetime - self.start_datetime).total_seconds() / 3600.0
                    self.duration_hours = Decimal(str(delta)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                except Exception:
                    pass
        except Exception:
            # if anything fails, skip auto-calculation and leave distance_nm as-is
            pass

        super().save(*args, **kwargs)

    def recalculate_from_events(self):
        """Recalculate voyage totals (distance_nm, duration_hours, avg_speed_kn)
        from its associated VoyageEvent instances ordered by timestamp.
        - distance_nm: sum of segment distances between consecutive events (in NM)
        - duration_hours: hours between first and last event timestamps
        - avg_speed_kn: distance_nm / duration_hours when possible
        """
        try:
            events = list(self.events.all().order_by('timestamp'))
            if not events:
                # no events -> leave values as-is or clear
                self.distance_nm = None
                self.duration_hours = None
                self.avg_speed_kn = None
                super().save(update_fields=['distance_nm', 'duration_hours', 'avg_speed_kn'])
                return

            from decimal import Decimal, ROUND_HALF_UP
            import math

            total_nm = Decimal('0')
            # compute distances between consecutive events
            for i in range(1, len(events)):
                prev = events[i-1]
                cur = events[i]
                if prev.latitude is not None and prev.longitude is not None and cur.latitude is not None and cur.longitude is not None:
                    # haversine
                    def to_rad(x):
                        return math.radians(float(x))
                    rlat1 = to_rad(prev.latitude)
                    rlon1 = to_rad(prev.longitude)
                    rlat2 = to_rad(cur.latitude)
                    rlon2 = to_rad(cur.longitude)
                    dlat = rlat2 - rlat1
                    dlon = rlon2 - rlon1
                    a = math.sin(dlat/2)**2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon/2)**2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    meters = 6371000.0 * c
                    nm = meters / 1852.0
                    total_nm += Decimal(str(nm))
                else:
                    # fallback: if the event has stored distance_from_prev_nm use it
                    if cur.distance_from_prev_nm is not None:
                        total_nm += Decimal(str(cur.distance_from_prev_nm))

            # round and store
            self.distance_nm = total_nm.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_nm != Decimal('0') else None

            # duration: difference between first and last event
            try:
                delta_hours = (events[-1].timestamp - events[0].timestamp).total_seconds() / 3600.0
                self.duration_hours = Decimal(str(delta_hours)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except Exception:
                self.duration_hours = None

            # avg speed
            try:
                if self.distance_nm is not None and self.duration_hours and float(self.duration_hours) > 0:
                    avg = float(self.distance_nm) / float(self.duration_hours)
                    self.avg_speed_kn = Decimal(str(avg)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    self.avg_speed_kn = None
            except Exception:
                self.avg_speed_kn = None

            super().save(update_fields=['distance_nm', 'duration_hours', 'avg_speed_kn'])
        except Exception:
            # keep existing values on error
            pass

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
    # Fichier PDF associé à l'action (ex: procédure, checklist détaillée)
    action = models.FileField(
        'Fichier action (PDF)',
        upload_to='checklists/actions/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text='Télécharger un fichier PDF décrivant l’action ou procédure.'
    )

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


class Chronology(models.Model):
    """Chronologie d'événements à afficher dans une section 'Chronologie'."""
    date = models.DateField('Date')
    time = models.TimeField('Heure', null=True, blank=True)
    description = models.TextField('Description')
    action_realisee = models.TextField("Action réalisée", blank=True)

    class Performer(models.TextChoices):
        TERRY = 'Terry', 'Terry'
        JEAN_ARIEL = 'Jean-Ariel', 'Jean-Ariel'

    performer = models.CharField("Réalisé par", max_length=40, choices=Performer.choices, default=Performer.TERRY)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'Chronologie'
        verbose_name_plural = 'Chronologie'

    def __str__(self):
        t = f" {self.time}" if self.time else ''
        return f"{self.date}{t} — {self.performer}: {self.description[:60]}"


class VoyageEvent(models.Model):
    """An event or period that occurs during a voyage.

    Each event stores a timestamp, an optional GPS position (lat/lng), a short
    description, and optional weather/notes. The model will also store computed
    values relative to the previous event in the same voyage: distance (NM)
    from the previous event, elapsed time (hours) since previous event, and
    average speed (knots) between the two points.
    """
    voyage = models.ForeignKey(LogbookEntry, on_delete=models.CASCADE, related_name='events', verbose_name='Voyage')
    timestamp = models.DateTimeField('Date et heure')
    latitude = models.DecimalField('Latitude', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Longitude', max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField('Détail de l\'événement')
    weather = models.CharField('Conditions météo', max_length=120, blank=True)
    notes = models.TextField('Remarques', blank=True)

    # Computed relative to previous event in the same voyage
    distance_from_prev_nm = models.DecimalField('Distance depuis précédent (NM)', max_digits=7, decimal_places=2, null=True, blank=True)
    elapsed_hours_since_prev = models.DecimalField('Temps écoulé depuis précédent (heures)', max_digits=6, decimal_places=2, null=True, blank=True)
    avg_speed_since_prev_kn = models.DecimalField('Vitesse moyenne depuis précédent (kn)', max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Événement de voyage"
        verbose_name_plural = "Événements de voyage"

    def __str__(self):
        return f"{self.voyage} @ {self.timestamp} — {self.description[:40]}"

    def save(self, *args, **kwargs):
        # Compute distance/speed/elapsed time relative to the previous event
        try:
            prev = VoyageEvent.objects.filter(voyage=self.voyage, timestamp__lt=self.timestamp).order_by('-timestamp').first()
            if prev and self.latitude is not None and self.longitude is not None and prev.latitude is not None and prev.longitude is not None:
                # haversine (meters)
                import math
                def to_rad(x):
                    return math.radians(float(x))
                rlat1 = to_rad(prev.latitude)
                rlon1 = to_rad(prev.longitude)
                rlat2 = to_rad(self.latitude)
                rlon2 = to_rad(self.longitude)
                dlat = rlat2 - rlat1
                dlon = rlon2 - rlon1
                a = math.sin(dlat/2)**2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                R = 6371000.0
                meters = R * c
                nm = meters / 1852.0
                from decimal import Decimal, ROUND_HALF_UP
                self.distance_from_prev_nm = Decimal(str(nm)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                # elapsed hours
                try:
                    delta_hours = (self.timestamp - prev.timestamp).total_seconds() / 3600.0
                    self.elapsed_hours_since_prev = Decimal(str(delta_hours)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                except Exception:
                    self.elapsed_hours_since_prev = None
                # avg speed (knots) = nm / hours
                try:
                    if self.elapsed_hours_since_prev and float(self.elapsed_hours_since_prev) > 0:
                        avg_kn = float(self.distance_from_prev_nm) / float(self.elapsed_hours_since_prev)
                        self.avg_speed_since_prev_kn = Decimal(str(avg_kn)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    else:
                        self.avg_speed_since_prev_kn = None
                except Exception:
                    self.avg_speed_since_prev_kn = None
            else:
                # No previous event or missing coords; clear computed values
                self.distance_from_prev_nm = None
                self.elapsed_hours_since_prev = None
                self.avg_speed_since_prev_kn = None
        except Exception:
            # If any error happens, skip calculations
            pass

        super().save(*args, **kwargs)
        # After saving an event, recompute voyage totals
        try:
            if self.voyage_id:
                self.voyage.recalculate_from_events()
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        voyage = self.voyage
        super().delete(*args, **kwargs)
        try:
            if voyage:
                voyage.recalculate_from_events()
        except Exception:
            pass


# =============================================================================
# NOUVEAUX MODÈLES BASÉS SUR LE LIVRE DE BORD RÉEL
# =============================================================================

class VoyageLog(models.Model):
    """
    Livre de bord d'un voyage complet
    Basé sur la structure du PDF Livre_de_Bord.pdf
    """
    # Informations générales du voyage
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    port_depart = models.CharField(max_length=200, verbose_name="Port de départ")
    port_arrivee = models.CharField(max_length=200, blank=True, verbose_name="Port d'arrivée")
    
    # Navigation
    skipper = models.CharField(max_length=100, verbose_name="Skipper")
    sujet_voyage = models.CharField(max_length=200, verbose_name="Sujet du voyage", help_text="Ex: Séjour à Moorea, Visite des Tuamotu", default="")
    bateau = models.CharField(max_length=100, verbose_name="Nom du bateau")
    immatriculation = models.CharField(max_length=50, blank=True, verbose_name="Immatriculation")
    
    # Statut
    STATUS_CHOICES = [
        ('preparation', 'En préparation'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparation')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Livre de bord"
        verbose_name_plural = "Livres de bord"
        ordering = ['-date_debut']
    
    def __str__(self):
        if self.sujet_voyage:
            return f"{self.sujet_voyage} - {self.port_depart} → {self.port_arrivee} ({self.date_debut})"
        return f"{self.bateau} - {self.port_depart} → {self.port_arrivee} ({self.date_debut})"


class WeatherCondition(models.Model):
    """
    Conditions météorologiques pour un voyage
    Basé sur la section MÉTÉO du PDF
    """
    voyage = models.ForeignKey(VoyageLog, on_delete=models.CASCADE, related_name='conditions_meteo')
    
    # Timing
    datetime = models.DateTimeField(verbose_name="Date et heure")
    type_bulletin = models.CharField(max_length=50, blank=True, verbose_name="Origine du bulletin")
    
    # Situation générale
    situation_generale = models.TextField(blank=True, verbose_name="Situation générale")
    
    # Prévisions jour
    prev_jour_vent = models.CharField(max_length=200, blank=True, verbose_name="Vent prévu (jour)")
    prev_jour_mer = models.CharField(max_length=200, blank=True, verbose_name="Mer prévue (jour)")
    prev_jour_houle = models.CharField(max_length=200, blank=True, verbose_name="Houle prévue (jour)")
    prev_jour_temps = models.CharField(max_length=200, blank=True, verbose_name="Temps prévu (jour)")
    prev_jour_visibilite = models.CharField(max_length=100, blank=True, verbose_name="Visibilité prévue (jour)")
    
    # Prévisions nuit
    prev_nuit_vent = models.CharField(max_length=200, blank=True, verbose_name="Vent prévu (nuit)")
    prev_nuit_mer = models.CharField(max_length=200, blank=True, verbose_name="Mer prévue (nuit)")
    prev_nuit_houle = models.CharField(max_length=200, blank=True, verbose_name="Houle prévue (nuit)")
    prev_nuit_temps = models.CharField(max_length=200, blank=True, verbose_name="Temps prévu (nuit)")
    prev_nuit_visibilite = models.CharField(max_length=100, blank=True, verbose_name="Visibilité prévue (nuit)")
    
    # Tendances ultérieures
    tend_vent = models.CharField(max_length=200, blank=True, verbose_name="Tendance vent")
    tend_mer = models.CharField(max_length=200, blank=True, verbose_name="Tendance mer")
    tend_houle = models.CharField(max_length=200, blank=True, verbose_name="Tendance houle")
    tend_temps = models.CharField(max_length=200, blank=True, verbose_name="Tendance temps")
    tend_visibilite = models.CharField(max_length=100, blank=True, verbose_name="Tendance visibilité")
    
    # Marées
    marees = models.TextField(blank=True, verbose_name="Informations marées")
    
    class Meta:
        verbose_name = "Condition météorologique"
        verbose_name_plural = "Conditions météorologiques"
        ordering = ['datetime']
    
    def __str__(self):
        return f"Météo {self.datetime.strftime('%d/%m %H:%M')} - {self.voyage.bateau}"


class LogEntry(models.Model):
    """
    Entrée de log horodatée dans le livre de bord
    Basé sur le tableau central du PDF
    """
    voyage = models.ForeignKey(VoyageLog, on_delete=models.CASCADE, related_name='entries')
    
    # Timing
    heure = models.TimeField(verbose_name="Heure")
    date = models.DateField(verbose_name="Date")
    
    # Navigation
    log_nautique = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Log nautique")
    cap_compas = models.IntegerField(
        null=True, blank=True,
        verbose_name="Cap compas (°)"
    )
    
    # Événements et observations
    evenements = models.TextField(verbose_name="Événements")
    
    # Conditions de navigation
    vent_force = models.CharField(max_length=50, blank=True, verbose_name="Force du vent")
    vent_direction = models.CharField(max_length=50, blank=True, verbose_name="Direction du vent")
    allure = models.CharField(max_length=50, blank=True, verbose_name="Allure")
    voilure = models.CharField(max_length=200, blank=True, verbose_name="Voilure")
    
    # Position et observations (section droite du PDF)
    position = models.CharField(max_length=200, blank=True, verbose_name="Position")
    origine_position = models.CharField(max_length=100, blank=True, verbose_name="Origine position")
    etat_mer = models.CharField(max_length=100, blank=True, verbose_name="État de la mer")
    sonde = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, verbose_name="Sonde (m)")
    visibilite = models.CharField(max_length=100, blank=True, verbose_name="Visibilité")
    barometre = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, verbose_name="Baromètre (hPa)")
    nuages_temps = models.CharField(max_length=200, blank=True, verbose_name="Nuages/Temps")
    courants = models.CharField(max_length=200, blank=True, verbose_name="Courants")
    
    # Coordonnées GPS (calculées ou saisies)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name="Longitude")
    
    class Meta:
        verbose_name = "Entrée de log"
        verbose_name_plural = "Entrées de log"
        ordering = ['date', 'heure']
    
    def __str__(self):
        return f"{self.date.strftime('%d/%m')} {self.heure.strftime('%H:%M')} - {self.evenements[:50]}..."


class VoyageCrewMember(models.Model):
    """
    Membre d'équipage pour un voyage spécifique
    Basé sur la section ÉQUIPAGE du PDF
    """
    voyage = models.ForeignKey(VoyageLog, on_delete=models.CASCADE, related_name='equipage')
    
    # Informations personnelles
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    
    # Rôle à bord
    ROLE_CHOICES = [
        ('skipper', 'Skipper'),
        ('equipier', 'Équipier'),
        ('chef_de_bord', 'Chef de bord'),
        ('second', 'Second'),
        ('cuisinier', 'Cuisinier'),
        ('mecanicien', 'Mécanicien'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='equipier', verbose_name="Rôle")
    
    # Contact d'urgence
    contact_nom = models.CharField(max_length=100, blank=True, verbose_name="Contact prévu - Nom")
    contact_telephone = models.CharField(max_length=20, blank=True, verbose_name="Contact prévu - Téléphone")
    contact_relation = models.CharField(max_length=100, blank=True, verbose_name="Contact prévu - Relation")
    
    # Dates de participation
    date_embarquement = models.DateField(null=True, blank=True, verbose_name="Date d'embarquement")
    date_debarquement = models.DateField(null=True, blank=True, verbose_name="Date de débarquement")
    
    class Meta:
        verbose_name = "Membre d'équipage voyage"
        verbose_name_plural = "Membres d'équipage voyage"
        ordering = ['role', 'nom']
    
    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.get_role_display()})"


class VoyageIncident(models.Model):
    """
    Incidents de personnes et matériel
    Basé sur la section INCIDENTS du PDF
    """
    voyage = models.ForeignKey(VoyageLog, on_delete=models.CASCADE, related_name='incidents')
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, null=True, blank=True, related_name='incidents')
    
    # Timing
    datetime = models.DateTimeField(verbose_name="Date et heure")
    
    # Type d'incident
    TYPE_CHOICES = [
        ('personne', 'Incident de personne'),
        ('materiel', 'Incident matériel'),
        ('navigation', 'Incident de navigation'),
        ('meteo', 'Incident météorologique'),
    ]
    type_incident = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type d'incident")
    
    # Gravité
    GRAVITE_CHOICES = [
        ('mineur', 'Mineur'),
        ('moyen', 'Moyen'),
        ('grave', 'Grave'),
        ('critique', 'Critique'),
    ]
    gravite = models.CharField(max_length=20, choices=GRAVITE_CHOICES, default='mineur', verbose_name="Gravité")
    
    # Description
    description = models.TextField(verbose_name="Description de l'incident")
    actions_prises = models.TextField(blank=True, verbose_name="Actions prises")
    
    # Personnes concernées
    personnes_concernees = models.ManyToManyField(VoyageCrewMember, blank=True, verbose_name="Personnes concernées")
    
    class Meta:
        verbose_name = "Incident voyage"
        verbose_name_plural = "Incidents voyage"
        ordering = ['datetime']
    
    def __str__(self):
        return f"{self.get_type_incident_display()} - {self.datetime.strftime('%d/%m %H:%M')} - {self.get_gravite_display()}"
