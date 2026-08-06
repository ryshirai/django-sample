"""正式申請のテンプレート向け表示変換。"""

from app.models import Application


def status_label(*, status_code: str) -> str:
    """ステータスコードを表示ラベルへ。空は新規作成を表す。"""
    if not status_code:
        return "（新規）"
    return dict(Application.Status.choices).get(status_code, status_code)


def status_history_rows(*, application: Application) -> list[dict]:
    """状態履歴をテンプレート用の dict 列へ変換する。"""
    return [
        {
            "created_at": entry.created_at,
            "from_label": status_label(status_code=entry.from_status),
            "to_label": status_label(status_code=entry.to_status),
            "changed_by_username": entry.changed_by.username,
            "comment": entry.comment,
        }
        for entry in application.status_history.all()
    ]
