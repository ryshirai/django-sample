from app.errors import DomainError

SUCCESS_MESSAGES = {
    "draft_created": "入力を開始しました。",
    "draft_updated": "入力内容を保存しました。",
    "draft_deleted": "下書きを削除しました。",
    "application_submitted": "申請を受け付けました。",
    "application_cancelled": "申請を取り消しました。",
    "review_started": "審査を開始しました。",
    "application_approved": "申請を承認しました。",
    "application_rejected": "申請を却下しました。",
}

ERROR_MESSAGES = {
    "draft_validation_error": "入力内容全体を確認してください。",
    "draft_conflict": "別の画面で更新されています。最新の内容を読み直してください。",
    "application_locked": "この申請はロックされているため編集できません。",
    "draft_not_editable": "この下書きはすでに確定済みです。",
    "invalid_application_state": "現在の申請状態ではその操作を実行できません。",
    "staff_permission_required": "この操作にはスタッフ権限が必要です。",
}


def message_for_error(error: DomainError) -> str:
    return ERROR_MESSAGES.get(error.code, "処理を完了できませんでした。")
