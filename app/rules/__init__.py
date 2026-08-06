"""画面 Form と Draft 全体検証が共有する制約・エラーコード。"""

from .codes import ValidationCode
from .fields import POSTAL_CODE_PATTERN, POSTAL_CODE_REGEX

__all__ = [
    "POSTAL_CODE_PATTERN",
    "POSTAL_CODE_REGEX",
    "ValidationCode",
]
