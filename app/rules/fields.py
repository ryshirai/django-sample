import re

# Form の RegexField と Draft 全体検証の双方で使う郵便番号形式。
POSTAL_CODE_REGEX = r"^\d{3}-?\d{4}$"
POSTAL_CODE_PATTERN = re.compile(POSTAL_CODE_REGEX)

# 国内電話番号のざっくり形式（ハイフン任意）。
PHONE_REGEX = r"^0\d{1,4}-?\d{1,4}-?\d{3,4}$"
PHONE_PATTERN = re.compile(PHONE_REGEX)
