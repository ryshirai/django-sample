# SPA Aggregate State Design

## 目的

複数画面にまたがる大規模な入力業務をSPAで扱う際に、フロントエンドのstate、API、Django、DBの責務を整理する。

ここでは、DB上では多数のテーブルに正規化されている一方、業務上は「1件のまとまり」として編集・保存されるデータを対象とする。

サンプルでは `Meeting`（会議）を使うが、実際の業務名やテーブル構成に依存しない考え方とする。

---

## 基本方針

中心となる考え方は次のとおり。

> SPAはDBのテーブル構造を管理するのではなく、業務上の1まとまりであるAggregate全体を1つのstateとして保持する。

たとえばDB上では次のように分かれていてもよい。

```text
meeting
meeting_basic
meeting_attendee
attendee_affiliation
organization
organization_department
meeting_agenda
meeting_document
...
```

SPAからはこれをそのまま40個のテーブルとして扱わず、業務上理解しやすいツリーとして扱う。

```text
Meeting
├─ basic
├─ attendees[]
│  └─ affiliation?
│     └─ department?
├─ agendas[]
└─ documents[]
```

DBの正規化構造と、SPA/APIのデータ構造は一致させる必要はない。

```text
DB
正規化された永続化モデル

    ↓ hydrate

API
業務上意味のあるAggregate

    ↓

Svelte
現在編集中のAggregate state
```

保存時は逆方向に変換する。

```text
Svelte state
    ↓ snapshot
API payload
    ↓
Django Service
    ↓
複数テーブルへ同期
```

---

## Svelte側のstate

Svelte 5では、Aggregate Rootを1つの `$state` として持つ。

```ts
type Meeting = {
  id: number | null
  version: number | null

  basic: MeetingBasic
  attendees: Attendee[]
  agendas: Agenda[]
  documents: Document[]
}

type MeetingBasic = {
  title: string
  heldAt: string | null
}

type Attendee = {
  id: number | null
  name: string
  affiliation: Affiliation | null
}

type Affiliation = {
  id: number | null
  companyName: string
  department: Department | null
}

type Department = {
  id: number | null
  name: string
}

type Agenda = {
  id: number | null
  title: string
}

type Document = {
  id: number | null
  name: string
}
```

新規作成時のstate例。

```ts
let meeting = $state<Meeting>({
  id: null,
  version: null,
  basic: {
    title: '',
    heldAt: null,
  },
  attendees: [],
  agendas: [],
  documents: [],
})
```

重要なのは、画面ごとに別々の業務データstateを所有しないこと。

```text
NG

基本情報画面 state
参加者画面 state
所属画面 state
議題画面 state

各画面間で同期が必要になる
```

```text
推奨

              Meeting state
                   │
       ┌───────────┼───────────┐
       ↓           ↓           ↓
   基本情報画面   参加者画面   議題画面
       │           │           │
     basic     attendees[]   agendas[]
```

各画面はAggregate全体のうち、自分が担当する部分だけを編集する。

---

## 各画面からの更新

### 単純な入力値

単純な値はSvelteの `bind` で直接更新してよい。

```svelte
<script lang="ts">
  let { meeting } = $props()
</script>

<input bind:value={meeting.basic.title} />
<input bind:value={meeting.basic.heldAt} />
```

別画面から同じAggregateの別部分を編集する。

```svelte
{#each meeting.attendees as attendee}
  <input bind:value={attendee.name} />
{/each}
```

画面遷移をしてもデータを別stateへ移し替えない。

```text
画面A
meeting.basic.title を変更
        ↓
画面B
meeting.attendees を変更
        ↓
画面C
meeting.attendees[0].affiliation を変更
        ↓

すべて同じMeeting state上の変更
```

### 意味のある操作

配列の追加・削除やoptionalなネストの生成・削除など、意味のある操作は関数へ寄せる。

