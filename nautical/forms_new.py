"""
Formulaires pour le nouveau système de livre de bord
Basés sur les modèles créés à partir de Livre_de_Bord.pdf
"""
from django import forms
from django.forms import inlineformset_factory
from .models_new import VoyageLogNew, LogEntryNew, WeatherConditionNew, CrewMemberNew, IncidentNew


class VoyageLogForm(forms.ModelForm):
    """Formulaire principal pour créer un nouveau voyage"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formater les dates au format français pour l'affichage
        if self.instance and self.instance.pk:
            if self.instance.date_debut:
                self.fields['date_debut'].initial = self.instance.date_debut.strftime('%d/%m/%Y')
            if self.instance.date_fin:
                self.fields['date_fin'].initial = self.instance.date_fin.strftime('%d/%m/%Y')
    
    def clean_date_debut(self):
        date_str = self.cleaned_data.get('date_debut')
        if not date_str:
            raise forms.ValidationError("La date de début est obligatoire")
        
        # Essayer plusieurs formats
        from datetime import datetime
        formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except (ValueError, TypeError):
                continue
        
        raise forms.ValidationError("Format de date invalide. Utilisez JJ/MM/AAAA ou AAAA-MM-JJ")
    
    def clean_date_fin(self):
        date_str = self.cleaned_data.get('date_fin')
        if not date_str:
            return None  # Date de fin optionnelle
        
        # Essayer plusieurs formats
        from datetime import datetime
        formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except (ValueError, TypeError):
                continue
        
        raise forms.ValidationError("Format de date invalide. Utilisez JJ/MM/AAAA ou AAAA-MM-JJ")
    
    class Meta:
        model = VoyageLogNew
        fields = [
            'date_debut', 'date_fin', 'port_depart', 'port_arrivee',
            'sujet_voyage', 'statut'
        ]
        widgets = {
            'date_debut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '06/10/2025'}),
            'date_fin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '15/10/2025 (optionnel)'}),
            'port_depart': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Port ou mouillage de départ'}),
            'port_arrivee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Port ou mouillage d\'arrivée'}),
            'sujet_voyage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Séjour à Moorea, Visite des Tuamotu'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        # Forcer le nom du bateau
        obj.bateau = 'MANTA'
        # Préremplir skipper si absent (champ masqué)
        if not obj.skipper:
            try:
                last = type(obj).objects.exclude(skipper='').order_by('-created_at').first()
                obj.skipper = last.skipper if last and last.skipper else 'Skipper'
            except Exception:
                obj.skipper = 'Skipper'
        # Si aucune immatriculation fournie (champ masqué), conserver l'existant ou reprendre la dernière utilisée
        if not obj.immatriculation:
            try:
                last = type(obj).objects.exclude(immatriculation='').order_by('-created_at').first()
                if last and last.immatriculation:
                    obj.immatriculation = last.immatriculation
            except Exception:
                pass
        if commit:
            obj.save()
        return obj


class LogEntryNewForm(forms.ModelForm):
    """Formulaire pour ajouter une entrée de log en temps réel"""
    
    class Meta:
        model = LogEntryNew
        fields = [
            'date', 'heure', 'log_nautique', 'cap_compas', 'evenements',
            'vent_force', 'vent_direction', 'allure', 'voilure',
            'position', 'origine_position', 'etat_mer', 'sonde',
            'visibilite', 'barometre', 'nuages_temps', 'courants',
            'latitude', 'longitude'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'heure': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'log_nautique': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'cap_compas': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '360'}),
            'evenements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vent_force': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Force 4'}),
            'vent_direction': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: NE'}),
            'allure': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Choisir...'),
                ('moteur', 'Moteur'),
                ('pres_du_vent', 'Près du vent'),
                ('bon_plein', 'Bon plein'),
                ('largue', 'Largue'),
                ('grand_largue', 'Grand largue'),
                ('vent_arriere', 'Vent arrière'),
            ]),
            'voilure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: GV + Foc'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 17°35\'S / 149°36\'W'}),
            'origine_position': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Choisir...'),
                ('gps', 'GPS'),
                ('estime', 'Estime'),
                ('releve', 'Relevé'),
                ('radar', 'Radar'),
            ]),
            'etat_mer': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Choisir...'),
                ('calme', 'Calme'),
                ('belle', 'Belle'),
                ('peu_agitee', 'Peu agitée'),
                ('agitee', 'Agitée'),
                ('forte', 'Forte'),
                ('tres_forte', 'Très forte'),
            ]),
            'sonde': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Profondeur en m'}),
            'visibilite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Bonne (>10NM)'}),
            'barometre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Pression en hPa'}),
            'nuages_temps': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Nuageux, grain'}),
            'courants': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Direction et force'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir la date et l'heure actuelles pour les nouvelles entrées
        if not self.instance.pk:
            from django.utils import timezone
            now = timezone.now()
            self.fields['date'].initial = now.date()
            self.fields['heure'].initial = now.time()


class QuickLogEntryNewForm(forms.ModelForm):
    """Formulaire simplifié pour saisie rapide d'événements"""
    
    class Meta:
        model = LogEntryNew
        fields = ['heure', 'evenements', 'position']
        widgets = {
            'heure': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'evenements': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Que se passe-t-il ?'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '17°35\'S / 149°36\'W (optionnel)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            from django.utils import timezone
            now = timezone.now()
            self.fields['heure'].initial = now.time()


class WeatherConditionNewForm(forms.ModelForm):
    """Formulaire pour saisir les conditions météorologiques"""
    
    class Meta:
        model = WeatherConditionNew
        fields = [
            'datetime', 'type_bulletin', 'situation_generale',
            'prev_jour_vent', 'prev_jour_mer', 'prev_jour_houle', 'prev_jour_temps', 'prev_jour_visibilite',
            'prev_nuit_vent', 'prev_nuit_mer', 'prev_nuit_houle', 'prev_nuit_temps', 'prev_nuit_visibilite',
            'tend_vent', 'tend_mer', 'tend_houle', 'tend_temps', 'tend_visibilite',
            'marees'
        ]
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'type_bulletin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Météo France'}),
            'situation_generale': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
            # Prévisions jour
            'prev_jour_vent': forms.TextInput(attrs={'class': 'form-control'}),
            'prev_jour_mer': forms.TextInput(attrs={'class': 'form-control'}),
            'prev_jour_houle': forms.TextInput(attrs={'class': 'form-control'}),
            'prev_jour_temps': forms.TextInput(attrs={'class': 'form-control'}),
            'prev_jour_visibilite': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Prévisions nuit
            'prev_nuit_vent': forms.TextInput(attrs={'class': 'form-control'}),
            'prev_nuit_mer': forms.TextInput(attrs={'class': 'form-control'}),
            'prev_nuit_houle': forms.TextInput(attrs={'class': 'form-control'}),
            'prev_nuit_temps': forms.TextInput(attrs={'class': 'form-control'}),
            'prev_nuit_visibilite': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Tendances
            'tend_vent': forms.TextInput(attrs={'class': 'form-control'}),
            'tend_mer': forms.TextInput(attrs={'class': 'form-control'}),
            'tend_houle': forms.TextInput(attrs={'class': 'form-control'}),
            'tend_temps': forms.TextInput(attrs={'class': 'form-control'}),
            'tend_visibilite': forms.TextInput(attrs={'class': 'form-control'}),
            
            'marees': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['datetime'].initial = timezone.now()


