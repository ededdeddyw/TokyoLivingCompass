# 技術構成

---

## 1. スタック

| 層 | 採用 | 理由 |
|---|---|---|
| フレームワーク | Next.js (App Router) | 数万ページ規模の静的生成、locale ルーティング、動的ページの併用 |
| 言語 | TypeScript (strict) | データスキーマを型として全体で共有するため |
| スタイル | Tailwind CSS v4 | 設定ファイルなしで始められ、デザイン変更のコストが低い |
| データ検証 | Zod | スキーマとランタイム検証と型を一箇所で定義できる |
| データ保管 | リポジトリ内 JSON | 初期は Git 管理が最も扱いやすい。Phase 3 で DB 移行を判断 |

---

## 2. ディレクトリ

```
data/                     # ドメインデータ（下記 src/lib 以外から直接読まない）
docs/                     # 設計ドキュメント
scripts/
└── validate-data.ts      # 全データのスキーマ検証（CI / ビルド前）
src/
├── app/
│   ├── page.tsx                            # / → ロケール判定リダイレクト
│   └── [locale]/
│       ├── layout.tsx
│       ├── page.tsx                        # トップ
│       ├── stations/
│       │   ├── page.tsx                    # 駅一覧
│       │   └── [slug]/page.tsx             # 駅ページ
│       ├── compare/[pair]/page.tsx         # 駅比較
│       └── work/[office]/page.tsx          # 勤務先からの逆引き
├── components/           # 表示専用。データ取得はしない
└── lib/
    ├── schema.ts         # Zod スキーマと型（データ定義の単一の正）
    ├── stations.ts       # データ読み込み（ここだけが data/ を触る）
    ├── scoring.ts        # スコア計算・グレード変換・適合度
    ├── weights.ts        # 重みプリセット
    ├── i18n.ts           # ロケール定義
    └── dictionaries.ts   # UI 文言
```

---

## 3. 設計上の約束

1. **`data/` を読むのは `src/lib/stations.ts` だけ。** 他の場所から JSON を直接 import しない。DB 移行時にここだけ差し替えれば済むようにする。
2. **`src/lib/schema.ts` がデータ定義の単一の正。** ドキュメントと実装が食い違ったら実装が正。
3. **コンポーネントはデータを取りに行かない。** props で受け取る。サーバーコンポーネントでのデータ取得はページ側で行う。
4. **派生値は保存しない。** 総合評価・グレード・適合度は毎回計算する（[02-data-model.md](./02-data-model.md) §5）。
5. **スコア軸の追加はスキーマから。** `SCORE_AXES` を変えると型エラーで全ての追従漏れが検出される状態を保つ。

---

## 4. データ検証

```bash
npm run validate:data   # 全駅・全コンテンツのスキーマ検証
npm run typecheck       # 型検査
npm run build           # 本番ビルド（全駅ページの静的生成）
```

`validate:data` は以下を検証する。

- 駅マスタが Zod スキーマに適合するか
- ファイル名と `slug` が一致するか
- `similarStations` の参照先が実在するか
- 全駅が全オフィス駅への `commutes` を持つか
- コンテンツファイルの `slug` / `locale` がパスと一致するか

---

## 5. まだ決めていないこと

- ホスティング先（Vercel を想定しているが未確定）
- CI（GitHub Actions で `validate:data` と `build` を回す想定）
- 画像戦略（駅の写真をどう調達するか。権利の確認が必要）
- 解析ツール
