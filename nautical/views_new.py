"""
Vues pour le nouveau système de livre de bord
Basées sur la structure du PDF Livre_de_Bord.pdf
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.cache import cache_page
from django.utils.http import http_date
from django.utils.decorators import method_decorator

# Import pour PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from io import BytesIO

from .models_new import VoyageLogNew, LogEntryNew, WeatherConditionNew, CrewMemberNew, IncidentNew, VoyagePhoto
from .forms_new import (
    VoyageLogForm, LogEntryNewForm, QuickLogEntryNewForm, 
    WeatherConditionNewForm, CrewMemberNewForm, IncidentNewForm,
    LogEntryNewFormSet, CrewMemberNewFormSet, WeatherConditionNewFormSet,
    VoyagePhotoForm, HeaderPhotoForm, GalleryPhotoForm
)


@method_decorator(cache_page(30), name='dispatch')
class VoyageLogListView(ListView):
    """Liste de tous les livres de bord"""
    model = VoyageLogNew
    template_name = 'nautical/voyage_log_list.html'
    context_object_name = 'voyages'
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                total_entries=Count('entries'),
                crew_count=Count('equipage'),
                weather_count=Count('conditions_meteo'),
                incidents_count=Count('incidents'),
            )
        )
        # Filtrage optionnel par statut
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        return queryset


class VoyageLogDetailView(DetailView):
    """Affichage détaillé d'un livre de bord avec timeline"""
    model = VoyageLogNew
    template_name = 'nautical/voyage_log_detail.html'
    context_object_name = 'voyage'

    def get(self, request, *args, **kwargs):
        # Intercepter les objets manquants et rediriger proprement vers la liste
        try:
            self.object = self.get_object()
        except Http404:
            messages.info(request, "Ce livre de bord n'existe pas ou a été supprimé.")
            return redirect('voyage_log_list')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Optimiser les accès liés
        voyage = (
            VoyageLogNew.objects
            .prefetch_related(
                'entries',
                'conditions_meteo',
                'equipage',
                'incidents'
            )
            .get(pk=self.object.pk)
        )
        
        # Récupérer les entrées de log triées par date/heure (limiter par défaut)
        all_entries_qs = voyage.entries.all().order_by('date', 'heure')
        show_all = self.request.GET.get('all') == '1'
        max_entries = 50
        context['entries'] = list(all_entries_qs if show_all else all_entries_qs[:max_entries])
        context['entries_total_count'] = all_entries_qs.count()
        context['entries_shown_count'] = len(context['entries'])
        context['entries_truncated'] = (not show_all) and (context['entries_total_count'] > max_entries)
        context['show_all'] = show_all
        # Pré-calcul utile pour le template (évite add:-x)
        try:
            context['entries_remaining'] = max(0, context['entries_total_count'] - context['entries_shown_count'])
        except Exception:
            context['entries_remaining'] = 0
        
        # Conditions météo
        context['weather_conditions'] = voyage.conditions_meteo.all().order_by('datetime')
        
        # Équipage
        context['crew_members'] = voyage.equipage.all()
        
        # Incidents
        context['incidents'] = voyage.incidents.all().order_by('datetime')
        
        # Statistiques du voyage (utilise les données préfetchées)
        entries = list(context['entries'])
        if entries:
            context['total_entries'] = len(entries)
            first_entry = entries[0]
            last_entry = entries[-1]
            context['first_entry'] = first_entry
            context['last_entry'] = last_entry
            
            # Calculer la durée du voyage basée sur les dates de début/fin du voyage
            if voyage.date_fin and voyage.date_debut:
                # Utiliser les dates de voyage, pas les entrées de log
                duration = voyage.date_fin - voyage.date_debut
                context['voyage_duration'] = duration
            elif first_entry and last_entry:
                # Fallback: si pas de date de fin, utiliser les entrées
                from django.utils.timezone import make_aware, get_current_timezone
                tz = get_current_timezone()
                start_naive = timezone.datetime.combine(first_entry.date, first_entry.heure)
                end_naive = timezone.datetime.combine(last_entry.date, last_entry.heure)
                try:
                    start_dt = make_aware(start_naive, timezone=tz)
                    end_dt = make_aware(end_naive, timezone=tz)
                except Exception:
                    start_dt, end_dt = start_naive, end_naive
                context['voyage_duration'] = end_dt - start_dt
        
        return context


