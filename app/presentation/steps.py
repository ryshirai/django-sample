"""入力ステップの定義。ラベル・URL 名・遷移の単一ソース。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Step:
    key: str
    label: str

    @property
    def route_name(self) -> str:
        return f"app:draft-{self.key}"


STEPS: tuple[Step, ...] = (
    Step("basic", "基本情報"),
    Step("address", "住所"),
    Step("contact", "連絡先"),
    Step("members", "担当者"),
    Step("budget", "経費明細"),
    Step("attachments", "添付"),
    Step("confirm", "確認"),
)

STEP_BY_KEY = {step.key: step for step in STEPS}
STEP_KEYS = frozenset(STEP_BY_KEY)


def resolve_step_key(requested: str | None, *, fallback: str) -> str:
    """POST された next を許可キーへ正規化する。"""
    if requested and requested in STEP_BY_KEY:
        return requested
    return fallback
