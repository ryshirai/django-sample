"""Draft ステップ View の共通 HTTP 処理。"""

from collections.abc import Callable
from uuid import UUID

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from app.errors import DomainError, DraftNotEditableError
from app.messages import SUCCESS_MESSAGES, message_for_error
from app.models import ApplicationDraft
from app.presentation import STEP_BY_KEY, resolve_step_key
from app.selectors import get_draft_for_edit
from app.services import ensure_current_schema


def redirect_to_step(*, draft_id: UUID, step_key: str) -> HttpResponse:
    return redirect(STEP_BY_KEY[step_key].route_name, draft_id=draft_id)


def redirect_after_save(
    *,
    draft_id: UUID,
    requested: str | None,
    fallback: str,
) -> HttpResponse:
    step_key = resolve_step_key(requested, fallback=fallback)
    return redirect_to_step(draft_id=draft_id, step_key=step_key)


def load_editable_draft(
    *,
    request: HttpRequest,
    draft_id: UUID,
) -> tuple[ApplicationDraft | None, HttpResponse | None]:
    """
    所有者の Draft を取得し、編集中でなければ一覧へ Redirect する。

    404 は selector（存在しない / 所有者外）。編集不可は DomainError の文言付き Redirect。
    """
    draft = get_draft_for_edit(draft_id=draft_id, user=request.user)
    try:
        draft.ensure_editable()
    except DomainError as error:
        messages.error(request, message_for_error(error))
        return None, redirect("app:application-list")
    draft = ensure_current_schema(draft=draft)
    return draft, None


def run_draft_update(
    *,
    request: HttpRequest,
    draft_id: UUID,
    current_step: str,
    fallback_step: str,
    next_step: str | None,
    update: Callable[[], None],
) -> HttpResponse | None:
    """
    更新を実行し、成功時は次ステップへ、DomainError 時は同画面へ Redirect する。
    編集不可は一覧へ戻す。戻り値が None のときは呼び出し側が再表示する。
    """
    try:
        update()
    except DraftNotEditableError as error:
        messages.error(request, message_for_error(error))
        return redirect("app:application-list")
    except DomainError as error:
        messages.error(request, message_for_error(error))
        return redirect_to_step(draft_id=draft_id, step_key=current_step)
    messages.success(request, SUCCESS_MESSAGES["draft_updated"])
    return redirect_after_save(
        draft_id=draft_id,
        requested=next_step,
        fallback=fallback_step,
    )

