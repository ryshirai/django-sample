# Django Canon

AI と人間が Django 実装を同じ構造・責務・依存方向で再現するための正典（Canon）。

この文書は設計上の自由度より再現性を優先する。一般的な Django の選択肢を列挙する文書ではない。ここに規定された経路・公開 API・命名・禁止事項を、単純な CRUD を含むすべての実装で適用する。

## 1. Canon の優先順位

1. 明示されたプロダクト要件
2. この `docs/django-canon.md`
3. リポジトリ固有の仕様書
4. 既存コード
5. 一般的な Django 慣習

上位と下位が矛盾する場合は上位を優先する。ただし AI は矛盾を独自解釈で解消してはならず、人間へ確認する。

既存コードが Canon に違反していても、その違反を新規コードへコピーしない。要求範囲外の既存違反を無断で修正しない。

## 2. 基本原則

- Django 標準を優先する。
- Repository、独自 DI Container、不要な Interface / Protocol / BaseClass を導入しない。
- 読み取りと更新を分離する。
- ORM へ到達する公開経路を Selector と Service に限定する。
- 暗黙の副作用を作らない。
- 単純な CRUD でも固定経路を省略しない。
- 将来使うかもしれない抽象化、index、soft delete、共通基盤を先回りして追加しない。
- AI は要求範囲外の変更、依存追加、リファクタリングを行わない。
- 不明点は推測せず確認する。

## 3. 標準処理経路

### 3.1 読み取り

```text
View / API / Command
        |
        v
     Selector
        |
        v
   Model / ORM
```

### 3.2 更新・副作用

```text
View / API / Command
        |
        v
      Service
        |
        v
   Model / ORM
```

Form / Serializer は入力境界であり ORM を触らない。

Service と Selector は相互に呼ばない。public Service 同士も呼ばない。

## 4. 固定ディレクトリ

business Django app は `application` 1つだけとする。

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
│   ├── forms/
│   ├── views/
│   ├── templates/
│   └── urls.py
├── api/
│   ├── serializers/
│   ├── views/
│   └── urls.py
├── management/
│   └── commands/
├── admin.py
└── apps.py
```

`models.py` は作らず `models/` package を使う。primary Model 単位で Model / Service / Selector module を分割する。

`utils.py`、`common.py`、`misc.py` は禁止する。責務を命名できないコードは置き場所を決め直す。

## 5. 依存方向

| 呼び出し元 | 呼び出し可能 | 呼び出し禁止 |
|---|---|---|
| View / API | Form / Serializer, Service, Selector, Error mapping | ORM 直接操作 |
| Form / Serializer | pure Validator, Input dataclass 構築 | ORM, Service, Selector |
| Service | Model, Error, Message code, pure Validator, Audit API | Selector, 他 public Service, View / API |
| Selector | Model, Filter dataclass, Error | Service, View / API, 書き込み ORM |
| Model | 自身の instance 値だけを使う pure method | Service, Selector, 外部 I/O, ORM query |
| Admin | Selector | 独自 ORM 更新, Service 経由の更新 |
| Command | Service, Selector | ORM 直接操作 |

循環依存を解消するために依存方向を破ってはならない。責務配置を見直す。

## 6. 命名

コード上の識別子は英語のみ。

| 対象 | 規則 | 例 |
|---|---|---|
| Model | singular PascalCase | `PurchaseApplication` |
| Service | `<verb>_<noun>` | `submit_application` |
| Service Input | `<Verb><Noun>Input` | `SubmitApplicationInput` |
| Single Selector | `get_<noun>` | `get_purchase_application` |
| List Selector | `list_<plural>` | `list_purchase_applications` |
| Filter | `<Noun>Filter` | `PurchaseApplicationFilter` |
| Form | `<Verb><Noun>Form` | `CreatePurchaseApplicationForm` |
| API Input | `<Verb><Noun>InputSerializer` | `CreatePurchaseApplicationInputSerializer` |
| API Output | `<Noun>OutputSerializer` | `PurchaseApplicationOutputSerializer` |
| API List item | `<Noun>ListItemOutputSerializer` | `PurchaseApplicationListItemOutputSerializer` |
| View | `<noun>_<action>` | `purchase_application_create` |
| Error class | `<Noun><Reason>Error` | `PurchaseApplicationNotFoundError` |
| Error code | `<noun>.<reason>` | `purchase_application.not_found` |

`handler`, `process`, `execute`, `do`, `manager`, `helper` のように責務が曖昧な名前を公開 API に使わない。

## 7. Service

public Service は class ではなく module function とする。

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class SubmitApplicationInput:
    application_id: int
    expected_revision: int


@transaction.atomic
def submit_application(*, input: SubmitApplicationInput) -> None:
    application = PurchaseApplication.objects.select_for_update().get(
        pk=input.application_id,
    )
    application.status = PurchaseApplication.Status.SUBMITTED
    application.save(update_fields=["status"])
```

