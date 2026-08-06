from app.rules import ValidationCode

# ValidationCode -> 表示文言。ドメイン層はコードのみを返し、ここで解決する。
VALIDATION_MESSAGES = {
    ValidationCode.BASIC_TITLE_REQUIRED: "申請名は必須です。",
    ValidationCode.BASIC_PURPOSE_REQUIRED: "申請目的は必須です。",
    ValidationCode.PREFECTURE_REQUIRED: "都道府県は必須です。",
    ValidationCode.CITY_REQUIRED: "市区町村は必須です。",
    ValidationCode.ADDRESS_LINE_REQUIRED: "番地は必須です。",
    ValidationCode.POSTAL_CODE_INVALID: "郵便番号の形式が正しくありません。",
    ValidationCode.POSTAL_CODE_FORM_INVALID: "123-4567 の形式で入力してください。",
    ValidationCode.MEMBER_REQUIRED: "担当者を1名以上登録してください。",
    ValidationCode.MEMBER_EMAIL_DUPLICATE: "担当者のメールアドレスが重複しています。",
    ValidationCode.EMAIL_DUPLICATE: "メールアドレスが重複しています。",
    ValidationCode.OWNER_REQUIRED: "責任者を1名以上指定してください。",
    ValidationCode.MEMBER_ROW_ID_DUPLICATE: "担当者の行IDが重複しています。",
    ValidationCode.ATTACHMENT_ROW_ID_DUPLICATE: "添付の行IDが重複しています。",
    ValidationCode.ROW_ID_DUPLICATE_RELOAD: "行IDが重複しています。再読み込みしてください。",
    ValidationCode.ATTACHMENT_FILE_REQUIRED: "添付ファイルが選択されていません。",
    ValidationCode.FILE_REQUIRED: "ファイルを選択してください。",
    ValidationCode.INVALID_MEMBER_SOURCE: "不正な担当者IDが含まれています。",
    ValidationCode.INVALID_ATTACHMENT_SOURCE: "不正な添付IDが含まれています。",
}


def localize_validation_errors(errors: dict[str, list[str]]) -> dict[str, list[str]]:
    """フィールドごとの検証コードを表示文言へ変換する。"""
    return {
        field: [VALIDATION_MESSAGES.get(code, code) for code in codes]
        for field, codes in errors.items()
    }
