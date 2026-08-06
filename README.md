# Django 複数画面申請システム サンプル

Python 3.13 / Django 5.x を対象にした、MPA・モノアプリ構成の申請システムです。
クリーンアーキテクチャや Repository を持ち込まず、Django ORM、Form、Model、QuerySetを
そのまま活用しながら、HTTP・ユースケース・状態遷移・検索・表示変換の責務を分離しています。

すべての実装ファイルは省略のない独立したファイルです。新規申請、既存編集、画面間移動時の
Draft保存、担当者の動的追加・削除、添付の一時保存、確認、確定、Draft削除を実装しています。

## 起動

### Dev Container（推奨）

前提はDocker Desktop、VS Code、VS CodeのDev Containers拡張です。

1. VS Codeでこのフォルダを開く
2. コマンドパレットから `Dev Containers: Reopen in Container` を実行
3. 初回構築完了後、VS Codeのターミナルで次を実行

```bash
uv run python manage.py createsuperuser
uv run python manage.py runserver 0.0.0.0:8000
```

ブラウザで `http://127.0.0.1:8000/` を開きます。依存関係の同期とmigrationは
`postCreateCommand` で自動実行されます。ベースイメージはPython 3.13のmulti-platform imageなので、
Windows 11 ARM64のDocker Desktopでも同じ設定を利用できます。

テストと静的検査はコンテナ内で実行できます。

```bash
uv run pytest
uv run ruff check .
uv run python manage.py check
```

### ローカルで直接起動

```bash
uv sync --extra dev
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

このリポジトリは配布用PythonパッケージではなくDjangoプロジェクトなので、`tool.uv.package = false`
を設定しています。`uv sync` はプロジェクト自身をビルドせず、実行に必要な依存関係だけを導入します。

管理画面でログイン後、`http://127.0.0.1:8000/` を開きます。別の仮想環境ツールを使う場合は
`pip install -e '.[dev]'` でも構いません。

本番では最低限、`DJANGO_SECRET_KEY`、`DJANGO_DEBUG=false`、
`DJANGO_ALLOWED_HOSTS=example.com` を設定し、DBをPostgreSQLへ、ファイルストレージを
S3等へ変更してください。

## 設計の中心

### Draftが編集中の唯一の正

新規申請では空のJSON、既存編集では正式モデルのスナップショットからDraftを作ります。
スナップショット後の各GETはDraftだけを読み、正式モデルと表示内容を混ぜません。このため、
「ある項目はDraft、別の項目は正式データ」という二重の正が発生しません。

```text
新規: empty data ──> Draft ──> Command ──> Application
編集: Application ──> Draft ──> Command ──> Application update
                         ↑
                  編集中に読む唯一の正
```

`Application` に未完成状態はありません。未完成データをNULLだらけの正式テーブルへ保存せず、
正式データが作成・更新されるのは `submit_draft()` のトランザクション内だけです。

### 画面遷移と保存

各入力画面のステップボタンはリンクではなくsubmitボタンです。したがって、アプリ内の別画面へ
移動するときは必ず次の流れになります。

```text
GET Draft表示
  -> POST Form検証
  -> ServiceでDraft更新
  -> Redirect
  -> GET 次画面をDraftから表示
```

確認画面のステップ移動は確定を行いません。`action=submit` を送る「申請する」ボタンだけが
`submit_draft()` を呼びます。ブラウザを閉じる、URLを直接変更するなどPOSTを伴わない離脱では、
未送信のフォーム値は保存されません。`beforeunload` や非同期保存を入れないことで、必要最低限の
JavaScriptと明確なHTTP境界を維持しています。

### 楽観ロック

Draft更新は画面に埋め込んだ `revision` とDBの現在値を比較します。基本情報・住所・担当者は
次のcompare-and-swapを1 SQLで実行します。

```python
ApplicationDraft.objects.filter(
    pk=draft_id,
    revision=expected_revision,
    status="editing",
).update(data=new_data, revision=expected_revision + 1)
```

更新件数が0なら `DraftConflictError` です。添付更新はファイル行も同時に変更するため、
`transaction.atomic()` と `select_for_update()` の中でrevisionを比較します。確定も同じくDraftと
既存Applicationを行ロックします。

### JSONスキーマ

