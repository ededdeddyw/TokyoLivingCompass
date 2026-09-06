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
- 12駅のシードデータ（日本語・英語）
- スキーマ定義とデータ検証
- 設計ドキュメント一式

> **重要: 現在の駅データは全て開発用の推定値（`dataQuality: "seed"`）であり、出典に基づく確定値ではない。**
> 家賃・所要時間・スコア・在住者コメントのいずれも、公開前に実データへ差し替える必要がある。
> seed のあいだは駅ページが `noindex` になり、sitemap にも載らないよう実装してある。
> 次にやることは [docs/06-roadmap.md](./docs/06-roadmap.md) の Phase 1。

---

## セットアップ

```bash
npm install
npm run dev          # http://localhost:3000
```

```bash
npm run validate:data   # 全駅データのスキーマ・整合性検証
npm run typecheck       # 型検査
npm run build           # 本番ビルド（全駅ページの静的生成）
```

---

## 主な画面

| URL | 内容 |
|---|---|
| `/ja` `/en` | トップ |
| `/{locale}/stations` | 駅一覧。`?view=family` などで評価の視点を切り替えるとランキングが変わる |
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

---

## データを足すには

1. `data/stations/{slug}.json` に駅マスタ（言語非依存）を作る。
2. `data/content/ja/{slug}.json` と `data/content/en/{slug}.json` に散文を作る。
3. `npm run validate:data` を通す。

そのロケールの散文がない駅は、そのロケールではページを生成しない
（日本語にフォールバックしない。[docs/04-i18n.md](./docs/04-i18n.md) §5）。

スキーマの正は [`src/lib/schema.ts`](./src/lib/schema.ts)。

---

## 技術構成

Next.js (App Router) / TypeScript / Tailwind CSS / Zod。
詳細と設計上の約束事は [docs/07-architecture.md](./docs/07-architecture.md)。