class VoyageLogCreateView(CreateView):
    """Créer un nouveau livre de bord"""
    model = VoyageLogNew
    form_class = VoyageLogForm
    template_name = 'nautical/voyage_log_form.html'
    success_url = reverse_lazy('voyage_log_list')

    def form_valid(self, form):
        messages.success(self.request, f"Livre de bord créé pour {form.instance.bateau}")
        return super().form_valid(form)


class VoyageLogUpdateView(UpdateView):
    """Modifier un livre de bord existant"""
    model = VoyageLogNew
    form_class = VoyageLogForm
    template_name = 'nautical/voyage_log_form.html'

    def get_success_url(self):
        return reverse('voyage_log_detail', kwargs={'pk': self.object.pk})


def voyage_log_delete_view(request, pk):
    """
    Supprimer un livre de bord (seulement si statut = 'preparation').
    Si le voyage n'existe plus, on redirige proprement vers la liste.
    """
    voyage = VoyageLogNew.objects.filter(pk=pk).first()
    if voyage is None:
        messages.info(request, "Ce livre de bord n'existe pas ou a déjà été supprimé.")
        return redirect('voyage_log_list')
    
    # Vérifier que le voyage peut être supprimé
    if voyage.statut not in ['preparation']:
        messages.error(request, "Impossible de supprimer un voyage qui est en cours ou terminé.")
        return redirect('voyage_log_detail', pk=pk)
    
    if request.method == 'POST':
        titre_voyage = voyage.sujet_voyage if voyage.sujet_voyage else voyage.bateau
        voyage.delete()
        messages.success(request, f"Le livre de bord '{titre_voyage}' a été supprimé.")
        return redirect('voyage_log_list')
    
    context = {
        'voyage': voyage,
        'title': 'Supprimer le livre de bord'
    }
    return render(request, 'nautical/voyage_log_confirm_delete.html', context)


def voyage_log_live_view(request, pk):
    """
    Vue 'live' du livre de bord - pour saisir des événements en temps réel
    """
    voyage = get_object_or_404(VoyageLogNew, pk=pk)
    
    # Récupérer les dernières entrées (10 plus récentes)
    recent_entries = voyage.entries.all().order_by('-date', '-heure')[:10]
    
    # Formulaire de saisie rapide
    if request.method == 'POST':
        form = QuickLogEntryNewForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.voyage = voyage
            entry.date = timezone.now().date()  # Date automatique
            entry.save()
            
            messages.success(request, "Entrée ajoutée au livre de bord")
            return redirect('voyage_log_live', pk=pk)
    else:
        form = QuickLogEntryNewForm()
    
    # Utiliser l'heure locale pour l'affichage (GMT-10)
    from django.utils import timezone as django_timezone
    import datetime
    
    # Obtenir l'heure UTC et la convertir en heure locale (GMT-10)
    utc_now = timezone.now()
    # GMT-10, donc on soustrait 10 heures
    local_time = utc_now - datetime.timedelta(hours=10)
    
    context = {
        'voyage': voyage,
        'form': form,
        'recent_entries': recent_entries,
        'current_time': local_time.strftime('%H:%M'),
        'entries_count': voyage.entries.count(),
        'crew_count': voyage.equipage.count(),
        'weather_count': voyage.conditions_meteo.count(),
    }
    
    return render(request, 'nautical/voyage_log_live.html', context)