Draftの `data` は次の形です。`schema_version` により、将来の項目追加時にバージョン別変換を
追加できます。

```json
{
  "basic": {"title": "...", "purpose": "..."},
  "address": {
    "postal_code": "100-0001",
    "prefecture": "東京都",
    "city": "千代田区",
    "address_line": "千代田1-1"
  },
  "members": [
    {
      "row_id": "画面行のUUID",
      "source_id": "既存ApplicationMemberのUUIDまたはnull",
      "name": "...",
      "email": "...",
      "role": "owner"
    }
  ],
  "attachments": [
    {
      "row_id": "画面行のUUID",
      "source_id": "既存ApplicationAttachmentのUUIDまたはnull",
      "label": "...",
      "file_name": "original.pdf",
      "storage_name": "application-files/.../original.pdf",
      "draft_upload_id": "一時アップロード行のUUIDまたはnull"
    }
  ]
}
```

Django formsetの連番はHTTPフィールド名を復元するためだけに使います。業務上の行同一性は
`row_id`、正式データとの対応は `source_id` で判断します。並べ替えや途中削除をしてもindexを
識別子として扱いません。

### 添付ファイル

バイナリをJSONFieldへ入れず、`DraftUpload` がストレージ上の不変オブジェクトを一時参照します。
Draft JSONにはメタデータとストレージキーを保存します。確定時は正式な
`ApplicationAttachment` が同じオブジェクトを参照し、その後 `DraftUpload` 行だけを削除します。
Draftを破棄した場合は、`transaction.on_commit()` で未採用ファイルをストレージから削除します。

DBトランザクションはオブジェクトストレージまでロールバックできません。本番では、プロセス停止で
残った孤児ファイルを削除する定期ジョブ、ウイルススキャン、拡張子だけに依存しないMIME検査、
サイズ上限を追加してください。

## 責務

| 層 | 責務 | 持たない責務 |
|---|---|---|
| `views/` | HTTPメソッド、認証、Form束縛、Redirect、Django messages | 業務更新、ORM更新手順 |
| `forms/` | 画面単位の型・必須・形式・同一画面内検証 | 画面をまたぐ整合性、正式保存 |
| `services/` | 画面/業務単位のユースケース、トランザクション境界 | 日本語メッセージ、HTML、Repository抽象化 |
| `models/` | 状態遷移、不変条件、DB表現、DB制約 | 画面遷移、ユースケースのオーケストレーション |
| `models/querysets.py` | 所有者スコープ、編集可能検索、関連先のロード方針 | 状態変更 |
| `selectors/` | View向け読取。404は「不存在/所有者外」のみ | 書込み、編集可否判定 |
| `drafts/` | JSON型、snapshot、全体検証、Command・ステップ payload | HTTP、正式保存、表示文言 |
| `rules/` | Form と全体検証が共有する正規表現・検証コード | 文言、HTTP |
| `messages/` | 成功・DomainError・検証コードの表示文言 | エラー発生条件 |
| `errors/` | 言語非依存のDomainErrorコードと構造化パラメータ | 表示文言 |
| `presentation/` | ステップ定義、テンプレート向け初期値 | DB更新 |

ServiceはDjango ORMを直接使います。ORMを単に包むRepositoryは、QuerySetの表現力、
`select_for_update()`、`prefetch_related()`、`transaction.atomic()` を隠し、抽象化の維持コストを
増やすため採用していません。

## バリデーションの3段階

1. `forms/`: 現在画面の入力だけを検証します。途中保存なので、他画面の未入力は許容します。
2. `drafts/validation.py`: submit直前に全画面の必須項目、責任者、重複、行IDを検証します。
3. `Model.full_clean()` とDB制約: 正式保存の直前とDB自身で最終防衛します。
   `full_clean` の失敗も Django の表示文言ではなく `error.code` → `ValidationCode` にマップし、
   文言は `messages/` が解決します。

郵便番号形式などの共有制約は `rules/` に置き、Form と Draft 全体検証の両方から参照します。
全体検証と submit 時のドメイン検証は **言語非依存の `ValidationCode`** だけを
`app.errors.ValidationError` に載せます。View が `localize_validation_errors()` で
`messages/validation.py` の文言へ変換します。Form は即時表示のため messages を直接参照します。

Django自身のValidationErrorと名前が衝突する箇所ではimport aliasを使い、どちらのエラーかを
明示しています。

