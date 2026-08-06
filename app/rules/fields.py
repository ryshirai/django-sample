import re

# Form の RegexField と Draft 全体検証の双方で使う郵便番号形式。
POSTAL_CODE_REGEX = r"^\d{3}-?\d{4}$"
POSTAL_CODE_PATTERN = re.compile(POSTAL_CODE_REGEX)