def add_log_entry(request, voyage_pk):
    """Ajouter une entrée complète de log"""
    voyage = get_object_or_404(VoyageLogNew, pk=voyage_pk)
    
    if request.method == 'POST':
        form = LogEntryNewForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.voyage = voyage
            entry.save()
            
            messages.success(request, "Entrée de log ajoutée")
            return redirect('voyage_log_detail', pk=voyage_pk)
    else:
        form = LogEntryNewForm()
    
    context = {
        'voyage': voyage,
        'form': form,
        'title': 'Ajouter une entrée de log'
    }
    
    return render(request, 'nautical/log_entry_form.html', context)


def edit_log_entry(request, voyage_pk, entry_pk):
    """Modifier une entrée de log"""
    voyage = get_object_or_404(VoyageLogNew, pk=voyage_pk)
    entry = get_object_or_404(LogEntryNew, pk=entry_pk, voyage=voyage)
    
    if request.method == 'POST':
        form = LogEntryNewForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Entrée de log modifiée")
            return redirect('voyage_log_detail', pk=voyage_pk)
    else:
        form = LogEntryNewForm(instance=entry)
    
    context = {
        'voyage': voyage,
        'form': form,
        'entry': entry,
        'title': 'Modifier l\'entrée de log'
    }
    
    return render(request, 'nautical/log_entry_form.html', context)


def add_weather_condition(request, voyage_pk):
    """Ajouter des conditions météorologiques"""
    voyage = get_object_or_404(VoyageLogNew, pk=voyage_pk)
    
    if request.method == 'POST':
        form = WeatherConditionNewForm(request.POST)
        if form.is_valid():
            weather = form.save(commit=False)
            weather.voyage = voyage
            weather.save()
            
            messages.success(request, "Conditions météo ajoutées")
            return redirect('voyage_log_detail', pk=voyage_pk)
    else:
        form = WeatherConditionNewForm()
    
    context = {
        'voyage': voyage,
        'form': form,
        'title': 'Ajouter des conditions météo'
    }
    
    return render(request, 'nautical/weather_form.html', context)


def add_crew_member(request, voyage_pk):
    """Ajouter un membre d'équipage"""
    voyage = get_object_or_404(VoyageLogNew, pk=voyage_pk)
    
    if request.method == 'POST':
        form = CrewMemberNewForm(request.POST)
        if form.is_valid():
            # Vérifier si on utilise un membre existant ou un nouveau
            existing_member = form.cleaned_data.get('existing_member')
            
            if existing_member:
                # Utiliser un membre existant
                crew = form.save(commit=False)
                crew.voyage = voyage
                # Les champs nom/prenom sont déjà remplis par le clean() du formulaire
                # Mais on peut aussi récupérer d'autres infos
                if not crew.role or crew.role == 'equipier':  # Si pas de rôle spécifique ou rôle par défaut
                    crew.role = existing_member.role
                if not crew.contact_telephone:
                    crew.contact_telephone = existing_member.contact
                crew.save()
                
                messages.success(request, f"{existing_member.full_name} ajouté à l'équipage du voyage")
            else:
                # Nouveau membre
                crew = form.save(commit=False)
                crew.voyage = voyage
                crew.save()
                
                # Ajouter aussi à la liste générale des membres d'équipage
                from .models import CrewMember
                full_name = f"{crew.prenom} {crew.nom}".strip()
                
                # Vérifier si cette personne existe déjà dans la liste générale
                general_crew, created = CrewMember.objects.get_or_create(
                    full_name=full_name,
                    defaults={
                        'role': crew.role,
                        'contact': crew.contact_telephone or '',
                        'notes': f"Ajouté depuis le voyage {voyage.sujet_voyage or voyage.bateau}"
                    }
                )
                
                if created:
                    messages.success(request, f"{crew.prenom} {crew.nom} ajouté à l'équipage et à la liste générale")
                else:
                    messages.success(request, f"{crew.prenom} {crew.nom} ajouté à l'équipage")
            
            return redirect('voyage_log_detail', pk=voyage_pk)
    else:
        form = CrewMemberNewForm()
    
    context = {
        'voyage': voyage,
        'form': form,
        'title': 'Ajouter un membre d\'équipage'
    }
    
    return render(request, 'nautical/crew_form.html', context)


