from .models import Entry
from django import forms

class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ['title', 'description', 'value']

        def form_valid(self, form: forms.BaseModelForm):
            form.instance.user = self.request.user
            return super(EntryForm, self).form_valid(form)

