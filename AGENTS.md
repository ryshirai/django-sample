# AGENTS.md

AI がこのリポジトリ（および同構成の Django 案件）で実装するときの指示。
人間がレビュー・保守する。**省略より可読性。** 詳細は `docs/project-conventions.md`。

## やってよい / やってはいけない

| する | しない |
|---|---|
| 既存パッケージの責務に沿ってファイルを増やす | 勝手な `utils.py` / Repository / Clean Architecture 層 |
| Service で更新と `transaction.atomic` | View で ORM 更新・トランザクション |
| selector / QuerySet で読取と 404 | Service で `get_object_or_404` |
| DomainError は言語非依存 code | Service に日本語文言 |
| Form は画面単位の検証のみ | Form で正式保存や画面横断必須の確定 |
| パッケージの `__init__` 経由で import | 他パッケージの内部ファイル直 import |
| 公開関数は `def name(*, ...)` + 型注釈 | 業務引数の位置引数羅列 |
| 業務名はフルスペル | `u`, `d`, `app`, `req`, `e` など省略名 |
| テスト名で仕様を述べる | `test_1`, `test_update` |

## 層と置き場所

```text
views/          HTTP・Form 束縛・Redirect・messages・テンプレート
forms/          画面の型・必須・形式・同一画面内整合
services/       ユースケース・TX・ORM 更新
models/         永続化・状態遷移・DB 制約
models/querysets.py  所有者スコープ・関連ロード（書込なし）
selectors/      View 向け読取・get_object_or_404
rules/          共有正規表現・ValidationCode
errors/         DomainError（文言なし）
messages/       成功・エラーの表示文言
presentation/   ステップ定義・テンプレ初期値
drafts/         型・snapshot・Command・全体検証（HTTP/正式保存なし）
```

新規コードを書く前に「どの層か」を決め、その層の禁止事項を侵さない。

責務が混ざり始めたときだけパッケージを足す:

| 症状 | 行き先 |
|---|---|
| View に業務更新 | `services/` |
| 読取クエリの重複 | `selectors/` または QuerySet |
| Service に日本語 | `errors/` + `messages/` |
| Form と全体検証で制約が二重 | `rules/` |
| テンプレ用組み立てが View を肥大化 | `presentation/` |
| JSON/Command 変換が Service を汚染 | `drafts/` 等 |

## 依存の向き

```text
views    → forms, selectors, services, presentation, messages, errors
services → models, drafts, rules, errors, ORM
selectors → models
forms    → rules, messages（即時表示のみ）
models   → errors のみ可（状態メソッド用）。messages/views 禁止
errors / rules → 他層に依存しない
```

## バリデーション

1. **forms/** … 今画面だけ。途中保存なら他画面未入力は許容
2. **全体検証**（例: `drafts/validation`）… 確定直前。返すのは code のみ
3. **Model.full_clean + DB 制約** … 正式保存の最終防衛

共有形式は `rules/` に置き、Form と全体検証の両方から参照する。

## エラー

- 存在しない（権限付きスコープ外）→ selector の 404
- 業務ルール違反（ロック・競合・編集不可）→ Service が DomainError
- 確定時の入力不整合 → DomainError 派生の ValidationError（code のみ）
- View が `message_for_error` / `localize_validation_errors` で文言化

```python
# Service
raise DraftConflictError(expected_revision=..., current_revision=...)

# View
except DomainError as error:
    messages.error(request, message_for_error(error))
    return redirect(...)
```

## Python

- 公開 API: キーワード専用引数、戻り値型、一文 docstring
- 例外: Django View の `(request, draft_id)`、`self`、自明な第1レシーバ
- 早期 return。ネストと二重否定を避ける
- リスト内包は1段まで。重い変換は for
- DRY は「同じ意図」だけ。呼び出しが読めなくなる共通化はしない
- `except ... as error`（`e` にしない）

名前:

| 避ける | 使う |
|---|---|
| `u`, `usr` | `user`, `owner` |
| `app`, `appl` | `application` |
| `d`, `dr` | `draft` |
| `req`, `res` | `request`, `response` |
| `e` | `error` |

`pk` / `id` / `url` は Django 慣例として可。

## データの渡し方

- Form → Service は dict 直渡しより **frozen Payload**
- JSON の形は TypedDict
- 動的行: `row_id`（画面行）、`source_id`（正式行）。formset index は HTTP 用のみ

## 実装手順

1. 変更対象の層を決める
2. 既存の同種ファイル（近い service / view / form）を読んで揃える
3. 公開面はパッケージ `__init__.py` の `__all__` に載せる
4. 更新系 POST は成功後 Redirect（POST-Redirect-GET）
5. 所有者条件は QuerySet（`owned_by` 等）。View/Service に `filter(owner=...)` をバラ撒かない
6. テストを仕様名で追加する
7. 通す: `uv run ruff check .` / `uv run pytest` / 必要なら `manage.py check`

## 完了前セルフチェック

- [ ] View に `.create` / `.update` / `transaction.atomic` が無い
- [ ] Service に `messages` / HTML / redirect が無い
- [ ] 日本語は `messages/`（Form 即時表示を除く）
- [ ] 業務名が省略されていない
- [ ] 公開関数がキーワード専用
- [ ] 404 と DomainError を混同していない
- [ ] テスト名で何を守るか分かる
