from django.urls import path
from .views import EntryListView, CreateEntryView, UpdateEntryView, DeleteEntryView, EntryDetailView

urlpatterns = [
    path("list/", EntryListView.as_view(), name="entry_list"),
    path('create/', CreateEntryView.as_view(), name = 'create_entry'),
    path('update/<int:pk>/', UpdateEntryView.as_view(), name='update_entry'),
    path('delete/<int:pk>/', DeleteEntryView.as_view(), name = 'delete_entry'),
    path('entry/<int:pk>/', EntryDetailView.as_view(), name='entry_detail'),
]
