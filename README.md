# Tokyo Living Compass

> **東京で、あなたに一番合う街を見つける。**
> Find the Tokyo neighborhood that fits you.

東京の駅ごとの住みやすさ・家賃・通勤・生活環境を多言語で提供し、
「東京でどこに住むべきか」を決めるための意思決定エンジン。

物件を探す**前に**、住む街を決めるためのサービス。物件検索そのものは行わない。

---

## 現在の状態

Phase 0（土台）が完了。動く形で以下が揃っている。

- 駅ページ / 駅一覧 / 駅比較 / 勤務先起点の逆引き検索 / 重みプリセット
- **全443駅 / 62路線**（都営・東京メトロ・JR山手/中央/中央総武・23区を通る私鉄）
- **全443駅の所要時間**（7オフィス街、計算値。既知18区間との誤差は平均+0.8分）
- **全443駅の `commute` / `transitConvenience` スコア**
- 12駅の詳細シードデータ（日本語・英語）

方針として **443駅すべてを詳細データにする**。データは層ごとに順に埋めていく設計で、
`npm run validate:data` が毎回、層別の充足率を表示する。計画は
[docs/11-all-stations-plan.md](./docs/11-all-stations-plan.md)。
- スキーマ定義とデータ検証
- 設計ドキュメント一式

> **重要: 現在の駅データは全て開発用の推定値（`dataQuality: "seed"`）であり、出典に基づく確定値ではない。**
> 家賃・所要時間・スコア・在住者コメントのいずれも、公開前に実データへ差し替える必要がある。
> seed のあいだは駅ページが `noindex` になり、sitemap にも載らないよう実装してある。
> 次にやることは [docs/06-roadmap.md](./docs/06-roadmap.md) の Phase 1。
> 家賃の出典は調査・決定済み（[docs/08-data-sources-rent.md](./docs/08-data-sources-rent.md)）。
> 出典を記録する `sources.rent` と駅ページでの出典表示は実装済みで、
> 出典のないデータは `reviewed` に昇格できないようビルドで縛ってある。

---

## セットアップ

```bash
npm install
npm run dev          # http://localhost:3000
```

```bash
npm run validate:data   # 全駅データのスキーマ・整合性検証
# データ生成（いずれも標準ライブラリのみで動く）
python3 scripts/build-roster.py     # 全443駅と路線マスタ
python3 scripts/build-commutes.py   # 所要時間（443駅 × 7オフィス街）
python3 scripts/build-scores.py     # 計算で出せるスコア軸
npm run typecheck       # 型検査
npm run build           # 本番ビルド（全駅ページの静的生成）
```

---

## 主な画面

| URL | 内容 |
|---|---|
| `/ja` `/en` | トップ |
| `/{locale}/roster` | 掲載候補の全443駅。区ごとに並び、路線でしぼれる |
| `/{locale}/stations` | 詳細ページのある駅の一覧。`?view=family` などで評価の視点を切り替えるとランキングが変わる |
| `/{locale}/stations/{slug}` | 駅ページ。16軸スコア、家賃、通勤、在住者コメント |
| `/{locale}/compare/{a}-vs-{b}` | 駅比較 |
| `/{locale}/work/{office}` | 勤務先起点の逆引き検索。条件は全て URL クエリに載る |

例:

- `/ja/stations?view=quiet`
- `/ja/stations/kiyosumi-shirakawa`
- `/ja/compare/koenji-vs-higashi-nakano`
- `/en/work/toranomon?rentType=oneLDK&maxRent=170000&maxMinutes=30&view=quiet`

---

## ドキュメント

| ファイル | 内容 |
|---|---|
| [docs/00-concept.md](./docs/00-concept.md) | 事業構想（原文） |
| [docs/01-requirements.md](./docs/01-requirements.md) | 要件定義 / MVP スコープ |
| [docs/02-data-model.md](./docs/02-data-model.md) | データモデル |
| [docs/03-scoring.md](./docs/03-scoring.md) | スコア設計（16軸、重み、適合度） |
| [docs/04-i18n.md](./docs/04-i18n.md) | 多言語方針 |
| [docs/05-seo.md](./docs/05-seo.md) | SEO 設計 |
| [docs/06-roadmap.md](./docs/06-roadmap.md) | ロードマップ |
| [docs/07-architecture.md](./docs/07-architecture.md) | 技術構成 |
| [docs/08-data-sources-rent.md](./docs/08-data-sources-rent.md) | 家賃相場データの出典（調査と決定） |
| [docs/09-station-roster.md](./docs/09-station-roster.md) | 全443駅の洗い出し方と出典 |
| [docs/10-commute-estimation.md](./docs/10-commute-estimation.md) | 所要時間の計算方法と精度・限界 |
| [docs/11-all-stations-plan.md](./docs/11-all-stations-plan.md) | 443駅を全部埋めるための計画と数量 |

---

## データを足すには

駅名・所在区・路線・所要時間は全443駅ぶん揃っているので、足すのはその上の層。

1. `data/stations/{slug}.json` に家賃・スコア・施設を書く（**すべて任意**。分かったものから足せる）。
2. `data/content/ja/{slug}.json` と `data/content/en/{slug}.json` に散文を作る。
3. `npm run validate:data` を通す。充足率が上がる。

そのロケールの散文がない駅は、そのロケールではページを生成しない
（日本語にフォールバックしない。[docs/04-i18n.md](./docs/04-i18n.md) §5）。

スキーマの正は [`src/lib/schema.ts`](./src/lib/schema.ts)。

---

## 技術構成

Next.js (App Router) / TypeScript / Tailwind CSS / Zod。
詳細と設計上の約束事は [docs/07-architecture.md](./docs/07-architecture.md)。
