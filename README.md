# 副業現場ラボ（fukugyou-genba-lab.com）

> 副業の本当のところを、AI で集めて、たまに自分でも試して、リアルに伝える。
> 会社員のための副業情報キュレーション + 実体験ハイブリッドサイト。

## 概要

| 項目 | 値 |
|---|---|
| サイト名 | 副業現場ラボ |
| ドメイン | https://fukugyou-genba-lab.com |
| インフラ | Cloudflare Pages + Astro |
| 技術スタック | Astro 6.2・Tailwind CSS v4・MDX・Pagefind・TypeScript |
| ペンネーム | とっても！ハッピーマン |
| 量産計画 | 月 30 本（2 年で 720 本） |
| 収益目標 | 18 ヶ月後 月 ¥50,000 / 24 ヶ月後 月 ¥100,000 |

## カテゴリ（11 種）

| Slug | カテゴリ |
|---|---|
| `getting-started` | 始め方ガイド |
| `blog-writing` | ブログ・ライティング |
| `video-audio` | 動画・音声 |
| `creative` | クリエイティブ |
| `programming` | プログラミング・IT |
| `retail` | 物販 |
| `investment` | 投資・資産運用 |
| `skill-market` | スキルマーケット |
| `tools` | ツール比較 |
| `ai-side-job` | **AI × 副業**（差別化軸）|
| `real-experience` | **実体験ログ**（10% スパイス枠）|

## 副業特化コンポーネント

- `<JobCard>` 副業ジャンルカード
- `<RealExperienceLog>` 「💡 私もやってみた」スパイス枠
- `<RevenueRange>` 収益レンジバッジ（5 段階）
- `<ToolComparisonTable>` 副業ツール・ASP 比較表
- `<ExperiencerVoice>` 体験者の声引用ブロック（出典 URL 必須）
- `<ROICalculator>` 副業 ROI（時給換算）算出
- 汎用：`<Callout>` `<ProsCons>` `<ComparisonTable>` `<TableOfContents>` `<PRBadge>`

## ローカル開発

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # 本番ビルド + Pagefind 検索インデックス
npm run preview

# Cloudflare Pages デプロイ
npx wrangler pages deploy dist --project-name=fukugyou-genba-lab --branch=main
```

## 関連

- 企画書：`E:\5つの力+生きる\1. 稼ぐ\07. 副業・複業\06. アフィリエイトブログ\05_副業現場ラボ\★企画_副業現場ラボ.md`
- 記事マスターリスト 120 本：`E:\5つの力+生きる\1. 稼ぐ\07. 副業・複業\06. アフィリエイトブログ\05_副業現場ラボ\02_キーワード戦略\記事マスターリスト_2026-06_2026-09_120本.md`

---

🤖 Generated and maintained with Claude
