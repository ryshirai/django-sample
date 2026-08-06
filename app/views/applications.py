from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from app.errors import DomainError
from app.messages import SUCCESS_MESSAGES, message_for_error
from app.selectors import (
    application_list as select_application_list,
)
from app.selectors import (
    editing_draft_list,
    get_application_for_edit,
    get_draft_for_edit,
)
from app.services import create_draft, delete_draft


@login_required
@require_GET
def application_list(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "app/application_list.html",
        {
            "applications": select_application_list(user=request.user),
            "drafts": editing_draft_list(user=request.user),
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
