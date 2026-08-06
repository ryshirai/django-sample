# Django プロジェクト構成・コーディング規約

この文書は `django-sample` から抜き出した、**他プロジェクトでも同じ骨格で始められる**ための指針です。

| 文書 | 役割 |
|---|---|
| `AGENTS.md` | AI 向けの短い実装指示（本ファイルの要約） |
| 本ファイル | 骨格・責務・Python 可読性の本体（案件横断でコピーする） |
| 各リポジトリの README | ドメイン固有の設計・起動方法・代替案の比較 |

対象読者:

- 新規 Django プロジェクトを立ち上げる人
- AI に実装を依頼し、人間がレビュー・保守するチーム

前提:

- Python 3.13+ / Django 5.x を想定
- MPA（サーバレンダリング）・モノアプリ構成が主戦場
- Clean Architecture や Repository は持ち込まない
- **省略形や技巧より、人間が読める明示性を優先する**

### 5分チェックリスト（実装・レビュー共通）

1. 変更はどの層か。その層の「やってはいけないこと」を侵していないか
2. View に業務更新・トランザクションが混ざっていないか
3. Service に日本語文言・HTML・HTTP が混ざっていないか
4. 公開関数はキーワード専用（`*`）か。業務名は省略していないか
5. エラーは code、表示は `messages/` か
6. 所有者スコープは QuerySet（`owned_by` 等）に寄っているか
7. テスト名で「何を守るか」が読めるか

---

## 1. この構成の狙い

### 1.1 やること

| 狙い | 具体策 |
|---|---|
| HTTP と業務を分ける | View は入出力、Service が更新とトランザクション |
| 読取と書込を分ける | selector / QuerySet が読取、Service が書込 |
| エラーと文言を分ける | ドメインは言語非依存コード、messages が日本語 |
| 画面検証と業務検証を分ける | Form → ユースケース検証 → Model/DB 制約 |
| 公開境界を明示する | 各パッケージの `__init__.py` と `__all__` |
| AI が迷わず増やせる | 層ごとの「持たない責務」を固定する |

### 1.2 やらないこと

- ORM を包むだけの Repository
- エンティティ変換だらけの Clean Architecture
- フレームワーク機能の再発明（Form Wizard の無理な流用など）
- 「賢い」省略記法や一行に詰め込んだ処理

Django の強み（ORM、Form、`transaction.atomic`、`select_for_update`、messages）を正面から使う。

---

## 2. 推奨ディレクトリ構成

小〜中規模の業務アプリでは、**Django app を1つ（または業務境界ごとの少数）** にまとめ、app 内を責務パッケージで分割する。

```text
project-root/
├── config/                     # Django プロジェクト設定
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── app/                        # モノアプリ（業務の中心）
│   ├── models/                 # 永続化・状態遷移・DB制約
│   │   ├── application.py      # 例: 正式エンティティ
│   │   ├── draft.py            # 例: 編集中エンティティ
│   │   └── querysets.py        # 所有者スコープ・関連ロード
│   ├── services/               # ユースケース・トランザクション境界
│   ├── selectors/              # View 向け読取・404 境界
│   ├── forms/                  # 画面単位の入力検証
│   ├── views/                  # HTTP メソッド・Redirect・messages
│   ├── drafts/                 # 編集中データ型・変換・全体検証（必要な場合）
│   ├── rules/                  # Form/全体検証が共有する制約・コード
│   ├── errors/                 # DomainError（言語非依存）
│   ├── messages/               # 成功/失敗の表示文言
│   ├── presentation/           # ステップ定義・テンプレート初期値
│   ├── templates/app/
│   ├── static/app/
│   ├── tests/
│   ├── urls.py
│   └── admin.py
├── pyproject.toml
├── manage.py
└── docs/
    └── project-conventions.md  # 本ファイル（他案件へコピー可）
```

案件によっては `drafts/` がなくてもよい。  
「編集中の一時データ」や「複数画面にまたがる入力」がなければ、`forms` + `services` + `models` で足りる。

### 2.1 パッケージを増やす判断

| 症状 | 置き場所 |
|---|---|
| View に業務更新が混ざる | `services/` へ切り出す |
| 同じ読取クエリが View に散る | `selectors/` または `querysets.py` |
| 日本語文言が Service に直書き | `messages/` + `errors/` |
| Form と submit 検証で正規表現が二重 | `rules/` |
| テンプレート用の組み立てが View を肥大化 | `presentation/` |
| 画面間 JSON / コマンド変換が Service を汚染 | `drafts/` 相当の純粋モジュール |