### 7.1 契約

- public Service は Use Case 固有 Input dataclass のみを業務入力として受ける。
- Input は `@dataclass(frozen=True, slots=True, kw_only=True)`。
- Input に Model instance / QuerySet / request / Form / Serializer を入れない。
- ID、文字列、数値、日付、Enum / Choices 等の値を渡す。
- primary Model ごとに module を分割する。
- 更新 Service は `transaction.atomic` 必須。
- 既存行を更新する場合は原則 `select_for_update()` でロックする。
- `save()` は `update_fields=[...]` を明示する。
- 削除は Service 内で明示的に行う。
- Service は Selector を呼ばない。
- public Service から別 public Service を呼ばない。
- 同一 Use Case の分割は同一 module 内 private function とする。

### 7.2 複数 Model 更新

1つの Use Case が複数 Model / table を更新する場合でも、入口となる public Service は1つにする。同一 transaction 内で必要な Model を直接取得・更新し、private helper へ分割する。

public Service の連鎖でオーケストレーションしない。

### 7.3 読み取りを伴う更新

更新判断に DB 読み取りが必要でも Selector は呼ばない。Service 自身が ORM で必要な行を取得する。読み取りロジックの重複を避けるために Service → Selector を許可することはしない。

## 8. Selector

public Selector は module function とする。

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class PurchaseApplicationFilter:
    status: PurchaseApplication.Status | None = None


def get_purchase_application(*, application_id: int) -> PurchaseApplication:
    try:
        return PurchaseApplication.objects.get(pk=application_id)
    except PurchaseApplication.DoesNotExist as error:
        raise PurchaseApplicationNotFoundError() from error


def list_purchase_applications(
    *,
    filter: PurchaseApplicationFilter,
) -> QuerySet[PurchaseApplication]:
    queryset = PurchaseApplication.objects.all()
    if filter.status is not None:
        queryset = queryset.filter(status=filter.status)
    return queryset
```

### 8.1 契約

- 単一取得は keyword-only 引数。
- 不存在は typed NotFound Error。`None` を返さない。
- 一覧・検索は未評価 QuerySet を返す。
- 一覧条件は frozen Filter dataclass にまとめる。
- Selector は DB write を行わない。
- `select_related` / `prefetch_related` / `annotate` / `only` 等の読み取り最適化は Selector 内に置ける。
- custom Manager / custom QuerySet へ読み取り責務を逃がさない。

### 8.2 Timeline 例外

ページング、複数種別統合、既評価データの合成等により QuerySet 契約を維持できない Timeline は、仕様で明示された場合のみ評価済み immutable DTO sequence を返してよい。AI が独自に Timeline 例外を作ってはならない。

## 9. Model

Model は ORM 定義、DB constraint、自身の instance 値だけから計算できる pure behavior のみを持つ。

許可例:

```python
def is_submitted(self) -> bool:
    return self.status == self.Status.SUBMITTED
```

禁止:

- Model method 内 ORM query
- related manager への暗黙アクセス
- Model method による状態変更
- Model method 内 `save()` / `delete()`
- `save()` / `delete()` override
- custom Manager / custom QuerySet
- project 固有 Signal
- 独自 `clean()` / `full_clean()`
- 外部 I/O

主キーは原則 `BigAutoField`。共通 BaseModel を作らない。timestamp、soft delete 等も必要な Model に明示する。

DB constraint は DB で保証すべき不変条件に使う。speculative index は追加しない。

## 10. Validator

Validator は pure function とする。

- ORM を呼ばない。
- Service / Selector を呼ばない。
- request / Form / Serializer に依存しない。
- 値を受け取り、成功時は値を返すか `None`、失敗時は定義済み typed business error を送出する。
- 複数境界で再利用される値レベルのルールだけを置く。

DB 状態を必要とする検証は pure Validator ではない。読み取りなら Selector、更新 Use Case の事前条件なら Service 内で実施する。

## 11. Form

- `forms.Form` のみ使用する。
- `ModelForm` 禁止。
- `ModelChoiceField` 禁止。
- ORM / Service / Selector を呼ばない。
- HTTP 入力の型、必須、形式、同一入力内整合を検証する。
- DB ID の choice 表示が必要なら View が Selector で候補を取得し、Form constructor に値の sequence として渡す。
- `cleaned_data` から Service Input dataclass を構築できる境界とする。

## 12. Serializer

- `serializers.Serializer` のみ使用する。
- `ModelSerializer` 禁止。
- `PrimaryKeyRelatedField` 禁止。
- Input と Output を必ず別 class にする。
- ORM / Service / Selector を呼ばない。
- Input Serializer は値の検証と Service Input 構築まで。
- Output Serializer は View が Selector / Service から得た出力の表現に限定する。

## 13. View

View は function-based view のみ。CBV / writing generic CBV / `ModelViewSet` を禁止する。

### 13.1 MPA

- GET は Selector で読み取る。
- POST は Form → Service。
- 成功 POST は必ず Redirect する（Post/Redirect/Get）。
- ORM を直接呼ばない。
- Service 戻り Model を View で mutation / save しない。
- user-facing message は `messages` package の定義済み message を使用する。

### 13.2 API

- prefix は `/api/v1/` 固定。
- Input Serializer → Service / Selector → Output Serializer の順とする。
- 成功 status は endpoint 種別ごとに仕様で固定する。
- error response は共通 envelope に固定する。

```json
{
  "error": {
    "code": "purchase_application.not_found",
    "message": "...",
    "details": {}
  }
}
```

未定義の status / error code / envelope を AI が発明しない。

## 14. Admin

Admin は原則 read / inspect 用とする。

- 読み取りに Selector を利用できる。
- 独自 ORM 更新は禁止。
- Service 経由の更新も禁止。
- 業務更新が必要なら通常の Web / API Use Case を用意する。
- Django admin 標準が内部で行う ORM 操作まで禁止対象とはしない。ただし独自 action / `save_model` 等で業務更新を追加しない。

## 15. Management Command

Command は orchestration boundary とする。

- 読み取りは Selector。
- 更新は Service。
- ORM 直接操作は禁止。
- business logic を Command に実装しない。

## 16. Error と Message

予測可能な業務失敗は typed custom exception を使う。business error に Django `ValidationError` を使わない。

```python
class PurchaseApplicationNotFoundError(Exception):
    code = "purchase_application.not_found"