```ts
function addAttendee() {
  meeting.attendees.push({
    id: null,
    name: '',
    affiliation: null,
  })
}

function removeAttendee(index: number) {
  meeting.attendees.splice(index, 1)
}

function addAffiliation(attendee: Attendee) {
  attendee.affiliation = {
    id: null,
    companyName: '',
    department: null,
  }
}

function removeAffiliation(attendee: Attendee) {
  attendee.affiliation = null
}
```

すべての値をsetter経由にする必要はない。

```text
単純な入力値
→ bindで直接変更

配列の追加・削除
→ function

optionalなネストの生成・削除
→ function

複数項目を一括変更する業務操作
→ function
```

`setTitle()`、`setDate()`、`setAttendeeName()` のように単純入力までsetter化すると、Svelteの単純さを失いやすい。

---

## `null`、`[]`、IDの意味

APIとstateでは値の意味を明確に固定する。

### `[]`

`0..N` 件の関連が現在0件であることを表す。

```json
{
  "attendees": []
}
```

これは「参加者が0人」という意味であり、「未ロード」という意味では使わない。

### `null`

`0..1` 件の関連が現在存在しないことを表す。

```json
{
  "attendee": {
    "id": 10,
    "name": "田中",
    "affiliation": null
  }
}
```

これは「参加者は存在するが所属情報は存在しない」という意味になる。

### `id: null`

まだDB上に存在しない新規データを表す。

```json
{
  "id": null,
  "name": "佐藤"
}
```

### `id` あり

DB上の既存レコードを表す。

```json
{
  "id": 501,
  "name": "田中"
}
```

### フィールド欠落

全量同期を前提とする保存Payloadでは、原則として「未ロード」を表すためのフィールド欠落は作らない。

```text
null
= 0..1の関連が存在しない

[]
= 0..Nの関連が0件

id: null
= 新規データ

idあり
= 既存データ

missing
= 原則使わない
```

---

## 新規作成

初回アクセスは新規扱いとし、既存DBデータには触れない。

```text
空のMeeting stateを生成
    ↓
各画面で入力
    ↓
POST /api/meetings
    ↓
新規INSERT
    ↓
保存後のCanonical Response
    ↓
Svelte stateを同期
```

送信例。

```json
{
  "id": null,
  "version": null,
  "basic": {
    "title": "定例会議",
    "heldAt": null
  },
  "attendees": [
    {
      "id": null,
      "name": "田中",
      "affiliation": null
    }
  ],
  "agendas": [],
  "documents": []
}
```

保存後にはIDやversionが採番される。

```json
{
  "id": 100,
  "version": 1,
  "basic": {
    "title": "定例会議",
    "heldAt": null
  },
  "attendees": [
    {
      "id": 501,
      "name": "田中",
      "affiliation": null
    }
  ],
  "agendas": [],
  "documents": []
}
```

---

## 既存編集

既存編集はDBからAggregate全体を読み出してstateへhydrateしてから開始する。

```text
GET /api/meetings/100
    ↓
DBからAggregate全体をhydrate
    ↓
Svelte stateへ設定
    ↓
各画面で編集
    ↓
全量PUT
```

例。

```json
{
  "id": 100,
  "version": 7,
  "attendees": [
    {
      "id": 501,
      "name": "田中",
      "affiliation": {
        "id": 800,
        "companyName": "ABC株式会社",
        "department": {
          "id": 900,
          "name": "開発部"
        }
      }
    }
  ]
}
```

所属を削除する場合、フロント側では単純に `null` にする。

```ts
meeting.attendees[0].affiliation = null
```

送信Payloadは次のようになる。

```json
{
  "id": 100,
  "version": 7,
  "attendees": [
    {
      "id": 501,
      "name": "田中",
      "affiliation": null
    }
  ]
}
```

Django側では、既存の `affiliation id=800` がPayload上から消えたため論理削除する。

---

## 論理削除

SPAにDBの削除フラグを持ち込まない。

フロント側では「存在する / 存在しない」だけを表現する。

```text
SPA
存在する / 存在しない

        ↓

Django Service
差分を解釈

        ↓

DB
is_deleted=false / true
```