def add_incident(request, voyage_pk):
    """Signaler un incident"""
    voyage = get_object_or_404(VoyageLogNew, pk=voyage_pk)
    
    if request.method == 'POST':
        form = IncidentNewForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.voyage = voyage
            incident.save()
            
            messages.warning(request, f"Incident {incident.get_gravite_display().lower()} signalé")
            return redirect('voyage_log_detail', pk=voyage_pk)
    else:
        form = IncidentNewForm()
    
    context = {
        'voyage': voyage,
        'form': form,
        'title': 'Signaler un incident'
    }
    
    return render(request, 'nautical/incident_form.html', context)


def voyage_log_api_entries(request, pk):
    """API pour récupérer les entrées de log en JSON (pour rafraîchissement live)"""
    voyage = get_object_or_404(VoyageLogNew, pk=pk)
    
    # Récupérer les entrées depuis une certaine date/heure si spécifiée
    since = request.GET.get('since')
    entries = voyage.entries.all().order_by('-date', '-heure')
    
    if since:
        try:
            since_datetime = timezone.datetime.fromisoformat(since)
            entries = entries.filter(
                Q(date__gt=since_datetime.date()) |
                (Q(date=since_datetime.date()) & Q(heure__gt=since_datetime.time()))
            )
        except ValueError:
            pass
    
    # Limiter à 20 entrées max
    entries = entries[:20]
    
    data = []
    for entry in entries:
        data.append({
            'id': entry.id,
            'date': entry.date.strftime('%d/%m/%Y'),
            'heure': entry.heure.strftime('%H:%M'),
            'evenements': entry.evenements,
            'position': entry.position,
            'vent_force': entry.vent_force,
            'vent_direction': entry.vent_direction,
            'allure': entry.allure,
        })
    
    return JsonResponse({'entries': data})


def voyage_dashboard(request):
    """Tableau de bord des voyages"""
    # Voyages en cours
    voyages_en_cours = VoyageLogNew.objects.filter(statut='en_cours')
    
    # Voyages récents
    voyages_recents = VoyageLogNew.objects.all().order_by('-created_at')[:5]
    
    # Statistiques
    total_voyages = VoyageLogNew.objects.count()
    total_entries = LogEntryNew.objects.count()
    
    context = {
        'voyages_en_cours': voyages_en_cours,
        'voyages_recents': voyages_recents,
        'total_voyages': total_voyages,
        'total_entries': total_entries,
    }
    
    return render(request, 'nautical/voyage_dashboard.html', context)


