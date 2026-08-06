import uuid

from django import forms
from django.forms import BaseFormSet, formset_factory

from app.messages import VALIDATION_MESSAGES
from app.models import ApplicationMember


class RevisionForm(forms.Form):
    revision = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    next = forms.CharField(required=False, widget=forms.HiddenInput)


class BasicForm(RevisionForm):
    title = forms.CharField(label="申請名", max_length=200)
    purpose = forms.CharField(label="申請目的", widget=forms.Textarea, max_length=2000)


class AddressForm(RevisionForm):
    postal_code = forms.RegexField(
        label="郵便番号",
        regex=r"^\d{3}-?\d{4}$",
        max_length=8,
        error_messages={"invalid": VALIDATION_MESSAGES["postal_code_form_invalid"]},
    )
    prefecture = forms.CharField(label="都道府県", max_length=20)
    city = forms.CharField(label="市区町村", max_length=100)
    address_line = forms.CharField(label="番地・建物名", max_length=200)


class MemberForm(forms.Form):
    row_id = forms.UUIDField(widget=forms.HiddenInput)
    source_id = forms.UUIDField(required=False, widget=forms.HiddenInput)
    name = forms.CharField(label="氏名", max_length=100)
    email = forms.EmailField(label="メールアドレス")
    role = forms.ChoiceField(label="役割", choices=ApplicationMember.Role.choices)
    DELETE = forms.BooleanField(required=False, widget=forms.HiddenInput)


class BaseMemberFormSet(BaseFormSet):
    def clean(self) -> None:
        super().clean()
        if any(self.errors):
            return
        active = [form.cleaned_data for form in self.forms if not form.cleaned_data.get("DELETE")]
        if not active:
            raise forms.ValidationError(VALIDATION_MESSAGES["member_required"])
        emails = [item["email"].casefold() for item in active]
        if len(emails) != len(set(emails)):
            raise forms.ValidationError(VALIDATION_MESSAGES["email_duplicate"])
        row_ids = [item["row_id"] for item in active]
        if len(row_ids) != len(set(row_ids)):
            raise forms.ValidationError(VALIDATION_MESSAGES["row_id_duplicate_reload"])


MemberFormSet = formset_factory(MemberForm, formset=BaseMemberFormSet, extra=0)


class AttachmentForm(forms.Form):
    row_id = forms.UUIDField(widget=forms.HiddenInput)
    source_id = forms.UUIDField(required=False, widget=forms.HiddenInput)
    label = forms.CharField(label="表示名", max_length=100)
    file = forms.FileField(label="ファイル", required=False)
    existing_file_name = forms.CharField(required=False, widget=forms.HiddenInput)
    DELETE = forms.BooleanField(required=False, widget=forms.HiddenInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("DELETE"):
            return cleaned
        if not cleaned.get("file") and not cleaned.get("existing_file_name"):
            self.add_error("file", VALIDATION_MESSAGES["file_required"])
        return cleaned


class BaseAttachmentFormSet(BaseFormSet):
    def clean(self) -> None:
        super().clean()
        if any(self.errors):
            return
        row_ids = [
            form.cleaned_data["row_id"]
            for form in self.forms
            if not form.cleaned_data.get("DELETE")
        ]
        if len(row_ids) != len(set(row_ids)):
            raise forms.ValidationError(VALIDATION_MESSAGES["row_id_duplicate_reload"])


AttachmentFormSet = formset_factory(
    AttachmentForm,
    formset=BaseAttachmentFormSet,
    extra=0,
)


def new_row_id() -> str:
    return str(uuid.uuid4())