最初から全部作る必要はない。**責務が混ざり始めたらパッケージを足す。**

---

## 3. 責務の固定表

レビュー時の判断基準として使う。

| 層 | やること | やってはいけないこと |
|---|---|---|
| `views/` | 認証、HTTP メソッド、Form 束縛、Redirect、Django messages、テンプレート選択 | 業務更新、ORM の更新手順、トランザクション設計 |
| `forms/` | 画面単位の型・必須・形式・同一画面内整合 | 画面横断の必須、正式保存、他画面未入力の強制 |
| `services/` | ユースケース、トランザクション境界、ORM 更新 | 日本語メッセージ、HTML 組み立て、HTTP ステータス |
| `models/` | 状態遷移、不変条件、フィールド、DB 制約 | 画面遷移、複数画面のオーケストレーション |
| `models/querysets.py` | 所有者スコープ、編集可能条件、関連のロード方針 | 状態変更、副作用 |
| `selectors/` | View 向け読取の名前付け、`get_object_or_404` 境界 | 書込み、業務判定の本体 |
| `rules/` | 共有正規表現、検証コード定数 | 文言、HTTP |
| `errors/` | 言語非依存の DomainError と構造化 params | 表示文言 |
| `messages/` | 成功文言、DomainError / ValidationCode の日本語化 | エラー発生条件 |
| `presentation/` | ステップ定義、テンプレ向け初期値 | DB 更新 |
| `drafts/` 等の純粋層 | 型、snapshot、Command 変換、全体検証 | HTTP、正式保存、表示文言 |

### 3.1 依存の向き

```text
views         → forms, selectors, services, presentation, messages, errors
services      → models, drafts, rules, errors, ORM
selectors     → models（QuerySet）
forms         → rules, messages（即時表示用の文言参照は可）
presentation  → models, drafts（読取・表示変換のみ）
drafts        → rules, errors, 必要なら models の列挙値のみ
models        → errors（状態メソッドが DomainError を投げる場合のみ）
errors / rules → 他層に依存しない
messages      → errors, rules（コード参照のみ）
```

原則:

- **外側（views / messages）が内側を知り、内側が外側を知らない**
- models が `errors` に依存するのは、状態遷移メソッドが HTTP 非依存の DomainError を投げるため。  
  models が `messages` や `views` を import してはいけない
- `drafts/` は「HTTP と正式保存を知らない」ことが本分。Model の Role 列挙など **永続化の語彙を参照するのは可**。  
  逆に drafts から Service / View を呼んではいけない

---

## 4. バリデーションは段階で分ける

1. **Form（画面）**  
   今の画面の入力だけを検証する。途中保存なら他画面の未入力は許容する。

2. **ユースケース検証（例: `drafts/validation.py`）**  
   確定や公開など「ここで初めて全体が揃う」操作の直前に、横断必須・重複・行 ID などを検証する。  
   **返すのは言語非依存コード**。

3. **Model.full_clean() と DB 制約**  
   正式保存直前と DB 自身の最終防衛。

共有できる形式制約（郵便番号など）は `rules/` に置き、Form と全体検証の両方から参照する。

```text
良い:
  Form ──参照──▶ rules.POSTAL_CODE_REGEX
  validate_* ──参照──▶ rules.POSTAL_CODE_REGEX / ValidationCode

悪い:
  Form に正規表現直書き
  Service に "郵便番号が正しくありません" を直書き
```

---

## 5. エラーとメッセージ

### 5.1 ドメインはコード、表示は messages

```python
# errors/domain.py — 言語非依存
@dataclass(eq=False)
class DomainError(Exception):
    code: str
    params: dict[str, Any] = field(default_factory=dict)


class DraftConflictError(DomainError):
    def __init__(self, *, expected_revision: int, current_revision: int | None) -> None:
        super().__init__(
            code="draft_conflict",
            params={
                "expected_revision": expected_revision,
                "current_revision": current_revision,
            },
        )
```

```python
# messages/application.py — 表示専用
ERROR_MESSAGES = {
    "draft_conflict": "別の画面で更新されています。最新の内容を読み直してください。",
}

def message_for_error(error: DomainError) -> str:
    return ERROR_MESSAGES.get(error.code, "処理を完了できませんでした。")
```

View の基本形:

