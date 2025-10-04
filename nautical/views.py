
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView
from django.views import View
from .models import LogbookEntry, CrewMember, MaintenanceRecord, Checklist
from .forms import LogbookEntryForm, MediaAssetForm
from django.views.generic.edit import UpdateView, DeleteView  # ✅ AJOUT
from django.forms import inlineformset_factory
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse
from django.db.models import Q
from urllib.parse import urlencode
import csv
from io import BytesIO
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF


MaintenanceFormSet = inlineformset_factory(
    parent_model=LogbookEntry,
    model=MaintenanceRecord,
    fields=['date','equipment','description','cost_eur','engine_hours_at_time','next_due_date'],
    extra=1,
    can_delete=True
)

def home(request):
    return render(request, 'nautical/home.html', {
        'voyages_count': LogbookEntry.objects.count(),
        'crew_count': CrewMember.objects.count(),
        'maintenance_count': MaintenanceRecord.objects.count(),
    })

class LogbookListView(ListView):
    model = LogbookEntry
    template_name = 'nautical/voyage_list.html'
    paginate_by = 20

class LogbookDetailView(DetailView):
    model = LogbookEntry
    template_name = 'nautical/voyage_detail.html'

class LogbookCreateView(CreateView):
    model = LogbookEntry
    form_class = LogbookEntryForm
    success_url = reverse_lazy('voyage_list')
    template_name = 'nautical/voyage_form.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['maintenance_formset'] = MaintenanceFormSet(self.request.POST)
        else:
            data['maintenance_formset'] = MaintenanceFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['maintenance_formset']
        if formset.is_valid():
            response = super().form_valid(form)  # self.object est créé
            formset.instance = self.object
            formset.save()
            return response
        return self.form_invalid(form)

class MediaUploadView(View):
    def post(self, request, pk):
        voyage = get_object_or_404(LogbookEntry, pk=pk)
        form = MediaAssetForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.voyage = voyage
            asset.save()
        return redirect('voyage_detail', pk=pk)

class CrewListView(ListView):
    model = CrewMember
    template_name = 'nautical/crew_list.html'

class MaintenanceListView(ListView):
    model = MaintenanceRecord
    template_name = 'nautical/maintenance_list.html'

class ChecklistListView(ListView):
    model = Checklist
    template_name = 'nautical/checklist_list.html'


class ChecklistCreateView(CreateView):
    model = Checklist
    form_class = None
    template_name = 'nautical/checklist_form.html'
    success_url = reverse_lazy('checklist_list')

    def get_form_class(self):
        from .forms import ChecklistForm
        return ChecklistForm


class ChecklistUpdateView(UpdateView):
    model = Checklist
    template_name = 'nautical/checklist_form.html'

    def get_form_class(self):
        from .forms import ChecklistForm
        return ChecklistForm

    def get_success_url(self):
        return reverse('checklist_list')


class ChecklistDeleteView(DeleteView):
    model = Checklist
    template_name = 'nautical/checklist_confirm_delete.html'
    success_url = reverse_lazy('checklist_list')

class LogbookUpdateView(UpdateView):
    model = LogbookEntry
    form_class = LogbookEntryForm
    template_name = 'nautical/voyage_form.html'

    def get_success_url(self):
        return reverse('voyage_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['maintenance_formset'] = MaintenanceFormSet(self.request.POST, instance=self.object)
        else:
            data['maintenance_formset'] = MaintenanceFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['maintenance_formset']
        if formset.is_valid():
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()
            return response
        return self.form_invalid(form)

class LogbookDeleteView(DeleteView):
    model = LogbookEntry
    template_name = 'nautical/voyage_confirm_delete.html'
    success_url = reverse_lazy('voyage_list')

from .forms import ConsumableForm
from .models import Consumable

class ConsumableListView(ListView):
    model = Consumable
    template_name = "nautical/consumable_list.html"
    context_object_name = "consumables"
    paginate_by = 50  # ajuste si besoin

    def get_queryset(self):
        qs = Consumable.objects.all().order_by('name')
        q = (self.request.GET.get('q') or '').strip()
        origin = (self.request.GET.get('origin') or '').strip()

        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(reference__icontains=q) |
                Q(remark__icontains=q)
            )
        if origin:
            qs = qs.filter(origin=origin)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = (self.request.GET.get('q') or '').strip()
        origin = (self.request.GET.get('origin') or '').strip()
        ctx['q'] = q
        ctx['origin_selected'] = origin
        ctx['origin_choices'] = Consumable._meta.get_field('origin').choices

        params = {}
        if q: params['q'] = q
        if origin: params['origin'] = origin
        ctx['querystring'] = urlencode(params)
        return ctx

    def get(self, request, *args, **kwargs):
        # prépare le queryset filtré AVANT d’éventuellement exporter
        self.object_list = self.get_queryset()
        if request.GET.get('export') == 'csv':
            return self.export_csv(self.object_list)
        context = self.get_context_data()
        return self.render_to_response(context)

    def export_csv(self, qs):
        """
        Exporte TOUT le queryset filtré (pas la pagination) en CSV.
        Délimiteur ';' pour compat Excel FR. Ajoute un BOM UTF-8 pour les accents.
        """
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="consommables.csv"'
        # BOM pour Excel
        response.write('\ufeff')
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Nom', 'Origine', 'Origine (code)', 'Référence', 'Quantité', 'Prix (€)', 'Remarque', 'Fichier'])
        for c in qs:
            try:
                file_url = c.image.url if c.image else ''
            except Exception:
                file_url = ''
            writer.writerow([
                c.name,
                c.get_origin_display(),
                c.origin,
                c.reference or '',
                c.quantity,
                (f"{c.price_eur:.2f}" if c.price_eur is not None else ''),
                (c.remark or '').replace('\n', ' ').strip(),
                file_url,
            ])
        return response



