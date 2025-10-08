"""
Nouveaux modèles Django basés sur la structure réelle du livre de bord
Analysé depuis Livre_de_Bord.pdf
"""
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class VoyageLogNew(models.Model):
    """
    Livre de bord d'un voyage complet
    Basé sur l'en-tête du document PDF
    """
    # Informations générales du voyage
    date_debut = models.DateField(verbose_name="Date de début", default=timezone.now)
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    port_depart = models.CharField(max_length=200, verbose_name="Port de départ")
    port_arrivee = models.CharField(max_length=200, blank=True, verbose_name="Port d'arrivée")
    
    # Navigation
    skipper = models.CharField(max_length=100, verbose_name="Skipper")
    sujet_voyage = models.CharField(max_length=200, verbose_name="Sujet du voyage", help_text="Ex: Séjour à Moorea, Visite des Tuamotu")
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
        return f"{self.sujet_voyage} - {self.port_depart} → {self.port_arrivee} ({self.date_debut})"
    
    def get_absolute_url(self):
        return reverse('voyage_log_detail', kwargs={'pk': self.pk})


class WeatherConditionNew(models.Model):
    """
    Conditions météorologiques pour un voyage
    Basé sur la section MÉTÉO du PDF
    """
    voyage = models.ForeignKey(VoyageLogNew, on_delete=models.CASCADE, related_name='conditions_meteo')
    
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


class LogEntryNew(models.Model):
    """
    Entrée de log horodatée dans le livre de bord
    Basé sur le tableau central du PDF
    """
    voyage = models.ForeignKey(VoyageLogNew, on_delete=models.CASCADE, related_name='entries')
    
    # Timing
    heure = models.TimeField(verbose_name="Heure")
    date = models.DateField(verbose_name="Date", default=timezone.now)
    
    # Navigation
    log_nautique = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Log nautique")
    cap_compas = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(360)],
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
    
    @property
    def datetime(self):
        """Combine date et heure pour faciliter l'affichage chronologique"""
        return timezone.datetime.combine(self.date, self.heure)


class CrewMemberNew(models.Model):
    """
    Membre d'équipage pour un voyage
    Basé sur la section ÉQUIPAGE du PDF
    """
    voyage = models.ForeignKey(VoyageLogNew, on_delete=models.CASCADE, related_name='equipage')
    
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
        verbose_name = "Membre d'équipage"
        verbose_name_plural = "Membres d'équipage"
        ordering = ['role', 'nom']
    
    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.get_role_display()})"

    @property
    def full_name(self) -> str:
        """Nom complet pratique pour l'affichage."""
        return f"{self.prenom} {self.nom}".strip()


class IncidentNew(models.Model):
    """
    Incidents de personnes et matériel
    Basé sur la section INCIDENTS du PDF
    """
    voyage = models.ForeignKey(VoyageLogNew, on_delete=models.CASCADE, related_name='incidents')
    log_entry = models.ForeignKey(LogEntryNew, on_delete=models.CASCADE, null=True, blank=True, related_name='incidents')
    
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
    personnes_concernees = models.ManyToManyField(CrewMemberNew, blank=True, verbose_name="Personnes concernées")
    
    class Meta:
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"
        ordering = ['datetime']
    
    def __str__(self):
        return f"{self.get_type_incident_display()} - {self.datetime.strftime('%d/%m %H:%M')} - {self.get_gravite_display()}"


class SecurityInstruction(models.Model):
    """
    Consignes de sécurité pour le voyage
    Basé sur la section CONSIGNES DE SÉCURITÉ du PDF
    """
    voyage = models.ForeignKey(VoyageLogNew, on_delete=models.CASCADE, related_name='consignes_securite')
    
    # Contenu
    titre = models.CharField(max_length=200, verbose_name="Titre de la consigne")
    description = models.TextField(verbose_name="Description détaillée")
    
    # Priorité
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='normale', verbose_name="Priorité")
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Consigne de sécurité"
        verbose_name_plural = "Consignes de sécurité"
        ordering = ['-priorite', 'titre']
    
    def __str__(self):
        return f"{self.titre} ({self.get_priorite_display()})"