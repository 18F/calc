from django import forms

from ..models import SubmittedPriceList
from ..schedules import registry
from frontend.upload import UploadWidget
from frontend.date import SplitDateField


class Step1Form(forms.Form):
    # TODO: Consider making this a ModelForm that we just don't save; that
    # way, the fields are generated through introspecting the
    # SubmittedPriceList model and we keep things nice and DRY.

    schedule = forms.ChoiceField(
        choices=registry.get_choices
    )
    contract_number = forms.CharField(
        max_length=128,
        help_text='This should be the full contract number, e.g. GS-XXX-XXXX.'
    )
    vendor_name = forms.CharField(max_length=128)


class Step2Form(forms.ModelForm):
    is_small_business = forms.ChoiceField(
        label='Business size',
        choices=[
            (True, 'This is a small business.'),
            (False, 'This is not a small business.'),
        ],
        widget=forms.widgets.RadioSelect,
    )

    contract_start = SplitDateField(required=False)
    contract_end = SplitDateField(required=False)

    class Meta:
        model = SubmittedPriceList
        fields = [
            'is_small_business',
            'contractor_site',
            'contract_start',
            'contract_end',
            'contract_year',
        ]


class Step3Form(forms.Form):
    # TODO: We should figure out a way of getting rid of this field, since
    # we're not actually asking the user for it anymore.

    schedule = forms.ChoiceField(
        choices=registry.get_choices
    )

    file = forms.FileField(widget=UploadWidget())

    def clean(self):
        cleaned_data = super().clean()
        schedule = cleaned_data.get('schedule')
        file = cleaned_data.get('file')

        if schedule and file:
            gleaned_data = registry.smart_load_from_upload(schedule, file)

            if gleaned_data.is_empty():
                raise forms.ValidationError(
                    "The file you uploaded doesn't have any data we can "
                    "glean from it."
                )

            cleaned_data['gleaned_data'] = gleaned_data

        return cleaned_data


class Step4Form(forms.ModelForm):
    class Meta:
        model = SubmittedPriceList
        fields = [
            'contract_number',
            'vendor_name',
            'schedule',
            'is_small_business',
            'contractor_site',
            'contract_start',
            'contract_end',
            'contract_year',
        ]

        # TODO: It'd be nice if we could actually get rid of all these
        # hidden inputs, since all this data is already stored in our request
        # session.

        widgets = {
            'contract_number': forms.HiddenInput(),
            'vendor_name': forms.HiddenInput(),
            'schedule': forms.HiddenInput(),
            'is_small_business': forms.HiddenInput(),
            'contractor_site': forms.HiddenInput(),
            'contract_year': forms.HiddenInput(),
            'contract_start': forms.HiddenInput(),
            'contract_end': forms.HiddenInput()
        }