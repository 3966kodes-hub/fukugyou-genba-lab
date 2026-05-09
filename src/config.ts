/**
 * サイト共通設定（タイトル・URL・メタ情報・カテゴリ定義）
 */

export const SITE = {
  name: '副業現場ラボ',
  shortName: '副業現場ラボ',
  url: 'https://fukugyou-genba-lab.com',
  description:
    '副業の本当のところを、AI で集めて、たまに自分でも試して、リアルに伝える。会社員のための副業情報キュレーション + 実体験ハイブリッドサイト。',
  author: '副業現場ラボ 編集部（とっても！ハッピーマン）',
  locale: 'ja-JP',
  ogImage: '/images/ogp/default.webp',
  twitter: '@fukugyou_genba', // 仮（取得後に更新）
} as const;

export type CategorySlug =
  | 'getting-started'
  | 'blog-writing'
  | 'video-audio'
  | 'creative'
  | 'programming'
  | 'retail'
  | 'investment'
  | 'skill-market'
  | 'tools'
  | 'ai-side-job'
  | 'real-experience';

export const CATEGORIES: Record<
  CategorySlug,
  { name: string; description: string; color: string; icon: string }
> = {
  'getting-started': {
    name: '始め方ガイド',
    description: '副業を始める前の基礎知識・規程確認・確定申告・税務の基本',
    color: 'blue',
    icon: 'lucide:flag',
  },
  'blog-writing': {
    name: 'ブログ・ライティング',
    description: 'アフィリエイトブログ・Webライター・Kindle 出版・note 有料記事',
    color: 'cyan',
    icon: 'lucide:pen-line',
  },
  'video-audio': {
    name: '動画・音声',
    description: 'YouTube・BGM 販売・効果音・音声配信（Voicy / stand.fm）・動画編集',
    color: 'violet',
    icon: 'lucide:video',
  },
  creative: {
    name: 'クリエイティブ',
    description: 'イラスト・LINE スタンプ・ハンドメイド・写真販売',
    color: 'pink',
    icon: 'lucide:palette',
  },
  programming: {
    name: 'プログラミング・IT',
    description: 'Web 制作・WordPress・モダンフロントエンド・クラウドソーシング',
    color: 'emerald',
    icon: 'lucide:code-2',
  },
  retail: {
    name: '物販',
    description: 'せどり・メルカリ・Amazon FBA・中国輸入・ハンドメイド販売',
    color: 'amber',
    icon: 'lucide:shopping-bag',
  },
  investment: {
    name: '投資・資産運用',
    description: '高配当株・株主優待・FX・不動産・REIT・暗号資産・自動売買 EA',
    color: 'red',
    icon: 'lucide:trending-up',
  },
  'skill-market': {
    name: 'スキルマーケット',
    description: 'ココナラ・タイムチケット・ストアカ・SKIMA',
    color: 'orange',
    icon: 'lucide:store',
  },
  tools: {
    name: 'ツール比較',
    description: 'サーバー・会計ソフト・時間管理・収支管理・名刺・バーチャルオフィス',
    color: 'slate',
    icon: 'lucide:wrench',
  },
  'ai-side-job': {
    name: 'AI × 副業',
    description: 'Claude / ChatGPT / Midjourney / Suno で副業を効率化・自動化',
    color: 'fuchsia',
    icon: 'lucide:sparkles',
  },
  'real-experience': {
    name: '私もやってみた（実体験ログ）',
    description: 'サイト主が実際に複数副業を運用するリアル体験談・ポートフォリオ実況',
    color: 'yellow',
    icon: 'lucide:notebook-pen',
  },
};

export const NAVIGATION = [
  { label: '始め方', href: '/category/getting-started/' },
  { label: 'ブログ', href: '/category/blog-writing/' },
  { label: '動画・音声', href: '/category/video-audio/' },
  { label: 'プログラミング', href: '/category/programming/' },
  { label: '投資', href: '/category/investment/' },
  { label: 'AI × 副業', href: '/category/ai-side-job/' },
  { label: '実体験ログ', href: '/category/real-experience/' },
] as const;

export const FOOTER_LINKS = [
  { label: 'About', href: '/about/' },
  { label: 'プライバシーポリシー', href: '/privacy/' },
  { label: '免責事項', href: '/disclaimer/' },
  { label: 'お問い合わせ', href: '/contact/' },
] as const;

export const HUB_PAGES = [
  { slug: 'beginner', label: '副業 始め方ハブ', href: '/hub/beginner/' },
  { slug: 'ai-side-job', label: 'AI × 副業ハブ', href: '/hub/ai-side-job/' },
  { slug: 'tax-guide', label: '確定申告・税務ハブ', href: '/hub/tax-guide/' },
  { slug: 'monthly-5man', label: '月 5 万円ロードマップ', href: '/hub/monthly-5man/' },
] as const;

/**
 * 副業の収益レンジ表記（RevenueRange コンポーネント用）
 */
export type RevenueRangeKey = 'sub-1man' | '1-5man' | '5-10man' | '10-30man' | '30man-plus';

export const REVENUE_RANGES: Record<
  RevenueRangeKey,
  { label: string; color: string }
> = {
  'sub-1man': { label: '〜1 万円', color: 'slate' },
  '1-5man': { label: '1〜5 万円', color: 'blue' },
  '5-10man': { label: '5〜10 万円', color: 'emerald' },
  '10-30man': { label: '10〜30 万円', color: 'amber' },
  '30man-plus': { label: '30 万円以上', color: 'red' },
};

/**
 * 副業の難易度（JobCard コンポーネント用）
 */
export type DifficultyKey = 'easy' | 'medium' | 'hard' | 'expert';

export const DIFFICULTIES: Record<
  DifficultyKey,
  { label: string; color: string; stars: number }
> = {
  easy: { label: '初心者向け', color: 'green', stars: 1 },
  medium: { label: '中級者向け', color: 'amber', stars: 2 },
  hard: { label: '上級者向け', color: 'orange', stars: 3 },
  expert: { label: 'エキスパート向け', color: 'red', stars: 4 },
};