@cache_page(120)
def export_voyage_pdf(request, pk):
    """Export d'un voyage complet en PDF sur une seule page"""
    voyage = get_object_or_404(
        VoyageLogNew.objects.prefetch_related(
            'entries', 'conditions_meteo', 'equipage', 'incidents'
        ),
        pk=pk
    )
    
    # Créer le buffer pour le PDF
    buffer = BytesIO()
    
    # Créer le document PDF en format A4
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=10*mm,
        leftMargin=10*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=6,
        textColor=colors.darkblue,
        alignment=1  # Centre
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=10,
        spaceAfter=3,
        textColor=colors.black,
        alignment=0
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=1
    )
    
    # Contenu du PDF
    story = []
    
    # Titre principal
    story.append(Paragraph(f"📚 LIVRE DE BORD - {voyage.bateau}", title_style))
    story.append(Spacer(1, 3*mm))
    
    # Informations du voyage
    voyage_info = [
        ['Sujet du voyage:', voyage.sujet_voyage or 'Non spécifié'],
        ['Dates:', f"{voyage.date_debut.strftime('%d/%m/%Y')} → {voyage.date_fin.strftime('%d/%m/%Y') if voyage.date_fin else 'En cours'}"],
        ['Trajet:', f"{voyage.port_depart} → {voyage.port_arrivee or 'En cours'}"],
        ['Statut:', voyage.get_statut_display()],
    ]
    
    voyage_table = Table(voyage_info, colWidths=[40*mm, 80*mm])
    voyage_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    story.append(voyage_table)
    story.append(Spacer(1, 3*mm))
    
    # Équipage
    story.append(Paragraph("👥 ÉQUIPAGE", subtitle_style))
    crew_data = [['Nom', 'Rôle', 'Embarquement', 'Débarquement']]
    for member in voyage.equipage.all():
        crew_data.append([
            f"{member.nom} {member.prenom}",
            member.get_role_display(),
            member.date_embarquement.strftime('%d/%m') if member.date_embarquement else '-',
            member.date_debarquement.strftime('%d/%m') if member.date_debarquement else 'À bord'
        ])
    
    if len(crew_data) > 1:
        crew_table = Table(crew_data, colWidths=[40*mm, 30*mm, 25*mm, 25*mm])
        crew_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ]))
        story.append(crew_table)
    else:
        story.append(Paragraph("Aucun membre d'équipage enregistré", normal_style))
    story.append(Spacer(1, 3*mm))
    
    # Entrées de log (résumé compact)
    story.append(Paragraph("📋 ENTRÉES DE LOG", subtitle_style))
    log_data = [['Date', 'Heure', 'Position', 'Log', 'Cap', 'Observations']]
    entries_qs = voyage.entries.all().order_by('date', 'heure')
    max_log_rows = 28
    total_logs = entries_qs.count()
    # Gestion des notes détaillées pour événements longs
    footnotes = []
    footnote_index = 1
    for entry in entries_qs[:max_log_rows]:
        observations = []
        truncated_ev = False
        # Événements prioritaires dans la colonne Observations
        if entry.evenements:
            ev_full = (entry.evenements or '').strip().replace('\n', ' ')
            ev_display = ev_full
            if len(ev_full) > 90:
                ev_display = ev_full[:87] + '...'
                truncated_ev = True
            # Ajouter marque de note si tronqué
            if truncated_ev:
                observations.append(f"{ev_display} [{footnote_index}]")
                # Ajouter la note détaillée avec ancrage date/heure
                footnotes.append(f"[{footnote_index}] {entry.date.strftime('%d/%m')} {entry.heure.strftime('%H:%M')} — {ev_full}")
                footnote_index += 1
            else:
                observations.append(ev_display)
        if entry.allure:
            observations.append(f"Allure: {entry.allure}")
        if entry.voilure:
            observations.append(f"Voilure: {entry.voilure}")
        # Ajouts compacts basés sur les champs existants
        if entry.vent_force or entry.vent_direction:
            vent_txt = f"{(entry.vent_force or '').strip()} {(entry.vent_direction or '').strip()}".strip()
            if vent_txt:
                observations.append(f"Vent: {vent_txt}")
        if entry.etat_mer:
            observations.append(f"Mer: {entry.etat_mer}")
        if entry.visibilite:
            observations.append(f"Visi: {entry.visibilite}")
        if entry.barometre:
            observations.append(f"Pression: {entry.barometre} hPa")

        # Afficher plus de détails si pas de note (jusqu'à 3 éléments)
        obs_limit = 2 if truncated_ev else 3
        log_data.append([
            entry.date.strftime('%d/%m'),
            entry.heure.strftime('%H:%M'),
            entry.position[:30] + '...' if entry.position and len(entry.position) > 30 else (entry.position or '-'),
            f"{entry.log_nautique:.1f}" if entry.log_nautique else '-',
            f"{entry.cap_compas}°" if entry.cap_compas else '-',
            ' | '.join(observations[:obs_limit])  # Jusqu'à 3 sans note, 2 si note
        ])
    
    if len(log_data) > 1:
        log_table = Table(log_data, colWidths=[18*mm, 18*mm, 50*mm, 15*mm, 15*mm, 60*mm])
        log_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ]))
        story.append(log_table)
        if total_logs > (len(log_data) - 1):
            extra_logs = total_logs - (len(log_data) - 1)
            story.append(Paragraph(f"… (+{extra_logs} entrées supplémentaires)", ParagraphStyle('Note', parent=styles['Normal'], fontSize=7, textColor=colors.grey)))
        # Ajouter section notes si nécessaire (limiter pour rester sur 1 page)
        if footnotes:
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph("Notes détaillées", ParagraphStyle('FootTitle', parent=styles['Normal'], fontSize=7, textColor=colors.black)))
            max_notes = 5
            for note in footnotes[:max_notes]:
                story.append(Paragraph(note, ParagraphStyle('Note', parent=styles['Normal'], fontSize=6, textColor=colors.grey)))
            if len(footnotes) > max_notes:
                story.append(Paragraph(f"… (+{len(footnotes) - max_notes} notes supplémentaires)", ParagraphStyle('Note', parent=styles['Normal'], fontSize=6, textColor=colors.grey)))
    else:
        story.append(Paragraph("Aucune entrée de log enregistrée", normal_style))
    story.append(Spacer(1, 3*mm))
    
    # Résumé météo (situation générale si disponible)
    try:
        first_summary = next((w.situation_generale for w in voyage.conditions_meteo.all() if w.situation_generale), None)
        if first_summary:
            story.append(Paragraph("🛈 Résumé météo", subtitle_style))
            story.append(Paragraph(first_summary, normal_style))
            story.append(Spacer(1, 2*mm))
    except Exception:
        pass

    # Conditions météorologiques
    story.append(Paragraph("🌤️ CONDITIONS MÉTÉO", subtitle_style))
    weather_data = [['Date/Heure', 'Bulletin', 'Vent (jour)', 'Mer (jour)', 'Visibilité (jour)']]
    wc_qs = voyage.conditions_meteo.all().order_by('datetime')
    max_wc_rows = 8
    total_wc = wc_qs.count()
    for weather in wc_qs[:max_wc_rows]:
        weather_data.append([
            weather.datetime.strftime('%d/%m %H:%M'),
            weather.type_bulletin or '-',
            weather.prev_jour_vent or '-',
            weather.prev_jour_mer or '-',
            weather.prev_jour_visibilite or '-',
        ])
    
    if len(weather_data) > 1:
        weather_table = Table(weather_data, colWidths=[35*mm, 35*mm, 30*mm, 30*mm, 30*mm])
        weather_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
        ]))
        story.append(weather_table)
        if total_wc > (len(weather_data) - 1):
            extra_wc = total_wc - (len(weather_data) - 1)
            story.append(Paragraph(f"… (+{extra_wc} bulletins supplémentaires)", ParagraphStyle('Note', parent=styles['Normal'], fontSize=7, textColor=colors.grey)))
    else:
        story.append(Paragraph("Aucune condition météo enregistrée", normal_style))
    story.append(Spacer(1, 3*mm))
    
    # Incidents (si existants)
    incidents = voyage.incidents.all()
    if incidents:
        story.append(Paragraph("⚠️ INCIDENTS", subtitle_style))
        for incident in incidents:
            incident_text = f"<b>{incident.datetime.strftime('%d/%m %H:%M')}</b> - {incident.get_gravite_display()}: {incident.description[:100]}"
            story.append(Paragraph(incident_text, normal_style))
    
    # Pied de page
    story.append(Spacer(1, 5*mm))
    footer_text = f"Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')} - Livre de bord électronique"
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=6, alignment=1, textColor=colors.grey)))
    
    # Construire le PDF
    doc.build(story)
    
    # Retourner la réponse PDF
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Livre_de_bord_{voyage.bateau}_{voyage.date_debut.strftime("%Y%m%d")}.pdf"'
    # Caching headers
    try:
        ts = int(voyage.updated_at.timestamp())
        response['ETag'] = f'W/"voyage-{voyage.pk}-{ts}"'
        response['Last-Modified'] = http_date(ts)
        response['Cache-Control'] = 'max-age=120, private'
    except Exception:
        pass
    
    return response