class CrewMemberNewForm(forms.ModelForm):
    """Formulaire pour ajouter un membre d'équipage"""
    
    # Champ pour choisir dans la liste existante
    existing_member = forms.ModelChoiceField(
        queryset=None,  # Sera défini dans __init__
        required=False,
        empty_label="-- Choisir dans la liste existante --",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'existing_member'}),
        label="Membre existant"
    )
    
    class Meta:
        model = CrewMemberNew
        fields = [
            'nom', 'prenom', 'role',
            'contact_nom', 'contact_telephone', 'contact_relation',
            'date_embarquement', 'date_debarquement'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'id': 'new_nom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'id': 'new_prenom'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'contact_nom': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_telephone': forms.TextInput(attrs={'class': 'form-control', 'id': 'new_telephone'}),
            'contact_relation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Époux/se, Parent'}),
            'date_embarquement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'JJ/MM/AAAA'}),
            'date_debarquement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'JJ/MM/AAAA (optionnel)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models_new import CrewMemberNew
        # Charger la liste des membres existants (trier par nom puis prénom)
        self.fields['existing_member'].queryset = CrewMemberNew.objects.all().order_by('nom', 'prenom')
        
        # Pré-remplir les dates par défaut
        if not self.instance.pk:
            from datetime import date
            self.fields['date_embarquement'].initial = date.today().strftime('%d/%m/%Y')
    
    def clean(self):
        cleaned_data = super().clean()
        existing_member = cleaned_data.get('existing_member')
        nom = cleaned_data.get('nom')
        prenom = cleaned_data.get('prenom')
        
        # Si un membre existant est sélectionné, on n'exige pas nom/prenom
        if existing_member:
            # Extraire nom et prénom du membre existant
            # Pré-remplir avec les champs du modèle
            cleaned_data['nom'] = existing_member.nom
            cleaned_data['prenom'] = existing_member.prenom
        else:
            # Si pas de membre existant, vérifier qu'on a nom et prénom
            if not nom:
                raise forms.ValidationError("Le nom est obligatoire pour un nouveau membre")
            if not prenom:
                raise forms.ValidationError("Le prénom est obligatoire pour un nouveau membre")
        
        return cleaned_data
    
    def clean_date_embarquement(self):
        date_str = self.cleaned_data.get('date_embarquement')
        if not date_str:
            return None
        
        # Essayer plusieurs formats
        from datetime import datetime
        formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except (ValueError, TypeError):
                continue
        
        raise forms.ValidationError("Format de date invalide. Utilisez JJ/MM/AAAA")
    
    def clean_date_debarquement(self):
        date_str = self.cleaned_data.get('date_debarquement')
        if not date_str:
            return None
        
        # Essayer plusieurs formats
        from datetime import datetime
        formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except (ValueError, TypeError):
                continue
        
        raise forms.ValidationError("Format de date invalide. Utilisez JJ/MM/AAAA")


class IncidentNewForm(forms.ModelForm):
    """Formulaire pour signaler un incident"""
    
    class Meta:
        model = IncidentNew
        fields = [
            'datetime', 'type_incident', 'gravite',
            'description', 'actions_prises'
        ]
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'type_incident': forms.Select(attrs={'class': 'form-control'}),
            'gravite': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'actions_prises': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['datetime'].initial = timezone.now()


# Formsets pour gérer plusieurs entrées en une fois
LogEntryNewFormSet = inlineformset_factory(
    VoyageLogNew, LogEntryNew,
    form=LogEntryNewForm,
    extra=1,
    can_delete=True
)

CrewMemberNewFormSet = inlineformset_factory(
    VoyageLogNew, CrewMemberNew,
    form=CrewMemberNewForm,
    extra=1,
    can_delete=True
)

WeatherConditionNewFormSet = inlineformset_factory(
    VoyageLogNew, WeatherConditionNew,
    form=WeatherConditionNewForm,
    extra=1,
    can_delete=True
)