## 確定トランザクション

`submit_draft()` は次を単一の `transaction.atomic()` 内で行います。

1. 所有者で絞ったDraftを `select_for_update()` し、statusとrevisionを検証
2. Draft全体検証
3. Draftからimmutableな `ApplicationCommand` を生成
4. 既存編集ならApplicationを `select_for_update()` してロック状態を検証
5. Applicationを状態遷移させ、`full_clean()` 後に保存
6. `source_id` が対象Application配下か検証して担当者・添付を同期
7. DB制約でメール・表示順の一意性を保証
8. Draftを `submitted` にしてrevisionを増加

担当者や添付の入れ替え時には、一意制約との一時衝突を避けるため、既存行を安全な仮値・仮順序へ
移してから最終値を保存します。これにより `source_id` を保持したまま更新できます。

## DB制約

- Draftの `revision >= 1`、`schema_version >= 1`
- Application/Draftのstatus値
- 1ユーザー・1正式申請につき編集中Draftは1件
- 同じApplication内の担当者メールアドレスは一意
- 担当者と添付のpositionはApplication内で一意
- 外部キー削除方針: 正式ApplicationのownerとDraft元Applicationは `PROTECT`

SQLiteはローカル実行用です。本番のロック・同時実行テストはPostgreSQLでも実施してください。

## 代替案との比較

### 正式モデルへ逐次保存

単純ですが、未完成データを正式モデルが持ち、必須制約を弱める必要があります。キャンセル時の復元や
公開範囲の判定も複雑になるため不採用です。本構成では正式モデルは常に正式状態です。

### セッションへDraftを保存

DB不要で小規模なら手軽ですが、複数端末、長期保存、検索、容量、監査、同時更新に弱いため不採用です。

### 項目ごとに正規化したDraftモデル

DB制約や検索には強い一方、正式モデルとほぼ同じテーブル群を二重保守します。申請項目が頻繁に変わる
前提ではJSONFieldとschema_versionの方が変更局所性に優れます。Draft内容を横断検索・集計する要件が
強い場合は正規化Draftを選ぶ価値があります。

### Django Form Wizard

順序付きウィザードには適しますが、本要件は画面を自由に往来し、DB永続Draftを唯一の正として
同時更新も検出します。Wizardの順序・ストレージモデルに合わせるより、通常のView/Form/Serviceを
明示する方が読みやすいため不採用です。

### Repository / Clean Architecture

ORM非依存が契約上必要な場合には候補ですが、通常のDjango案件ではQuerySetとトランザクション機能を
再抽象化し、ファイル数と変換コードが増えます。このサンプルはDjangoの境界を尊重し、ユースケースは
小さなService、読取再利用はQuerySet/selectorへ置きます。

### 悲観ロックだけを使う

複数画面の入力中ずっとDBロックを保持することはできません。通常更新はrevisionによる楽観ロック、
ファイル行を伴う短い処理と確定処理だけ `select_for_update()` を使う組合せが適しています。

## ファイル一覧と役割

### プロジェクト

- `.devcontainer/devcontainer.json`: Python 3.13コンテナ、拡張機能、ポート、初期化処理
- `.devcontainer/Dockerfile`: Dev Containers公式Pythonイメージとuv
- `pyproject.toml`: Python/Django依存、pytest、Ruff設定
- `manage.py`: Django管理コマンドの入口
- `config/settings.py`: 開発可能な基本設定と環境変数の入口
- `config/urls.py`: admin、アプリURL、開発時media配信
- `config/asgi.py`, `config/wsgi.py`: デプロイ入口

### モノアプリ `app`