たとえば既存DBが次の場合。

```text
attendee id=501 active
attendee id=502 active
```

Payloadが次の状態になったとする。

```json
{
  "attendees": [
    {
      "id": 501,
      "name": "田中"
    }
  ]
}
```

バックエンドでは次のように扱う。

```text
501
→ UPDATE

502
→ Payloadに存在しないため論理削除
```

新規データが追加されていればINSERTする。

```json
{
  "id": null,
  "name": "佐藤"
}
```

同期ルールは概念的には次のとおり。

```text
idあり + Payloadに存在
→ UPDATE

idなし
→ INSERT

DBには存在 + Payloadには存在しない
→ logical DELETE
```

内容や名前が一致するからといって、削除済みレコードを推測で復活させない。同一性はIDで判断する。

---

## Django側の同期イメージ

サンプルコードとしては次のような責務になる。

```python
@transaction.atomic
def update_meeting(*, meeting_id: int, version: int, input_data: MeetingInput):
    meeting = (
        Meeting.objects
        .select_for_update()
        .get(id=meeting_id)
    )

    check_version(meeting, version)

    _update_basic(meeting, input_data.basic)
    _sync_attendees(meeting, input_data.attendees)
    _sync_agendas(meeting, input_data.agendas)
    _sync_documents(meeting, input_data.documents)

    meeting.version += 1
    meeting.save(update_fields=["version"])

    return hydrate_meeting(meeting)
```

子要素同期の概念例。

```python
def _sync_attendees(meeting, inputs):
    existing = get_active_attendees(meeting)

    incoming_ids = {
        item.id
        for item in inputs
        if item.id is not None
    }

    for attendee in existing:
        if attendee.id not in incoming_ids:
            logical_delete(attendee)

    for item in inputs:
        if item.id is None:
            create_attendee(meeting, item)
        else:
            update_attendee(meeting, item)
```

実装ではネストした `affiliation` や `department` なども、それぞれの業務ルールに従って同期する。

40テーブルすべてを1つの巨大な汎用同期関数に押し込まず、業務セクション単位のprivate関数へ分ける。

---

## versionによる競合検知

全量保存では、古いstateによる上書きを防ぐためversionを必須とする。

```text
GET
version = 7

    ↓

ユーザーが編集

    ↓

PUT
version = 7
```

DB側もversion 7なら保存できる。

```text
DB version = 7
Payload version = 7

→ 保存
→ version = 8
```

他ユーザーや別タブが先に更新していた場合。

```text
DB version = 8
Payload version = 7

→ 409 Conflict
```

これにより、全量Payloadが古い状態でDBを上書きすることを防止できる。

---

## 保存後はCanonical Responseで置き換える

保存APIは単純にRequestをechoするのではなく、保存後のDB状態から再構成したCanonicalなAggregateを返す。

Svelteでは保存前にsnapshotを取る。

```ts
const payload = $state.snapshot(meeting)
```

新規・既存でAPIを分ける。

```ts
const saved = meeting.id === null
  ? await createMeeting(payload)
  : await updateMeeting(payload)
```

返却されたstateで現在のstateを同期する。

```ts
meeting = saved
```

これにより、次のようなサーバ側で確定した値を確実にstateへ戻せる。

```text
採番されたID
version
server default
正規化された値
計算値
updated_at
その他サーバ側で確定する項目
```

たとえば送信時に新規参加者が次の状態でも、

```json
{
  "id": null,
  "name": "田中"
}
```

保存後には、

```json
{
  "id": 501,
  "name": "田中"
}
```

として返却される。

クライアント側で部分的なmergeを頑張るより、サーバが返した正規状態へ同期する方が単純で安全である。

---

## UI stateは分離する

Aggregate stateへ画面制御用のstateを混ぜない。

```ts
let meeting = $state<Meeting>(createEmptyMeeting())

let ui = $state({
  currentSection: 'basic',
  sidebarOpen: true,
  saving: false,
  showValidationErrors: false,
})
```

