"""Draft ステップ View の共通 HTTP 処理。"""

from collections.abc import Callable
from uuid import UUID

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from app.errors import DomainError
from app.messages import SUCCESS_MESSAGES, message_for_error
from app.presentation import STEP_BY_KEY, resolve_step_key


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
    戻り値が None のときは呼び出し側が再表示する。
    """
    try:
        update()
    except DomainError as error:
        messages.error(request, message_for_error(error))
        return redirect_to_step(draft_id=draft_id, step_key=current_step)
    messages.success(request, SUCCESS_MESSAGES["draft_updated"])
    return redirect_after_save(
        draft_id=draft_id,
        requested=next_step,
        fallback=fallback_step,
    )