```python
try:
    submit_draft(draft_id=draft_id, owner=request.user, expected_revision=revision)
except DomainError as error:
    messages.error(request, message_for_error(error))
    return redirect(...)
```

### 5.2 Django の ValidationError と名前がぶつかるとき

import alias でどちら側か明示する。

```python
from django.core.exceptions import ValidationError as DjangoValidationError
from app.errors import ValidationError
```

レビュー時に「どちらの ValidationError か」が分からない状態を作らない。

---

## 6. 読み取りと書き込み

### 6.1 QuerySet にスコープを置く

```python
class ApplicationQuerySet(models.QuerySet):
    def owned_by(self, user):
        """所有者で絞り込む。"""
        return self.filter(owner=user)

    def with_details(self):
        """一覧・編集開始で必要な関連をまとめて読む。"""
        return self.select_related("owner").prefetch_related("members", "attachments")

    def editable(self):
        """ロック済みを除く。"""
        return self.exclude(status=self.model.Status.LOCKED)
```

所有者条件を View や Service にバラ撒かない。`owned_by` のような名前で意図を固定する。

### 6.2 selector は View の読取窓口

```python
def get_draft_for_edit(*, draft_id: UUID, user: AbstractBaseUser) -> ApplicationDraft:
    """編集可能な Draft を取得する。見つからなければ 404。"""
    return get_object_or_404(
        ApplicationDraft.objects.owned_by(user).editing(),
        pk=draft_id,
    )
```

- 404 にする境界は selector
- 業務上「存在はするが編集不可」は DomainError（Service 側）

### 6.3 例外の使い分け

| 状況 | 投げ方 | 受け止め |
|---|---|---|
| URL 上の ID が、権限付きスコープに存在しない | selector の `get_object_or_404` | Django が 404 |
| 編集中でない・ロック済み・revision 競合など業務ルール違反 | Service が `DomainError` | View が messages + Redirect |
| 入力の全体不整合（確定時） | `ValidationError`（DomainError 派生、code のみ） | View が localize して再表示 |
| Service 内の `.get()` が想定外に欠落 | `DoesNotExist`（通常は selector 済みで起きない） | バグとして 500。業務メッセージにしない |

View で selector 済みでも、Service は **所有者スコープ付きで dual に読む**（権限の最終防衛）。  
Service を HTTP なしで呼ぶテスト・管理コマンドでも同じ安全網が効く。

### 6.4 Service が更新とトランザクションを持つ

```python
def update_basic(
    *,
    draft_id: UUID,
    owner: AbstractBaseUser,
    expected_revision: int,
    payload: BasicPayload,
) -> ApplicationDraft:
    """basic セクションを payload で置き換える。"""

    def mutate(data: dict) -> None:
        data["basic"] = {"title": payload.title, "purpose": payload.purpose}

    return update_draft_data(
        draft_id=draft_id,
        owner=owner,
        expected_revision=expected_revision,
        mutate=mutate,
    )
```

- 関数はユースケース名（`create_draft`, `submit_draft`, `update_address`）
- 引数は **キーワード専用**（`*` 以降）
- 画面や HTTP を知らない

Repository は作らない。必要ななら QuerySet メソッドと selector で足りる。

---

## 7. View の型

### 7.1 薄い View

```python
@login_required
@require_POST
def draft_create(request: HttpRequest) -> HttpResponse:
    draft = create_draft(owner=request.user)
    messages.success(request, SUCCESS_MESSAGES["draft_created"])
    return redirect("app:draft-basic", draft_id=draft.id)
```

### 7.2 繰り返しは helpers に

ステップ更新のような同型処理は `views/helpers.py` に寄せ、各 View は「どの Form / どの Service を呼ぶか」だけ残す。

### 7.3 POST-Redirect-GET

更新系 POST の成功後は必ず Redirect する。  
再送信防止と「GET は表示、POST は更新」の境界を守る。

```text
GET  表示
POST 検証 → Service → Redirect
GET  次画面（または同画面）表示
```

---

## 8. パッケージの公開 API

各パッケージの `__init__.py` で公開面を明示する。

```python
# services/__init__.py
from .basic import update_basic
from .submission import submit_draft
# ...

__all__ = [
    "submit_draft",
    "update_basic",
    # ...
]
```

呼び出し側はできるだけパッケージ経由にする。

```python
# 良い
from app.services import update_basic
from app.errors import DomainError

# 避けたい（内部ファイルへの深い依存が広がる）
from app.services.basic import update_basic
```

