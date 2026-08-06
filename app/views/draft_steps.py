from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from app.drafts import AddressPayload, AttachmentPayload, BasicPayload, MemberPayload
from app.errors import DomainError, ValidationError
from app.forms import AddressForm, AttachmentFormSet, BasicForm, MemberFormSet, RevisionForm
from app.messages import SUCCESS_MESSAGES, localize_validation_errors, message_for_error
from app.presentation import attachment_initial, draft_page_context, member_initial
from app.selectors import get_draft_for_edit
from app.services import (
    submit_draft,
    update_address,
    update_attachments,
    update_basic,
    update_members,
)

from .helpers import redirect_after_save, run_draft_update


@login_required
@require_http_methods(["GET", "POST"])
def basic_edit(request: HttpRequest, draft_id) -> HttpResponse:
    draft = get_draft_for_edit(draft_id=draft_id, user=request.user)
    form = BasicForm(
        request.POST or None,
        initial={**draft.data["basic"], "revision": draft.revision},
    )
    if request.method == "POST" and form.is_valid():
        response = run_draft_update(
            request=request,
            draft_id=draft.id,
            current_step="basic",
            fallback_step="address",
            next_step=form.cleaned_data["next"],
            update=lambda: update_basic(
                draft_id=draft.id,
                owner=request.user,
                expected_revision=form.cleaned_data["revision"],
                payload=BasicPayload(
                    title=form.cleaned_data["title"],
                    purpose=form.cleaned_data["purpose"],
                ),
            ),
        )
        if response is not None:
            return response
    context = draft_page_context(draft=draft, current_step="basic")
    context["form"] = form
    return render(request, "app/draft_basic.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def address_edit(request: HttpRequest, draft_id) -> HttpResponse:
    draft = get_draft_for_edit(draft_id=draft_id, user=request.user)
    form = AddressForm(
        request.POST or None,
        initial={**draft.data["address"], "revision": draft.revision},
    )
    if request.method == "POST" and form.is_valid():
        response = run_draft_update(
            request=request,
            draft_id=draft.id,
            current_step="address",
            fallback_step="members",
            next_step=form.cleaned_data["next"],
            update=lambda: update_address(
                draft_id=draft.id,
                owner=request.user,
                expected_revision=form.cleaned_data["revision"],
                payload=AddressPayload(
                    postal_code=form.cleaned_data["postal_code"],
                    prefecture=form.cleaned_data["prefecture"],
                    city=form.cleaned_data["city"],
                    address_line=form.cleaned_data["address_line"],
                ),
            ),
        )
        if response is not None:
            return response
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
        payloads = [
            MemberPayload(
                row_id=item["row_id"],
                source_id=item.get("source_id"),
                name=item["name"],
                email=item["email"],
                role=item["role"],
            )
            for item in (form.cleaned_data for form in formset.forms)
            if not item.get("DELETE")
        ]
        response = run_draft_update(
            request=request,
            draft_id=draft.id,
            current_step="members",
            fallback_step="attachments",
            next_step=revision_form.cleaned_data["next"],
            update=lambda: update_members(
                draft_id=draft.id,
                owner=request.user,
                expected_revision=revision_form.cleaned_data["revision"],
                members=payloads,
            ),
        )
        if response is not None:
            return response
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
        payloads = [
            AttachmentPayload(
                row_id=item["row_id"],
                source_id=item.get("source_id"),
                label=item["label"],
                file=item.get("file"),
                existing_file_name=item.get("existing_file_name") or "",
                delete=bool(item.get("DELETE")),
            )
            for item in (form.cleaned_data for form in formset.forms)
        ]
        response = run_draft_update(
            request=request,
            draft_id=draft.id,
            current_step="attachments",
            fallback_step="confirm",
            next_step=revision_form.cleaned_data["next"],
            update=lambda: update_attachments(
                draft_id=draft.id,
                owner=request.user,
                expected_revision=revision_form.cleaned_data["revision"],
                attachments=payloads,
            ),
        )
        if response is not None:
            return response
    context = draft_page_context(draft=draft, current_step="attachments")
    context.update({"formset": formset, "revision_form": revision_form})
    return render(request, "app/draft_attachments.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def confirm(request: HttpRequest, draft_id) -> HttpResponse:
    draft = get_draft_for_edit(draft_id=draft_id, user=request.user)
    form = RevisionForm(request.POST or None, initial={"revision": draft.revision})
    validation_errors: dict[str, list[str]] = {}

    if request.method == "POST" and form.is_valid():
        # ステップナビは確定せず遷移のみ。
        if request.POST.get("action") != "submit":
            return redirect_after_save(
                draft_id=draft.id,
                requested=form.cleaned_data["next"],
                fallback="confirm",
            )
        try:
            submit_draft(
                draft_id=draft.id,
                owner=request.user,
                expected_revision=form.cleaned_data["revision"],
            )
        except ValidationError as error:
            # ドメインはコードのみ返すので、ここで表示文言へ変換する。
            validation_errors = localize_validation_errors(error.errors)
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
