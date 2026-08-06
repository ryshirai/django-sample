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
    ValidationCode.CONTACT_PHONE_REQUIRED: "連絡先電話番号は必須です。",
    ValidationCode.CONTACT_PHONE_INVALID: "電話番号の形式が正しくありません。",
    ValidationCode.CONTACT_PHONE_FORM_INVALID: (
        "電話番号は 03-1234-5678 などの形式で入力してください。"
    ),
    ValidationCode.CONTACT_EMAIL_REQUIRED: "連絡先メールアドレスは必須です。",
    ValidationCode.PREFERRED_CONTACT_METHOD_REQUIRED: "希望連絡手段を選択してください。",
    ValidationCode.MEMBER_REQUIRED: "担当者を1名以上登録してください。",
    ValidationCode.MEMBER_EMAIL_DUPLICATE: "担当者のメールアドレスが重複しています。",
    ValidationCode.EMAIL_DUPLICATE: "メールアドレスが重複しています。",
    ValidationCode.OWNER_REQUIRED: "責任者を1名以上指定してください。",
    ValidationCode.MEMBER_ROW_ID_DUPLICATE: "担当者の行IDが重複しています。",
    ValidationCode.ATTACHMENT_ROW_ID_DUPLICATE: "添付の行IDが重複しています。",
    ValidationCode.BUDGET_ROW_ID_DUPLICATE: "経費明細の行IDが重複しています。",
    ValidationCode.BUDGET_AMOUNT_INVALID: "金額は1円以上の整数で入力してください。",
    ValidationCode.BUDGET_DESCRIPTION_REQUIRED: "経費の内容は必須です。",
    ValidationCode.BUDGET_CATEGORY_REQUIRED: "経費区分を選択してください。",
    ValidationCode.ROW_ID_DUPLICATE_RELOAD: "行IDが重複しています。再読み込みしてください。",
    ValidationCode.ATTACHMENT_FILE_REQUIRED: "添付ファイルが選択されていません。",
    ValidationCode.FILE_REQUIRED: "ファイルを選択してください。",
    ValidationCode.INVALID_MEMBER_SOURCE: "不正な担当者IDが含まれています。",
    ValidationCode.INVALID_ATTACHMENT_SOURCE: "不正な添付IDが含まれています。",
    ValidationCode.INVALID_BUDGET_SOURCE: "不正な経費明細IDが含まれています。",
    ValidationCode.REJECTION_REASON_REQUIRED: "却下理由を入力してください。",
    ValidationCode.MODEL_FIELD_REQUIRED: "必須項目が未入力です。",
    ValidationCode.MODEL_FIELD_INVALID: "入力内容が正しくありません。",
    ValidationCode.MODEL_FIELD_MAX_LENGTH: "文字数が上限を超えています。",
    ValidationCode.MODEL_FIELD_MIN_LENGTH: "文字数が不足しています。",
    ValidationCode.MODEL_FIELD_UNIQUE: "既に登録されている値です。",
    ValidationCode.MODEL_VALIDATION_FAILED: "入力内容を確認してください。",
}


def localize_validation_errors(errors: dict[str, list[str]]) -> dict[str, list[str]]:
    """フィールドごとの検証コードを表示文言へ変換する。"""
    return {
        field: [VALIDATION_MESSAGES.get(code, code) for code in codes]
        for field, codes in errors.items()
    }
