from django.contrib.auth.base_user import AbstractBaseUser

from app.models import Application, ApplicationStatusHistory


def record_status_change(
    *,
    application: Application,
    from_status: str,
    to_status: str,
    changed_by: AbstractBaseUser,
    comment: str = "",
) -> ApplicationStatusHistory:
    """ステータス遷移を監査ログへ記録する。"""
    return ApplicationStatusHistory.objects.create(
        application=application,
        from_status=from_status,
        to_status=to_status,
        changed_by=changed_by,
        comment=comment,
    )