次のような項目はAPI Payloadへ含めない。

```text
currentSection
sidebarOpen
saving
modalOpen
accordionOpen
showValidationErrors
```

業務データとUI状態を明確に分離する。

---

## フロント側で差分管理を持たない

フロントで次のような差分stateを持つことは原則避ける。

```text
dirtyAttendees
deletedAttendees
newAttendees
updatedAttendees
```

SPAは「現在どうなっているか」という完全なAggregateを持つ。

```text
Frontend
現在の完全な状態を表現する

Backend
以前のDB状態とPayloadを比較して同期する
```

削除時も、フロント側では単純に配列から除去する。

```ts
meeting.attendees.splice(index, 1)
```

論理削除への変換はバックエンドの責務とする。

---

## APIの粒度

DBテーブル単位でAPIを作らない。

```text
避けたい例

POST /meeting-basic
POST /meeting-attendees
POST /meeting-agendas
POST /meeting-documents
...
```

業務上 `Meeting` が1つの保存単位なら、APIもAggregate単位にする。

```http
POST /api/meetings
GET  /api/meetings/{id}
PUT  /api/meetings/{id}
```

内部で多数テーブルへ保存されることは、API利用側には意識させない。

```text
API Aggregate != DB Table
```

---

## transaction境界

業務上1回の「保存」で成立する必要があるデータなら、DB更新もAggregate全体を1 transactionとする。

```text
Meeting全量保存
    ↓
transaction開始
    ↓
basic更新
attendee同期
affiliation同期
agenda同期
document同期
...
    ↓
version更新
    ↓
commit
```

途中の1テーブルで失敗した場合は全体をrollbackする。

多数テーブルが存在することを理由にtransactionを分割しない。transaction境界はテーブル数ではなく、業務上の整合性単位で判断する。

---

## バリデーション

フロントとバックエンドでは目的を分ける。

```text
Svelte
入力UXのためのvalidation
画面遷移可否
即時フィードバック

Django
保存可能かどうかの最終判定
業務ルール
整合性チェック
```

フロントのvalidationを業務ルールの唯一の正にしない。

---

## 推奨する全体フロー

### 新規

```text
createEmptyMeeting()
    ↓
Svelte Aggregate State
    ↓
各画面が担当部分を編集
    ↓
$state.snapshot()
    ↓
POST /api/meetings
    ↓
Django validation
    ↓
transaction
    ↓
複数テーブルへINSERT
    ↓
version付与
    ↓
DBからAggregateを再hydrate
    ↓
Canonical Response
    ↓
Svelte stateを置換
```

### 既存

```text
GET /api/meetings/{id}
    ↓
DBからAggregateをhydrate
    ↓
Svelte Aggregate State
    ↓
各画面が担当部分を編集
    ↓
$state.snapshot()
    ↓
PUT /api/meetings/{id}
    ↓
version確認
    ↓
transaction
    ↓
INSERT / UPDATE / logical DELETE
    ↓
version更新
    ↓
DBからAggregateを再hydrate
    ↓
Canonical Response
    ↓
Svelte stateを置換
```

---

## 設計上の感覚

この方式で最も重要なのは、DBのテーブル数に設計を引っ張られないこと。

```text
DB
40テーブルある

≠

SPA
40個のstateや40本の保存APIが必要
```

業務上1件として扱うものなら、SPAでは1つのAggregateとして持つ。

```text
1 Aggregate
1 root state
複数の画面 / section
1保存単位
1 transaction
1 canonical response
```

画面は「データの所有者」ではなく、Aggregateの一部分を編集するUIと考える。

```text
画面Aが所有するデータ
画面Bが所有するデータ
```

ではなく、

```text
Meetingがデータを所有する

画面AはMeeting.basicを編集する
画面BはMeeting.attendeesを編集する
画面CはMeeting.attendees[].affiliationを編集する
```

という関係にする。

この考え方にすると、多数テーブル・optionalな関連・深いネスト・複数画面という構造でも、フロント側は比較的単純なモデルで扱える。
