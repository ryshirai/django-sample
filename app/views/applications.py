from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from app.errors import DomainError
from app.forms import ApplicationListFilterForm
from app.messages import SUCCESS_MESSAGES, message_for_error
from app.models import Application
from app.presentation import status_history_rows
from app.selectors import (
    application_list as select_application_list,
)
from app.selectors import (
    editing_draft_list,
    get_application_for_edit,
    get_application_for_owner,
    get_draft_for_edit,
)
from app.services import cancel_application, create_draft, delete_draft


@login_required
@require_GET
def application_list(request: HttpRequest) -> HttpResponse:
    filter_form = ApplicationListFilterForm(request.GET or None)
    status = ""
    query = ""
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get("status") or ""
        query = (filter_form.cleaned_data.get("query") or "").strip()

    return render(
        request,
        "app/application_list.html",
        {
            "applications": select_application_list(
                user=request.user,
                status=status or None,
                query=query or None,
            ),
            "drafts": editing_draft_list(user=request.user),
            "filter_form": filter_form,
            "editable_statuses": Application.EDITABLE_STATUSES,
        },
    )


@login_required
@require_GET
def application_detail(request: HttpRequest, application_id: UUID) -> HttpResponse:
    application = get_application_for_owner(
        application_id=application_id,
        user=request.user,
    )
    return render(
        request,
        "app/application_detail.html",
        {
            "application": application,
            "can_edit": application.status in Application.EDITABLE_STATUSES,
            "can_cancel": application.status == Application.Status.SUBMITTED,
            "status_history_rows": status_history_rows(application=application),
        },
    )


@login_required
@require_POST
def draft_create(request: HttpRequest) -> HttpResponse:
    draft = create_draft(owner=request.user)
    messages.success(request, SUCCESS_MESSAGES["draft_created"])
    return redirect("app:draft-basic", draft_id=draft.id)


@login_required
@require_POST
def edit_start(request: HttpRequest, application_id: UUID) -> HttpResponse:
    get_application_for_edit(application_id=application_id, user=request.user)
    try:
        draft = create_draft(owner=request.user, application_id=application_id)
    except DomainError as error:
        messages.error(request, message_for_error(error))
        return redirect("app:application-list")
    messages.success(request, SUCCESS_MESSAGES["draft_created"])
    return redirect("app:draft-basic", draft_id=draft.id)


@login_required
@require_POST
def draft_delete(request: HttpRequest, draft_id: UUID) -> HttpResponse:
    get_draft_for_edit(draft_id=draft_id, user=request.user)
    try:
        delete_draft(draft_id=draft_id, owner=request.user)
    except DomainError as error:
        messages.error(request, message_for_error(error))
    else:
        messages.success(request, SUCCESS_MESSAGES["draft_deleted"])
    return redirect("app:application-list")


@login_required
@require_POST
def application_cancel(request: HttpRequest, application_id: UUID) -> HttpResponse:
    get_application_for_owner(application_id=application_id, user=request.user)
    try:
        cancel_application(application_id=application_id, owner=request.user)
    except DomainError as error:
        messages.error(request, message_for_error(error))
        return redirect("app:application-detail", application_id=application_id)
    messages.success(request, SUCCESS_MESSAGES["application_cancelled"])
    return redirect("app:application-detail", application_id=application_id)
