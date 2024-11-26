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
from .forms import EntryForm
from django.db import models
import django.http

# Create your views here.
class EntryListView(LoginRequiredMixin, ListView):
    context_object_name = 'entry_list'
    template_name = 'entry_list.html'

    def get_queryset(self) -> QuerySet[Any]:
        return Entry.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['sum_of_values'] = context['entry_list'].aggregate(models.Sum('value'))['value__sum']
        return context

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