```

- Error class と error code を `errors/` に集約する。
- user-facing message は `messages/` に集約する。
- code と message を分離する。
- literal message を View / Service / Model 等へ分散させない。
- 未定義 code / message を AI が発明しない。
- programmer error は business error に変換して握り潰さない。

## 17. Audit

Audit が要求される場合のみ `audit/` を使用する。

- Service から公開 Audit API を呼べる。
- Audit API は業務 Service を呼ばない。
- audit failure の transaction 方針は仕様で明示する。
- 任意の audit / log を AI 判断で追加しない。

## 18. Logging

既存 logging policy に従う。要求されていない log を追加しない。`print()` は禁止。

秘密情報、credential、token、password、個人情報を log へ出さない。

## 19. Transaction と競合

- 更新 Service は `transaction.atomic`。
- 更新対象の既存行は原則 `select_for_update()`。
- lock 順序が複数 Model にまたがる場合は module 内で順序を固定する。
- 外部 I/O を DB transaction 内に入れる必要がある場合は、失敗整合性を仕様で決める。AI が勝手に `on_commit` や retry を導入しない。
- optimistic revision を採用する場合は仕様で明示し、競合は typed error とする。

## 20. 外部 I/O

メール、Storage、HTTP API、queue 等は ORM とは別の副作用である。

- View / Form / Serializer / Model / Selector から直接実行しない。
- Service が Use Case として起動する。
- 外部 I/O 用 adapter が必要な場合も、要求された integration 単位の具体 module とし、汎用 Repository / DI abstraction を作らない。
- transaction との整合性、再試行、冪等性が必要なら仕様で定義する。

## 21. Complexity

public / private function とも以下を上限とする。

- cyclomatic complexity ≤ 10
- branch 数 ≤ 12
- statement 数 ≤ 50

超過時は同一 module 内 private function へ責務を分割する。閾値回避の `# noqa` は禁止。

## 22. Type / Lint / Format

- mypy strict 必須。
- Ruff Formatter + Linter を唯一の formatter / linter とする。
- `# noqa` 禁止。
- `type: ignore` 禁止。
- 型エラーを suppression せず、型境界を修正する。

## 23. Test Canon

- Use Case の更新仕様は Service test で検証する。
- 読み取り条件は Selector test で検証する。
- Form / Serializer は入力境界を検証する。
- View test は HTTP routing、status、redirect、message / response mapping を中心にする。
- Model test は pure behavior と DB constraint を中心にする。
- private helper を直接 test せず public contract 経由で検証する。
- test 名は仕様を説明する英語名にする。
- 実装詳細に依存する過剰 mock を避ける。

## 24. Canonical boundary decisions

### 24.1 Service から複雑な read が必要

Selector を呼ばない。Service module 内 private query helper、または Service 内 ORM を使う。read API の再利用より依存方向を優先する。

### 24.2 複数 Use Case で同じ更新ロジックが必要

public Service を共通関数として呼び回さない。完全に同じ primary Model の内部操作なら、その Model の Service module 内 private helper として共有する。module をまたぐ共通化が必要に見える場合は人間に設計確認する。