class ConsumableCreateView(CreateView):
    model = Consumable
    form_class = ConsumableForm
    template_name = "nautical/consumable_form.html"
    success_url = reverse_lazy("consumable_list")

class ConsumableUpdateView(UpdateView):
    model = Consumable
    form_class = ConsumableForm
    template_name = "nautical/consumable_form.html"
    def get_success_url(self):
        return reverse("consumable_list")

class ConsumableDeleteView(DeleteView):
    model = Consumable
    template_name = "nautical/consumable_confirm_delete.html"
    success_url = reverse_lazy("consumable_list")

class ConsumablePdfView(View):
    def get(self, request, *args, **kwargs):
        # 1) Reprend le même filtrage que la liste
        qs = Consumable.objects.all().order_by('name')
        q = (request.GET.get('q') or '').strip()
        origin = (request.GET.get('origin') or '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(reference__icontains=q) | Q(remark__icontains=q))
        if origin:
            qs = qs.filter(origin=origin)

        # 2) Prépare le doc A4
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=15*mm, rightMargin=15*mm, topMargin=20*mm, bottomMargin=15*mm
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Small', fontSize=9, leading=11))

        story = []

        # 3) En-tête avec logo SVG (si présent)
        logo_path = (settings.BASE_DIR / "static" / "img" / "logo_bateau_manta.svg")
        if logo_path.exists():
            drawing = svg2rlg(str(logo_path))
            # cible ~42 mm de large
            target_w = 120  # points
            scale = target_w / float(drawing.width or 1)
            drawing.width *= scale
            drawing.height *= scale
            class DrawingFlowable(Spacer):
                def __init__(self, drawing):
                    super().__init__(1, drawing.height)
                    self.drawing = drawing
                def draw(self):
                    renderPDF.draw(self.drawing, self.canv, 0, 0)
            story.append(DrawingFlowable(drawing))
            story.append(Spacer(1, 6))

        from datetime import date
        story.append(Paragraph(f"<b>Inventaire des consommables</b> — {date.today().strftime('%d/%m/%Y')}", styles['Heading2']))
        story.append(Spacer(1, 8))

        # 4) Tableau
        data = [['Nom', 'Origine', 'Référence', 'Qté', 'Prix (€)', 'Remarque']]
        for c in qs:
            data.append([
                c.name,
                c.get_origin_display(),
                c.reference or '',
                str(c.quantity),
                (f"{c.price_eur:.2f}" if c.price_eur is not None else ''),
                (c.remark or '').replace('\n', ' '),
            ])

        table = Table(data, colWidths=[60*mm, 22*mm, 32*mm, 13*mm, 18*mm, 55*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f3f6')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0a2342')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('ALIGN', (3,1), (3,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.25, colors.HexColor('#cfd8e3')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(table)

        # 5) Pied de page avec pagination
        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []
            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                super().showPage()
            def save(self):
                total_pages = len(self._saved_page_states) or 1
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self._draw_page_number(total_pages)
                    super().showPage()
                super().save()
            def _draw_page_number(self, total):
                self.setFont("Helvetica", 9)
                w, h = A4
                self.drawRightString(w - 15*mm, 10*mm, f"Page {self._pageNumber}/{total}")

        doc.build(story, canvasmaker=NumberedCanvas)

        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=\"consommables.pdf\"'
        return response