内部ファイル分割は自由。外からの入口を `__init__` に集約すると、リネームや分割が安全になる。

**例外:** パッケージ内の兄弟モジュール同士（例: `services/basic.py` → `services/draft_updater.py`）は相対 import でよい。  
公開したい型（TypedDict や Payload）が増えたら `__init__.py` の `__all__` に足し、外からはパッケージ経由にする。

---

## 9. 型とデータのかたち

### 9.1 構造化データは TypedDict / dataclass

```python
class BasicSection(TypedDict):
    title: str
    purpose: str


@dataclass(frozen=True, slots=True)
class BasicPayload:
    title: str
    purpose: str
```

| 用途 | 推奨 |
|---|---|
| JSON / dict の形 | `TypedDict` |
| 境界をまたぐ入力（Form → Service） | `frozen` dataclass（Payload） |
| 確定時の不変コマンド | `frozen` dataclass（Command） |
| ドメイン例外 | dataclass 継承の Exception |

「dict をそのまま Service に渡す」は境界が曖昧になりやすい。Payload に一度載せると、View と Service の契約がレビューしやすい。

### 9.2 行の同一性

動的な複数行（担当者・明細など）では:

| 識別子 | 意味 |
|---|---|
| `row_id` | 画面上の行の同一性（UUID） |
| `source_id` | 正式レコードとの対応（なければ null） |
| formset の index | **HTTP フィールド名の復元だけ**に使う。業務 ID にしない |

並べ替え・途中削除があっても index を業務キーにしない。

---

## 10. Python スタイル: 可読性優先

AI は短く書ける。人間のレビューと半年後の自分が読むための規約。

### 10.1 名前は省略しない

| 避ける | 推奨 |
|---|---|
| `u`, `usr` | `user`, `owner` |
| `app`, `appl` | `application` |
| `d`, `dr` | `draft` |
| `req`, `res` | `request`, `response` |
| `cfg`, `opts` | `config`, `options` |
| `tmp`, `buf` | 用途が分かる名前（`new_data`, `existing_members`） |
| `fn`, `cb` | `mutate`, `update`, `on_commit` など役割名 |
| `e`（except） | `error` |
| `i`, `j`（業務ループ） | `member`, `attachment`, `index`（単なる連番なら index 可） |

Django で定着している略語（`pk`, `id`, `url`）はそのままでよい。  
**業務ドメイン語を3文字に削らない。**

### 10.2 引数はキーワード専用を基本にする

```python
# 良い — 呼び出し側が自己説明的
create_draft(owner=request.user, application_id=application_id)
update_basic(
    draft_id=draft.id,
    owner=request.user,
    expected_revision=revision,
    payload=payload,
)

# 悪い — 位置引数の意味が呼び出し側で消える
create_draft(request.user, application_id)
```

公開関数は `def name(*, ...)` を原則とする。

**例外（位置引数でよいもの）:**

| 種類 | 例 | 理由 |
|---|---|---|
| Django View | `def basic_edit(request, draft_id)` | フレームワークの呼び出し規約 |
| 単一の自明レシーバ | `def member_initial(draft)` | レシーバ的な第1引数で誤解が起きにくい |
| モデルメソッド | `def submit(self, *, submitted_at)` | `self` は位置。追加引数はキーワード専用 |

「引数が2つ以上あり、どれが何かを呼び出し側で読み取れない」場合は必ずキーワード専用にする。

### 10.3 戻り値と型注釈を省略しない

```python
def get_draft_for_edit(*, draft_id: UUID, user: AbstractBaseUser) -> ApplicationDraft:
    ...
```

- 公開関数には引数型と戻り値型を付ける
- `dict` の中身が契約なら TypedDict かコメントで形を示す
- `Any` はファイル I/O など本当に必要なところに限定する

### 10.4 制御フローを素直に書く

```python
# 良い — 早期 return でネストを浅く
if draft.status != ApplicationDraft.Status.EDITING:
    raise DraftNotEditableError(draft_id=draft_id)

# 避けたい — 条件の否定と深いネスト
if not (draft.status != ...):  # 二重否定
    ...
```

- 1 関数 1 目的。長くなったら「保存」「検証」「同期」でプライベート関数へ
- リスト内包は **1 段まで**。フィルタと変換が両方重いなら普通の for
- セイウチ演算子 `:=` は、可読性が明らかに上がる場所以外では使わない
- 三項演算子は短い代入だけ。分岐が業務意味を持つなら if 文

