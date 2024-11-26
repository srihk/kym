from typing import Any
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from .models import Entry
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView
from .forms import EntryForm, AnalyticsFilterForm
from django.db import models
import django.http
import plotly.express as px
import calendar
from django.utils import timezone
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from datetime import datetime
import datetime
from django.utils import timezone
class EntryListView(LoginRequiredMixin, ListView):
    context_object_name = 'entry_list'
    template_name = 'entry_list.html'

    def get_queryset(self) -> QuerySet[Any]:
        return Entry.objects.filter(user=self.request.user)
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['sum_of_values'] = context['entry_list'].aggregate(models.Sum('value'))['value__sum']
        date = timezone.now()
        prevdate = timezone.now() - datetime.timedelta(days=30)
        context['monthly_total'] = context['entry_list'].filter(createdAt__startswith=str(date.year)+"-"+str(date.month)).aggregate(models.Sum('value'))['value__sum']
        prevmonth_total = context['entry_list'].filter(createdAt__startswith=str(prevdate.year)+"-"+str(prevdate.month)).aggregate(models.Sum('value'))['value__sum']
        if prevmonth_total:
            context['monthly_change'] = (context['monthly_total'] / prevmonth_total) * 100
        else:
            context['monthly_change'] = '-'
        
        context['average_value'] = int(context['entry_list'].aggregate(models.Avg('value'))['value__avg'])
        context['total_entries'] = len(context['entry_list'])

        context['largest_value'] = context['entry_list'].aggregate(models.Max('value'))['value__max']
        context['largest_entry_date'] = context['entry_list'].order_by('-value')[0].createdAt

        return context

class HomeView(LoginRequiredMixin, ListView):
    template_name = 'home.html'
    context_object_name = 'recent_entries'
    model = Entry

    def get_queryset(self) -> QuerySet[Any]:
        return Entry.objects.filter(user=self.request.user).order_by('createdAt')[:5]

class AnalyticsView(LoginRequiredMixin, FormView):
    template_name='analytics.html'
    form_class=AnalyticsFilterForm
    success_url=reverse_lazy('analytics')

    def get_queryset(self) -> QuerySet[Any]:
        return Entry.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        # Handle export requests
        export_type = request.GET.get('export')
        if export_type == 'csv':
            return self.export_csv()
        elif export_type == 'pdf':
            return self.export_pdf()
        return super().get(request, *args, **kwargs)

    def export_csv(self):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="spending_analytics_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Title', 'Description', 'Value'])
        
        entries = self.get_queryset().order_by('createdAt')
        for entry in entries:
            writer.writerow([
                entry.createdAt.strftime("%Y-%m-%d"),
                entry.title,
                entry.description,
                entry.value
            ])
        
        return response

    def export_pdf(self):
        # Create the HttpResponse object with PDF headers
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="spending_analytics_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        # Create the PDF object using ReportLab
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content to the PDF
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, 750, "Spending Analytics Report")
        
        p.setFont("Helvetica", 12)
        p.drawString(50, 720, f"Generated on: {timezone.now().strftime('%Y-%m-%d')}")
        
        # Add table headers
        y_position = 680
        headers = ['Date', 'Title', 'Value']
        x_positions = [50, 150, 450]
        
        p.setFont("Helvetica-Bold", 10)
        for header, x in zip(headers, x_positions):
            p.drawString(x, y_position, header)
        
        # Add entries
        p.setFont("Helvetica", 10)
        entries = self.get_queryset().order_by('createdAt')
        
        for entry in entries:
            y_position -= 20
            if y_position < 50:  # Start new page if near bottom
                p.showPage()
                y_position = 750
                p.setFont("Helvetica", 10)
            
            p.drawString(50, y_position, entry.createdAt.strftime("%Y-%m-%d"))
            p.drawString(150, y_position, str(entry.title)[:30])
            p.drawString(450, y_position, f"INR {entry.value:.2f}")
        
        # Add summary
        total = entries.aggregate(total=models.Sum('value'))['total'] or 0
        p.setFont("Helvetica-Bold", 10)
        p.drawString(350, y_position - 30, f"Total Spending: INR {total:.2f}")
        
        p.showPage()
        p.save()
        
        # Get the value of the BytesIO buffer and return the response
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response

    def form_valid(self, form: Any) -> HttpResponse:
        context = self.get_context_data()
        date = form.cleaned_data['month']
        
        filtered_objs = self.get_queryset().filter(createdAt__startswith=str(date.year)+"-"+str(date.month))
        if filtered_objs.exists():
            day_sum = filtered_objs.values('createdAt__day').annotate(total=models.Sum('value'))
            
            total_month = []
            for day in range(1, calendar.monthrange(date.year, date.month)[1]+1):
                total_month.append({'day': day, "total": 0})
            for obj in day_sum:
                total_month[obj['createdAt__day']-1]['total'] = obj['total']
            fig = px.bar(total_month, x='day', y='total', title='Expenses')
            fig.update_layout(barmode='group', xaxis={'type':'category'})
            context['fig'] = fig.to_html(full_html=False)
            curdate = timezone.now()
            print(str(curdate.year)+"-"+str(curdate.month)+"-"+str(curdate.day))
            context['daily_avg'] = self.get_queryset().filter(createdAt__startswith=str(curdate.year)+"-"+str(curdate.month)+"-"+str(curdate.day)).aggregate(models.Avg('value'))['value__avg']
            activedate = self.get_queryset().filter(createdAt__startswith=str(curdate.year)+"-"+str(curdate.month)).order_by('-value')[0].createdAt
            print(activedate)
            context['most_active_day'] = str(activedate.year) + '-' + str(activedate.month) + '-' + str(activedate.day)
        else:
            context['no_data'] = True
        return render(self.request, self.template_name, context)

class CreateEntryView(LoginRequiredMixin, CreateView):
    model = Entry
    fields = ['title', 'description', 'value']
    success_url = reverse_lazy('entry_list')
    template_name = 'create_entry.html'

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.user = self.request.user
        return super().form_valid(form)

class UpdateEntryView(LoginRequiredMixin, UpdateView):
    fields = ['title', 'description', 'value']
    success_url = reverse_lazy('entry_list')
    template_name = 'update_entry.html'

    def get_queryset(self) -> QuerySet[Any]:
        return Entry.objects.filter(user=self.request.user)

class DeleteEntryView(LoginRequiredMixin, DeleteView):
    fields = ['title', 'description', 'value']
    success_url = reverse_lazy('entry_list')
    template_name = 'confirm_delete_entry.html'
    context_object_name = 'entry'

    def get_queryset(self) -> QuerySet[Any]:
        return Entry.objects.filter(user=self.request.user)

class EntryDetailView(LoginRequiredMixin, DetailView):
    context_object_name = 'entry'
    template_name = 'entry_detail.html'
    
    def get_queryset(self) -> QuerySet[Any]:
        return Entry.objects.filter(user=self.request.user)