- `apps.py`: アプリ設定
- `admin.py`: 正式申請とDraftの運用確認画面
- `urls.py`: 一覧、Draft作成/削除、編集開始、各ステップ
- `models/application.py`: Application、担当者、正式添付、状態遷移
- `models/draft.py`: JSON Draft、一時添付、revision/schema/status制約
- `models/querysets.py`: 所有者・編集可能・関連取得（Application/Draft とも `owned_by`）
- `rules/codes.py`, `rules/fields.py`: 共有検証コードと郵便番号形式
- `errors/domain.py`: DomainError派生型
- `messages/application.py`: 成功文言とDomainErrorの表示変換
- `messages/validation.py`: ValidationCode の表示文言と localize 関数
- `drafts/types.py`: Draft JSON とステップ payload の型
- `drafts/schema.py`: 空Draft、snapshot、schema_version migrate フック
- `drafts/commands.py`: Draftから正式保存Commandへの純粋変換
- `drafts/validation.py`: Draft全体検証（コードのみ返す）
- `forms/application.py`: 画面単位Formと動的FormSet
- `services/draft_updater.py`: JSON compare-and-swap共通処理
- `services/draft_lifecycle.py`: Draft作成・削除
- `services/basic.py`, `address.py`, `members.py`, `attachments.py`: 画面単位更新
- `services/submission.py`: 全体検証と確定トランザクション
- `selectors/applications.py`, `selectors/drafts.py`: View向け読取（詳細は所有者のみ。編集可否は DomainError）
- `presentation/steps.py`: ステップ key / ラベル / ルート名の単一ソース
- `presentation/drafts.py`: Form初期値の表示変換
- `views/helpers.py`: ステップ更新の DomainError 処理と Redirect
- `views/applications.py`: 一覧・作成・編集開始・削除のHTTP処理
- `views/draft_steps.py`: 各画面のGET/POST/Redirect
- `templates/app/*.html`: MPA画面
- `templates/app/includes/step_navigation.html`: 保存を伴う共通ステップ操作
- `static/app/formset.js`: UUID行の追加・論理削除だけを行う最小JS
- `static/app/style.css`: 依存ライブラリなしの基本スタイル
- `migrations/0001_initial.py`: 全テーブル・制約の初期マイグレーション

各パッケージの `__init__.py` は公開APIを明示し、内部ファイル名への依存を減らしています。

### 他プロジェクトへ持ち回すとき

- AI 実装時の指示: [AGENTS.md](AGENTS.md)
- 人間向けの構成・規約の本体: [docs/project-conventions.md](docs/project-conventions.md)

他案件では `AGENTS.md` と `docs/project-conventions.md` をセットでコピーしてください。

ほぼそのままコピーできる核:

- `errors/`、`rules/` の仕組み、`services/draft_updater.py`
- Draft の revision / status / schema_version と `owned_by` QuerySet
- selector の 404 境界、3段バリデーション、`row_id` / `source_id`
- frozen Command とステップ payload、POST-Redirect-GET

案件ごとに差し替える部分:

- `drafts/schema`・`validation` の中身、`forms/`、各 step service
- `views/draft_steps` の画面、`templates/`、`messages` の文言

### テスト

- `tests/conftest.py`: ユーザーと一時MEDIA_ROOT fixture
- `tests/factories.py`: 正式申請と完全Draftデータのテストビルダー
- `tests/test_draft_lifecycle.py`: 新規/編集Draft作成、snapshot、ロック、削除
- `tests/test_draft_updates.py`: 更新、UUID行、revision競合とlost update防止
- `tests/test_submission.py`: 新規確定、既存更新、全体DomainError、添付移管
- `tests/test_views.py`: POST-Redirect-GETと画面更新

## 検証コマンド

```bash
ruff check .
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
```

作成時には Django 5.2.17 で `check`、マイグレーション差分なし、Ruff、12件のpytestを通しています。
実行コンテナにPython 3.13がなかったため検証ランタイムだけ3.12でしたが、プロジェクトの
`requires-python` とRuff targetは3.13に固定しています。使用しているDjango APIは5.2対応です。

## 実案件で追加するもの

- PostgreSQLでの `TransactionTestCase` を使った実並行トランザクション試験
- `migrate_draft_data` への版ごとの変換実装と、読取時の永続化・管理コマンド
- Draft有効期限、孤児ファイル、確定済みDraftの保管/削除ポリシー
- 添付の容量/MIME/マルウェア検査とprivate storageの署名URL
- 監査ログ（誰が、いつ、どのrevisionを確定したか）
- オブジェクト単位権限がowner以外にも必要ならPolicy関数または権限QuerySet
- 本番settings、PostgreSQL、キャッシュ、構造化ログ、エラー監視
- Application自体の外部更新も競合検出する場合はsource revisionをDraftへ保存

これらは要件・インフラ依存が強いためサンプルへ仮実装せず、拡張位置を明確にしています。