### 10.5 「賢さ」より「追跡しやすさ」

```python
# 避けたい — 何をしているか追いにくい
draft.data["members"] = [
    {**m, "email": m["email"].lower()}
    for m in draft.data.get("members", [])
    if not m.get("delete") and m.get("email")
]

# 良い — 手順がレビューできる
active_members = []
for member in draft.data.get("members", []):
    if member.get("delete"):
        continue
    email = member.get("email")
    if not email:
        continue
    active_members.append({**member, "email": email.lower()})
draft.data["members"] = active_members
```

DRY は「同じ意図の重複」を減らすためであり、「似た文字の boilerplate を消す」ためではない。  
**呼び出し側が読めなくなる共通化はしない。**

### 10.6 コメントと docstring

- 公開関数には **何をするか** を一文で
- 「なぜこうしているか」が非自明なときだけコメント
- コードを言い換えるだけのコメントは書かない

```python
def update_draft_data(...) -> ApplicationDraft:
    """mutate で data を書き換え、revision 一致時だけ CAS 更新する。"""
```

```python
# 一意制約を一時回避するための position 退避先。
TEMPORARY_POSITION_BASE = 100_000
```

### 10.7 モジュール分割の目安

| 目安 | 行動 |
|---|---|
| ファイルが 200〜300 行を超え、複数関心が混在 | ファイル分割を検討 |
| 関数が画面スクロールを超える | プライベート関数へ分解 |
| テスト名で「何を守るか」が言えない | 仕様が曖昧。コードより仕様を先に直す |

1 ファイル 1 クラスに固執しない。**関心のまとまり**で切る。

### 10.8 テストも読み物として書く

```python
def test_update_rejects_stale_revision(...):
    """古い revision での更新は DraftConflictError になる。"""
    ...
```

- テスト名は仕様を述べる（`test_1` や `test_update` は不可）
- factory / builder で「完全な正当データ」を組み立て、ケースごとに崩す
- アサーションは「守るべき業務結果」を明示（副作用の細部だけを見ない）

---

## 11. AI に実装させるときのプロンプト指針

人間がレビューする前提で、AI への指示に次を含めるとブレにくい。

1. **層の表を渡す**（本ドキュメント §3）
2. **「View に業務更新を書かない」「Service に日本語を書かない」を明記**
3. **公開関数はキーワード専用引数・型注釈・docstring**
4. **変数名は省略しない。業務語をフルスペルで**
5. **新規ファイルを足す前に、既存パッケージのどれに属するかを言わせる**
6. **変更後に「持たない責務」を侵していないか自己チェックさせる**

レビュー観点（人間用チェックリスト）:

- [ ] View が ORM の `update` / `create` / `transaction.atomic` を直接使っていないか
- [ ] Service が `messages.*` や HTML / Redirect を知らないか
- [ ] エラーが日本語ベタ書きではなく code + messages か
- [ ] Form の即時文言以外で、ドメイン層が日本語を持っていないか
- [ ] 所有者スコープが QuerySet / selector に寄っているか
- [ ] 404（selector）と業務エラー（DomainError）が混同されていないか
- [ ] 名前が省略・1 文字変数だらけになっていないか
- [ ] 位置引数の羅列で呼び出し意図が消えていないか
- [ ] 新規ファイルが既存パッケージの責務に収まるか（勝手な `utils.py` 肥大化がないか）
- [ ] テストが仕様を読める名前になっているか

---

## 12. ツール設定の最小セット

`pyproject.toml` の例:

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "Django>=5.2,<6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3,<9.0",
    "pytest-django>=4.9,<5.0",
    "ruff>=0.9,<1.0",
]

[tool.uv]
package = false   # Django プロジェクト配布しない場合

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py"]
testpaths = ["app/tests"]
addopts = "-ra --strict-markers"

