# AGENTS.md

AI がこのリポジトリで実装するときの最上位実装規約は `docs/django-canon.md` とする。

## 必須ルール

- 実装前に `docs/django-canon.md` を読む。
- Read は `View / API / Command → Selector → Model / ORM`。
- Write / Side Effect は `View / API / Command → Service → Model / ORM`。
- Service と Selector は相互に呼ばない。public Service 同士も呼ばない。
- View / Form / Serializer / Command / Admin から ORM を直接操作しない。
- Model は ORM 定義・DB constraint・instance 値だけの pure behavior に限定する。
- custom Manager / QuerySet、Signal、ModelForm、ModelSerializer、CBV、Repository、独自 DI を追加しない。
- public Service / Selector は module function とする。
- Service Input は Use Case 固有の `@dataclass(frozen=True, slots=True, kw_only=True)` とし、Model instance を入れない。
- 更新 Service は `transaction.atomic`。既存行更新は原則 `select_for_update()` と `save(update_fields=[...])`。
- Selector の一覧は未評価 QuerySet、単一取得の不存在は typed NotFound Error。
- business error は typed custom exception。user-facing message は `messages/` に集約する。
- `# noqa`、`type: ignore`、`print()`、要求されていない log を追加しない。
- 要求外の dependency、抽象化、soft delete、BaseModel、index、refactor を追加しない。
- 未定義の error code / message / API status / business rule を発明しない。不明点は人間に確認する。

## 固定構造

business Django app は `application` 1つとし、責務を以下へ分割する。

```text
application/
├── models/
├── services/
├── selectors/
├── validators/
├── errors/
├── messages/
├── audit/
├── web/
└── api/
```

primary Model 単位で module を分割する。`models.py`、`utils.py`、`common.py`、`misc.py` は作らない。

## 完了条件

実装後に Canon の Definition of Done を確認し、少なくとも Ruff、mypy strict、関連 test を実行する。

既存コードと Canon が矛盾する場合、既存コードを根拠に Canon を破らない。要求範囲外の既存違反も無断修正せず、人間へ報告する。
