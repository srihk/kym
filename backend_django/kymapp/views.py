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
import datetime

# Create your views here.
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

    def form_valid(self, form: Any) -> HttpResponse:
        context = self.get_context_data()
        date = form.cleaned_data['month']
        
        filtered_objs = self.get_queryset().filter(createdAt__startswith=str(date.year)+"-"+str(date.month))
        print("month:", date)
        for obj in Entry.objects.all():
            print(obj.createdAt)
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
            print(day_sum)
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
