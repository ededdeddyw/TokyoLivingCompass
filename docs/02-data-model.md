# データモデル

このプロダクトの資産は記事ではなく**構造化された東京居住データ**である（構想 §14）。したがってデータ層はプレゼンテーション層から完全に独立させる。

---

## 1. 基本方針

1. **言語非依存の構造化データ**と**言語依存の散文**を物理的に分離する。
   - 構造化データ（スコア、家賃、所要時間、路線）は 1 駅につき 1 ファイル。
   - 散文（説明、在住者コメント、向いている人）は locale ごとに別ファイル。
   - これにより「駅を 1 つ増やす」と「言語を 1 つ増やす」が独立した作業になる。
2. **単一の正**は日本語のマスターデータ。他言語はそこから生成・ローカライズする。
3. スキーマは Zod で定義し、ビルド前に必ず検証する（`npm run validate:data`）。
4. 現在はファイルベース（JSON）。行数が増えたら同じスキーマのまま DB へ移行する。

---

## 2. ディレクトリ構成

```
data/
├── stations/           # 言語非依存のマスターデータ（1駅1ファイル）
│   ├── nishimagome.json
│   ├── koenji.json
│   └── ...
└── content/            # 言語依存の散文（locale/駅slug）
    ├── ja/
    │   ├── nishimagome.json
    │   └── ...
    └── en/
        ├── nishimagome.json
        └── ...
```

路線マスタとオフィス駅マスタは、現時点では独立したファイルにしていない。

- 路線は駅ごとに `lines` として埋め込む（1駅あたり1〜3件で、正規化する利点より参照コストの方が大きいため）。
- オフィス駅は `src/lib/schema.ts` の `OFFICE_HUBS`（識別子）と `src/lib/dictionaries.ts`（各言語の表示名）に持つ。

駅数が数百を超えて路線ページを作る段階になったら、路線を独立エンティティへ切り出す。

---

## 3. Station（駅マスタ）

`data/stations/{slug}.json`。型定義の正は [`src/lib/schema.ts`](../src/lib/schema.ts)。

| フィールド | 型 | 説明 |
|---|---|---|
| `slug` | string | URL 用 ID。ローマ字ケバブケース（例 `nishimagome`） |
| `nameJa` | string | 日本語駅名（例 `西馬込`） |
| `nameRomaji` | string | ローマ字表記（例 `Nishimagome`） |
| `ward` | string | 所在区の slug（例 `ota`） |
| `wardNameJa` | string | 所在区の日本語名（例 `大田区`） |
| `lines` | Line[] | 乗り入れ路線 |
| `hasFirstTrain` | boolean | 始発の有無 |
| `morningCrowding` | 1–5 | 朝ラッシュの混雑度（1 = 空いている、5 = 非常に混雑） |
| `rent` | Rent | 間取り別の家賃相場（円 / 月） |
| `commutes` | Commute[] | 主要オフィス駅への所要時間 |
| `scores` | Scores | 16軸スコア（0–100） |
| `facilities` | Facilities | 周辺施設の実名リスト |
| `similarStations` | string[] | 似ている駅の slug |
| `dataQuality` | `seed` \| `reviewed` \| `verified` | データの検証状態 |
| `lastReviewedAt` | string (YYYY-MM-DD) | 最終確認日 |

### Line

```jsonc
{ "nameJa": "都営浅草線", "nameEn": "Toei Asakusa Line", "operator": "toei" }
```

`operator` は `jr` / `tokyo-metro` / `toei` / `private` のいずれか。

### Rent（円 / 月）

```jsonc
{ "oneRoom": 82000, "oneK": 89000, "oneLDK": 148000, "twoLDK": 205000 }
```

間取りキーは `RENT_TYPES` として定数化し、逆引き検索の入力と 1:1 対応させる。

### Commute

```jsonc
{ "to": "toranomon", "minutes": 22, "transfers": 0 }
```

- `to` は `src/lib/schema.ts` の `OFFICE_HUBS` に定義されたオフィス駅 ID。
- `minutes` は朝ピーク時の実乗車時間 + 乗換時間（駅までの徒歩は含まない）。
- 全駅が全オフィス駅への値を持つ（欠損はスキーマ検証で弾く）。

### Facilities

```jsonc
{
  "supermarkets": ["ライフ", "サミット"],
  "commercial": ["アトレ大森"],
  "notes": "..."   // 任意
}
```

---

## 4. StationContent（散文）

`data/content/{locale}/{slug}.json`。

| フィールド | 型 | 説明 |
|---|---|---|
| `slug` | string | 対応する駅 slug |
| `locale` | string | ロケール |
| `name` | string | その言語での駅名表記 |
| `tagline` | string | 1行の要約 |
| `summary` | string | 2〜4文の概要 |
| `goodFor` | string[] | 向いている人 |
| `notFor` | string[] | 向かない人 |
| `residentComment` | string | 東京在住者コメント。**人間が書く。AI 生成禁止** |
| `authoredBy` | `human` \| `ai-localized` \| `seed-placeholder` | 生成方法の記録。`seed-placeholder` は公開不可 |

`residentComment` は本サービスの差別化の中核（構想 §4.2）なので、日本語は必ず人間が書き、他言語はその**翻訳ではなくローカライズ**とする。方針は [04-i18n.md](./04-i18n.md)。

---

## 5. 派生データ（ファイルに持たないもの）

以下は保存せず、実行時に計算する。二重管理を避けるため。

| 派生値 | 計算元 |
|---|---|
| 総合評価（0–10） | scores × 重みプリセット |
| ◎○△× のグレード | scores の閾値変換 |
| 適合度（%） | 逆引き検索の入力 × scores × rent × commutes |
| 駅ランキング | 上記の適合度のソート |

---

## 6. 将来: Tokyo Residential Graph

構想 §15 のグラフ構造は、現行スキーマの `lines` / `commutes` / `similarStations` / `ward` が既にエッジになっている。DB 移行時にこれらをそのままリレーションへ写す想定で、フィールド名は変えない。

ノード候補: 駅 / 路線 / 区 / オフィス街 / 施設。
エッジ候補: 乗り入れ、所要時間、隣接、類似、所在。