# =============================================================================
# VUES POUR GESTION DES PHOTOS
# =============================================================================

class VoyagePhotoUploadView(CreateView):
    """Vue pour ajouter une photo à un voyage"""
    model = VoyagePhoto
    template_name = 'nautical/voyage_photo_form.html'
    
    def get_form_class(self):
        photo_type = self.request.GET.get('type', 'gallery')
        if photo_type == 'header':
            from .forms_new import HeaderPhotoForm
            return HeaderPhotoForm
        else:
            from .forms_new import GalleryPhotoForm
            return GalleryPhotoForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.voyage = get_object_or_404(VoyageLogNew, pk=self.kwargs['voyage_pk'])
        context['voyage'] = self.voyage
        context['photo_type'] = self.request.GET.get('type', 'gallery')
        return context
    
    def form_valid(self, form):
        self.voyage = get_object_or_404(VoyageLogNew, pk=self.kwargs['voyage_pk'])
        form.instance.voyage = self.voyage
        
        # Si c'est une photo d'en-tête et qu'il y en a déjà une, la remplacer
        if form.instance.type_photo == 'header':
            existing_header = self.voyage.photos.filter(type_photo='header').first()
            if existing_header:
                existing_header.delete()
        
        photo_type_msg = "d'en-tête" if form.instance.type_photo == 'header' else 'de galerie'
        messages.success(self.request, 
            f"📸 Photo {photo_type_msg} ajoutée avec succès !")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('voyage_log_detail', kwargs={'pk': self.kwargs['voyage_pk']})


