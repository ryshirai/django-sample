from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from app.errors import DomainError, ValidationError
from app.forms import AddressForm, AttachmentFormSet, BasicForm, MemberFormSet, RevisionForm
from app.messages import SUCCESS_MESSAGES, message_for_error
from app.presentation import attachment_initial, draft_page_context, member_initial
from app.selectors import get_draft_for_edit
from app.services import (
    submit_draft,
    update_address,
    update_attachments,
    update_basic,
    update_members,
)

NEXT_ROUTES = {
    "basic": "app:draft-basic",
    "address": "app:draft-address",
    "members": "app:draft-members",
    "attachments": "app:draft-attachments",
    "confirm": "app:draft-confirm",
}


def _redirect_step(*, draft_id, requested: str, fallback: str):
    route = NEXT_ROUTES.get(requested, NEXT_ROUTES[fallback])
    return redirect(route, draft_id=draft_id)


@login_required
@require_http_methods(["GET", "POST"])
def basic_edit(request: HttpRequest, draft_id) -> HttpResponse:
    draft = get_draft_for_edit(draft_id=draft_id, user=request.user)
    initial = {**draft.data["basic"], "revision": draft.revision}
    form = BasicForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            update_basic(
                draft_id=draft.id,
                owner=request.user,
                expected_revision=form.cleaned_data["revision"],
                title=form.cleaned_data["title"],
                purpose=form.cleaned_data["purpose"],
            )
        except DomainError as error:
            messages.error(request, message_for_error(error))
            return redirect("app:draft-basic", draft_id=draft.id)
        messages.success(request, SUCCESS_MESSAGES["draft_updated"])
        return _redirect_step(
            draft_id=draft.id,
            requested=form.cleaned_data["next"],
            fallback="address",
        )
    context = draft_page_context(draft=draft, current_step="basic")
    context["form"] = form
    return render(request, "app/draft_basic.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def address_edit(request: HttpRequest, draft_id) -> HttpResponse:
    draft = get_draft_for_edit(draft_id=draft_id, user=request.user)
    initial = {**draft.data["address"], "revision": draft.revision}
    form = AddressForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            update_address(
                draft_id=draft.id,
                owner=request.user,
                expected_revision=form.cleaned_data["revision"],
                postal_code=form.cleaned_data["postal_code"],
                prefecture=form.cleaned_data["prefecture"],
                city=form.cleaned_data["city"],
                address_line=form.cleaned_data["address_line"],
            )
        except DomainError as error:
            messages.error(request, message_for_error(error))
            return redirect("app:draft-address", draft_id=draft.id)
        messages.success(request, SUCCESS_MESSAGES["draft_updated"])
        return _redirect_step(
            draft_id=draft.id,
            requested=form.cleaned_data["next"],
            fallback="members",
        )
    context = draft_page_context(draft=draft, current_step="address")
    context["form"] = form
    return render(request, "app/draft_address.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def members_edit(request: HttpRequest, draft_id) -> HttpResponse:
    draft = get_draft_for_edit(draft_id=draft_id, user=request.user)
    formset = MemberFormSet(
        request.POST or None,
        initial=member_initial(draft),
        prefix="members",
    )
    revision_form = RevisionForm(
        request.POST or None,
        initial={"revision": draft.revision},
    )
    if request.method == "POST" and formset.is_valid() and revision_form.is_valid():
        try:
            update_members(
                draft_id=draft.id,
                owner=request.user,
                expected_revision=revision_form.cleaned_data["revision"],
                members=[form.cleaned_data for form in formset.forms],
            )
        except DomainError as error:
            messages.error(request, message_for_error(error))
            return redirect("app:draft-members", draft_id=draft.id)
        messages.success(request, SUCCESS_MESSAGES["draft_updated"])
        return _redirect_step(
            draft_id=draft.id,
            requested=revision_form.cleaned_data["next"],
            fallback="attachments",
        )
    context = draft_page_context(draft=draft, current_step="members")
    context.update({"formset": formset, "revision_form": revision_form})
    return render(request, "app/draft_members.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def attachments_edit(request: HttpRequest, draft_id) -> HttpResponse:
    draft = get_draft_for_edit(draft_id=draft_id, user=request.user)
    formset = AttachmentFormSet(
        request.POST or None,
        request.FILES or None,
        initial=attachment_initial(draft),
        prefix="attachments",
    )
    revision_form = RevisionForm(
        request.POST or None,
        initial={"revision": draft.revision},
    )
    if request.method == "POST" and formset.is_valid() and revision_form.is_valid():
        try:
            update_attachments(
                draft_id=draft.id,
                owner=request.user,
                expected_revision=revision_form.cleaned_data["revision"],
                attachments=[form.cleaned_data for form in formset.forms],
            )
        except DomainError as error:
            messages.error(request, message_for_error(error))
            return redirect("app:draft-attachments", draft_id=draft.id)
        messages.success(request, SUCCESS_MESSAGES["draft_updated"])
        return _redirect_step(
            draft_id=draft.id,
            requested=revision_form.cleaned_data["next"],
            fallback="confirm",
        )
    context = draft_page_context(draft=draft, current_step="attachments")
    context.update({"formset": formset, "revision_form": revision_form})
    return render(request, "app/draft_attachments.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def confirm(request: HttpRequest, draft_id) -> HttpResponse:
    draft = get_draft_for_edit(draft_id=draft_id, user=request.user)
    form = RevisionForm(request.POST or None, initial={"revision": draft.revision})
    validation_errors = {}
    if request.method == "POST" and form.is_valid() and request.POST.get("action") != "submit":
        return _redirect_step(
            draft_id=draft.id,
            requested=form.cleaned_data["next"],
            fallback="confirm",
        )
    if request.method == "POST" and form.is_valid():
        try:
            submit_draft(
                draft_id=draft.id,
                owner=request.user,
                expected_revision=form.cleaned_data["revision"],
            )
        except ValidationError as error:
            validation_errors = error.errors
            messages.error(request, message_for_error(error))
        except DomainError as error:
            messages.error(request, message_for_error(error))
            return redirect("app:draft-confirm", draft_id=draft.id)
        else:
            messages.success(request, SUCCESS_MESSAGES["application_submitted"])
            return redirect("app:application-list")
    context = draft_page_context(draft=draft, current_step="confirm")
    context.update({"form": form, "validation_errors": validation_errors})
    return render(request, "app/draft_confirm.html", context)
