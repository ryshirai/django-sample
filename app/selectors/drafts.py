from django.shortcuts import get_object_or_404

from app.models import ApplicationDraft


def editing_draft_list(*, user):
    return ApplicationDraft.objects.owned_by(user).editing().order_by("-updated_at")


def get_draft_for_view(*, draft_id, user) -> ApplicationDraft:
    return get_object_or_404(ApplicationDraft.objects.owned_by(user), pk=draft_id)


def get_draft_for_edit(*, draft_id, user) -> ApplicationDraft:
    return get_object_or_404(
        ApplicationDraft.objects.owned_by(user).editing(),
        pk=draft_id,
    )
