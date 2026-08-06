"""Django の full_clean / Field 検証コードをアプリの ValidationCode へ変換する。"""

from app.rules.codes import ValidationCode

# Django が ValidationError.code に載せる値 -> 言語非依存の ValidationCode。
# 未登録の code は MODEL_VALIDATION_FAILED に落とす（表示文言は messages 側）。
_DJANGO_CODE_TO_VALIDATION_CODE = {
    "required": ValidationCode.MODEL_FIELD_REQUIRED,
    "blank": ValidationCode.MODEL_FIELD_REQUIRED,
    "null": ValidationCode.MODEL_FIELD_REQUIRED,
    "invalid": ValidationCode.MODEL_FIELD_INVALID,
    "invalid_choice": ValidationCode.MODEL_FIELD_INVALID,
    "max_length": ValidationCode.MODEL_FIELD_MAX_LENGTH,
    "min_length": ValidationCode.MODEL_FIELD_MIN_LENGTH,
    "unique": ValidationCode.MODEL_FIELD_UNIQUE,
}


def validation_code_from_django(code: str | None) -> str:
    """Django ValidationError.code を ValidationCode 定数へマップする。"""
    if code is None:
        return ValidationCode.MODEL_VALIDATION_FAILED
    return _DJANGO_CODE_TO_VALIDATION_CODE.get(code, ValidationCode.MODEL_VALIDATION_FAILED)