class VoyagePhotoUpdateView(UpdateView):
    """Vue pour modifier une photo de voyage"""
    model = VoyagePhoto
    form_class = VoyagePhotoForm
    template_name = 'nautical/voyage_photo_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['voyage'] = self.object.voyage
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['voyage'] = self.object.voyage
        context['photo_type'] = self.object.type_photo
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "📸 Photo modifiée avec succès !")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('voyage_log_detail', kwargs={'pk': self.object.voyage.pk})


class VoyagePhotoDeleteView(DeleteView):
    """Vue pour supprimer une photo de voyage"""
    model = VoyagePhoto
    template_name = 'nautical/voyage_photo_confirm_delete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['voyage'] = self.object.voyage
        return context
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        voyage = self.object.voyage
        
        # Supprimer le fichier image du système de fichiers
        try:
            if self.object.image:
                self.object.image.delete(save=False)
        except Exception:
            pass  # Ignorer les erreurs de suppression de fichier
        
        messages.success(request, "🗑️ Photo supprimée avec succès !")
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('voyage_log_detail', kwargs={'pk': self.object.voyage.pk})


def set_header_photo(request, voyage_pk, photo_pk):
    """Vue pour définir une photo comme photo d'en-tête"""
    voyage = get_object_or_404(VoyageLogNew, pk=voyage_pk)
    photo = get_object_or_404(VoyagePhoto, pk=photo_pk, voyage=voyage)
    
    # Supprimer l'ancienne photo d'en-tête s'il y en a une
    old_header = voyage.photos.filter(type_photo='header').first()
    if old_header and old_header != photo:
        old_header.type_photo = 'gallery'
        old_header.save()
    
    # Définir cette photo comme en-tête
    photo.type_photo = 'header'
    photo.ordre = 0
    photo.save()
    
    messages.success(request, f"📸 '{photo.titre or 'Photo'}' définie comme photo d'en-tête !")
    return redirect('voyage_log_detail', pk=voyage_pk)


def voyage_gallery_view(request, pk):
    """Vue pour afficher la galerie complète d'un voyage"""
    voyage = get_object_or_404(VoyageLogNew, pk=pk)
    
    context = {
        'voyage': voyage,
        'gallery_photos': voyage.gallery_photos,
        'header_photo': voyage.header_photo,
    }
    
    return render(request, 'nautical/voyage_gallery.html', context)