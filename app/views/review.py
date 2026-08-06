from uuid import UUID

from django.contrib import messages
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from app.errors import DomainError, ValidationError
from app.forms import RejectApplicationForm
from app.messages import SUCCESS_MESSAGES, localize_validation_errors, message_for_error
from app.models import Application
from app.presentation import status_history_rows
from app.selectors import get_application_for_review, review_queue
from app.services import approve_application, reject_application, start_review


def _is_staff(user: AbstractBaseUser) -> bool:
    return bool(user.is_authenticated and user.is_staff)


@login_required
@user_passes_test(_is_staff)
@require_GET
def review_list(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "app/review_list.html",
        {
            "applications": review_queue(),
            "submitted_status": Application.Status.SUBMITTED,
            "under_review_status": Application.Status.UNDER_REVIEW,
        },
    )


@login_required
@user_passes_test(_is_staff)
@require_http_methods(["GET", "POST"])
def review_detail(request: HttpRequest, application_id: UUID) -> HttpResponse:
    application = get_application_for_review(application_id=application_id)
    reject_form = RejectApplicationForm(request.POST or None)
    validation_errors: dict[str, list[str]] = {}

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "start_review":
                start_review(application_id=application.id, reviewer=request.user)
                messages.success(request, SUCCESS_MESSAGES["review_started"])
                return redirect("app:review-detail", application_id=application.id)
            if action == "approve":
                approve_application(application_id=application.id, reviewer=request.user)
                messages.success(request, SUCCESS_MESSAGES["application_approved"])
                return redirect("app:review-list")
            if action == "reject":
                if not reject_form.is_valid():
                    return render(
                        request,
                        "app/review_detail.html",
                        {
                            "application": application,
                            "reject_form": reject_form,
                            "validation_errors": validation_errors,
                            "status_history_rows": status_history_rows(
                                application=application
                            ),
                            "submitted_status": Application.Status.SUBMITTED,
                            "under_review_status": Application.Status.UNDER_REVIEW,
                        },
                    )
                reject_application(
                    application_id=application.id,
                    reviewer=request.user,
                    reason=reject_form.cleaned_data["reason"],
                )
                messages.success(request, SUCCESS_MESSAGES["application_rejected"])
                return redirect("app:review-list")
        except ValidationError as error:
            validation_errors = localize_validation_errors(error.errors)
            messages.error(request, message_for_error(error))
        except DomainError as error:
            messages.error(request, message_for_error(error))
            return redirect("app:review-detail", application_id=application.id)

    return render(
        request,
        "app/review_detail.html",
        {
            "application": application,
            "reject_form": reject_form,
            "validation_errors": validation_errors,
            "status_history_rows": status_history_rows(application=application),
            "submitted_status": Application.Status.SUBMITTED,
            "under_review_status": Application.Status.UNDER_REVIEW,
        },
    )


@login_required
@user_passes_test(_is_staff)
@require_POST
def review_start(request: HttpRequest, application_id: UUID) -> HttpResponse:
    """互換用の単独 POST エンドポイント。詳細画面の action でも可。"""
    get_application_for_review(application_id=application_id)
    try:
        start_review(application_id=application_id, reviewer=request.user)
    except DomainError as error:
        messages.error(request, message_for_error(error))
        return redirect("app:review-detail", application_id=application_id)
    messages.success(request, SUCCESS_MESSAGES["review_started"])
    return redirect("app:review-detail", application_id=application_id)