### 24.3 Form の select choices に DB 値が必要

View → Selector で取得し、Form へ `(value, label)` 等の pure data を渡す。Form から Selector を呼ばない。

### 24.4 Service が作成後 Model を View に返したい

原則 ID または immutable result dataclass を返す。View が Model を変更できる契約を作らない。画面表示の再取得が必要なら Redirect 後 GET で Selector を使う。

### 24.5 NotFound と業務上の利用不可

存在しないことは typed NotFound Error。存在するが現在の状態では操作できないことは別の typed business error。Selector の filter で「操作不可」を「不存在」に偽装しない。

### 24.6 uniqueness の確認

表示・事前案内の read は Selector に置ける。更新時の競合防止は Service + DB constraint が最終責任を持つ。事前 SELECT だけを整合性保証にしない。

### 24.7 bulk update / bulk create

性能要件または仕様上必要な場合のみ Service 内で使用する。`save()`、signal 等が走らない性質を理解し、Canon の暗黙副作用禁止と整合させる。AI が性能推測だけで導入しない。

### 24.8 soft delete

原則導入しない。要件で必要な場合のみ、通常の状態として Model に明示し、全 Selector / Service 契約を仕様化してから採用する。共通 BaseModel や custom Manager で暗黙化しない。

### 24.9 Django authentication / permission

Django 標準 authentication / permission framework の内部 ORM は禁止対象外。アプリ固有の ownership / business authorization query は Selector または Service の責務として明示する。

### 24.10 migration

migration は Django migration framework を使う。data migration が必要な場合、migration の historical model API は例外として ORM を直接使用できる。runtime Service / Selector を migration から import しない。

## 25. 禁止パターン一覧

- Repository
- 独自 DI Container
- 不要な Interface / Protocol / BaseClass
- Service class / Selector class
- `utils.py` / `common.py` / `misc.py`
- custom Manager / QuerySet
- project 固有 Django Signal
- Model `save` / `delete` override
- Model 独自 `clean` / `full_clean`
- ModelForm / ModelSerializer
- ModelChoiceField / PrimaryKeyRelatedField
- ModelViewSet / writing generic CBV
- View / Form / Serializer / Command / Admin の ORM 直接操作
- Service → Selector
- Selector → Service
- public Service → public Service
- Selector の DB write
- View による Service 戻り Model の mutation / save
- business error への Django ValidationError
- user-facing message literal の分散
- `# noqa` / `type: ignore`
- `print()`
- 任意の log 追加
- soft delete / BaseModel の無断追加
- speculative index
- 要求外 dependency の追加
- 要求外 abstraction / refactor

## 26. AI 実装プロトコル

AI は実装前に以下を順に判定する。

1. 要求を read / write / boundary / infrastructure に分類する。
2. primary Model を特定する。
3. 変更対象 module と公開 API 名を Canon から決める。
4. 既存仕様と Canon の矛盾を確認する。
5. 不明な business rule / code / message / status があれば作業を止めて確認する。
6. 最小変更で実装する。
7. Ruff、mypy、test を実行する。
8. 禁止依存と ORM 直接操作をセルフレビューする。

AI がしてはならないこと:

- 「より綺麗」「将来便利」を理由に構造を変更する。
- 既存の違反を見つけたことを理由に要求範囲を拡張する。
- 未定義仕様を一般論で補完する。
- test を通すために Canon を回避する。

## 27. Definition of Done

- [ ] Read は Selector、Write / Side Effect は Service を通る
- [ ] View / API / Form / Serializer / Command / Admin に禁止 ORM がない
- [ ] Service ↔ Selector 呼び出しがない
- [ ] public Service 間呼び出しがない
- [ ] 更新 Service が `transaction.atomic` を持つ
- [ ] 既存行更新で必要な lock と `update_fields` が明示されている
- [ ] Model が pure contract を守る
- [ ] Input / Filter dataclass が frozen + slots + kw_only
- [ ] Form / Serializer が ORM 非依存
- [ ] typed error code と message が分離されている
- [ ] message literal が分散していない
- [ ] complexity 上限内
- [ ] mypy strict が通る
- [ ] Ruff が通る
- [ ] test が通る
- [ ] `noqa` / `type: ignore` / `print()` がない
- [ ] 要求外 dependency / abstraction / index / log がない
- [ ] 未定義仕様を AI が発明していない

## 28. Canon の変更

Canon 自体の変更は通常実装と分離してレビューする。個別機能を通すためにその場で Canon を緩和しない。

例外が必要な場合は、少なくとも以下を明文化する。

- どの規則の例外か
- なぜ通常規則では成立しないか
- 適用範囲
- 代替案を採用しない理由
- 例外が恒久か一時的か

一度の例外を暗黙の新ルールとして横展開しない。