[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "DJ"]
```

検証コマンド:

```bash
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest
```

Ruff はフォーマットと低レベル欠陥用。  
**層の責務違反や命名の省略は Ruff では防げない。** そこは本規約とレビューで担保する。

---

## 13. 他プロジェクトへの適用手順

### 13.1 ほぼそのまま持っていく核

- 責務表（§3）と依存の向き
- `errors/` + `messages/` の分離
- `rules/` による共有制約
- `selectors/` の 404 境界、`querysets` の `owned_by`
- Service のキーワード専用 API と薄い View
- 3 段バリデーション
- `__init__.py` 公開 API
- 可読性優先の Python スタイル（§10）

### 13.2 案件ごとに作り直す部分

- models のフィールドと状態機械
- forms と templates
- services のユースケース関数
- drafts / schema / validation の中身（必要な場合）
- messages の文言
- presentation のステップ定義

### 13.3 適用の順序（新規案件）

1. `config/` + 空の `app/` + `pyproject.toml` を用意する
2. `models/` と `querysets.py` で永続化の芯を置く
3. `errors/` と `messages/` の骨格だけ先に作る
4. 最初のユースケースを `services/` + `views/` + `forms/` で縦一本当てる
5. 読取が重複したら `selectors/`、共有制約が出たら `rules/`
6. テストをユースケース単位で足す
7. 画面や項目が増えても **層の境界は変えずファイルだけ増やす**

---

## 14. よくある逸脱と戻し方

| 逸脱 | 症状 | 戻し方 |
|---|---|---|
| Fat View | View に `transaction.atomic` や複数 model 更新 | Service へ移す |
| Fat Model | Model メソッドが複数画面の流れを知っている | Service へ。Model は状態遷移と不変条件だけ |
| 文言のドメイン汚染 | Service が日本語文字列を raise / return | DomainError code + messages |
| 隠れ 404 | Service が `get_object_or_404` | 読取は selector、業務不可は DomainError |
| 偽 Repository | `save(entity)` だけのラッパ | 削除して ORM を Service から直接使う |
| 省略名の蔓延 | `upd()`, `u`, `d2` | フルスペルへリネーム。AI 出力はここを重点レビュー |
| 過度な共通化 | 汎用 `handle_step` が全画面の特殊事情を if 分岐 | 画面固有は各 View/Service に戻し、本当に同じ部分だけ helper に |

---

## 15. このサンプル固有だが再利用価値の高いパターン

申請ドラフト用途で実装しているが、他ドメインでも転用しやすいもの。

| パターン | 要点 |
|---|---|
| 編集中の唯一の正 | 途中入力を正式モデルに混ぜない。正式保存は確定トランザクションだけ |
| 楽観ロック（revision） | 複数タブ・複数画面の lost update を CAS で検出 |
| schema_version | JSON 進化時の移行フックを先に用意 |
| frozen Command | 検証済み入力を不変オブジェクトにしてから正式保存 |
| 添付の一時アップロード | バイナリを JSON に入れず、ストレージキーとメタだけを持つ |

必須ではない。要件が「複数画面の途中保存」「同時編集」「未完成データの隔離」を含むときに採用する。

---

## 16. 一文まとめ

> **Django の境界を尊重し、HTTP・検証・ユースケース・永続化・文言を分け、Python は省略せず人間が追えるように書く。**  
> AI は層の表に沿ってファイルを増やし、人間は責務違反と命名をレビューする。

本ファイルはプロジェクト間でコピーしてよい。  
案件固有のドメインルールは README や `docs/domain.md` に分け、この規約は「骨格」に留める。

---

## 付録. この規約自体の自己レビュー所見

文書初版を、サンプル実装と突き合わせて見直したときの結論（維持の指針）。

| 判定 | 項目 | 内容 |
|---|---|---|
| 良い | 責務表と「持たない責務」 | レビューの共通言語になる。最重要部分 |
| 良い | errors / messages 分離 | 実装と一致し、多言語化や文言変更に強い |
| 良い | 可読性 §10 | AI 向けに「省略するな」を明示している点が実務的 |
| 注意 | README との二重管理 | ドメイン手順は README、骨格は本ファイル。同じ表を両方に長く書かない |
| 注意 | サンプルは理想の上限ではない | View の URL 引数型、selector の戻り値型など、規約より緩い箇所が残りうる。規約側を正とする |
| 修正済 | models 無依存の言い切り | 状態メソッドからの DomainError は許可、と明記した |
| 修正済 | キーワード専用の例外 | View / `self` / 自明レシーバを例外として書いた |
| 修正済 | 404 と DomainError | 使い分け表を §6.3 に追加した |
| 残課題 | 機械チェックが弱い | Ruff では層違反を検出できない。将来 import-linter 等は任意 |
| 残課題 | API / 非同期 | 本規約は MPA 前提。JSON API では messages の代わりに error code をそのまま返す形へ読み替える |

他案件へ持ち出すときは、まず冒頭の **5分チェックリスト** と **§3 責務表** だけをチーム合意にし、残りは必要になった節から採用すると負担が少ない。
