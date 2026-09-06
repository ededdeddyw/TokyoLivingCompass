import type { ActiveLocale } from "./i18n";
import type { RentMethod, RentType, ScoreAxis } from "./schema";
import type { Grade } from "./scoring";
import type { WeightPreset } from "./weights";

/** UI 文言。駅の散文（data/content）とは別管理（docs/04-i18n.md §6）。 */

export type Dictionary = {
  siteName: string;
  tagline: string;
  nav: { stations: string; find: string; compare: string };
  home: {
    lead: string;
    findCta: string;
    browseCta: string;
    featuredHeading: string;
  };
  station: {
    overall: string;
    rent: string;
    commute: string;
    lines: string;
    firstTrain: string;
    crowding: string;
    scores: string;
    facilities: string;
    supermarkets: string;
    commercial: string;
    goodFor: string;
    notFor: string;
    residentComment: string;
    similar: string;
    compareWith: string;
    perMonth: string;
    minutes: string;
    transfers: string;
    noTransfer: string;
    yes: string;
    no: string;
    backToList: string;
  };
  list: {
    heading: string;
    count: string;
    sortBy: string;
    perspective: string;
  };
  find: {
    heading: string;
    lead: string;
    office: string;
    maxRent: string;
    rentType: string;
    maxMinutes: string;
    maxTransfers: string;
    priority: string;
    submit: string;
    results: string;
    noResults: string;
    fit: string;
    why: string;
    weakness: string;
  };
  compare: {
    heading: string;
    winner: string;
    tie: string;
  };
  dataQuality: {
    seedWarning: string;
  };
  rentSource: {
    missing: string;
    askingCaveat: string;
    basis: Record<"asking" | "contracted" | "paid", string>;
    statistic: Record<"median" | "mean", string>;
    method: Record<RentMethod, string>;
  };
  axes: Record<ScoreAxis, string>;
  grades: Record<Grade, string>;
  rentTypes: Record<RentType, string>;
  presets: Record<WeightPreset, string>;
  offices: Record<string, string>;
  crowdingLevels: Record<1 | 2 | 3 | 4 | 5, string>;
};

const ja: Dictionary = {
  siteName: "Tokyo Living Compass",
  tagline: "東京で、あなたに一番合う街を見つける。",
  nav: { stations: "駅を見る", find: "駅を探す", compare: "駅を比べる" },
  home: {
    lead: "勤務先・予算・暮らし方から、東京のどこに住むべきかを決めるためのサービスです。物件を探す前に、街を決める。",
    findCta: "勤務先から駅を探す",
    browseCta: "駅一覧を見る",
    featuredHeading: "掲載中の駅",
  },
  station: {
    overall: "総合評価",
    rent: "家賃相場",
    commute: "都心アクセス",
    lines: "路線",
    firstTrain: "始発",
    crowding: "朝の混雑",
    scores: "駅スコア",
    facilities: "周辺施設",
    supermarkets: "スーパー",
    commercial: "商業施設",
    goodFor: "向いている人",
    notFor: "向かない人",
    residentComment: "東京在住者コメント",
    similar: "似ている駅",
    compareWith: "この駅と比べる",
    perMonth: "／月",
    minutes: "分",
    transfers: "乗換",
    noTransfer: "直通",
    yes: "あり",
    no: "なし",
    backToList: "駅一覧へ戻る",
  },
  list: {
    heading: "掲載駅一覧",
    count: "駅",
    sortBy: "並び替え",
    perspective: "評価の視点",
  },
  find: {
    heading: "勤務先から住む駅を探す",
    lead: "勤務先・家賃・通勤時間の条件を入れると、条件を満たす駅を適合度順に表示します。",
    office: "勤務先",
    maxRent: "家賃上限",
    rentType: "間取り",
    maxMinutes: "通勤時間の上限",
    maxTransfers: "乗換回数の上限",
    priority: "重視すること",
    submit: "駅を探す",
    results: "検索結果",
    noResults:
      "条件に合う駅が見つかりませんでした。家賃上限か通勤時間の条件をゆるめてみてください。",
    fit: "適合度",
    why: "推せる点",
    weakness: "弱点",
  },
  compare: {
    heading: "駅を比べる",
    winner: "優位",
    tie: "同等",
  },
  dataQuality: {
    seedWarning:
      "このページのデータは開発用の推定値です。出典に基づく確定値ではありません。",
  },
  rentSource: {
    missing: "家賃の出典は未設定です。",
    askingCaveat: "募集賃料のため、実際の成約額はこれより下がることがあります。",
    basis: {
      asking: "募集賃料",
      contracted: "成約賃料",
      paid: "支払家賃",
    },
    statistic: { median: "中央値", mean: "平均値" },
    method: {
      "vendor-station-area": "出典元が駅の範囲で集計した値",
      "radius-800m-weighted": "駅から半径800mの町丁を戸数で加重平均",
      manual: "手集計",
    },
  },
  axes: {
    rentValue: "家賃コスパ",
    commute: "都心アクセス",
    transitConvenience: "乗換利便性",
    shopping: "買い物",
    food: "飲食店",
    cafe: "カフェ",
    nightlife: "ナイトライフ",
    safety: "治安",
    quietness: "静かさ",
    family: "ファミリー適性",
    singleLife: "一人暮らし適性",
    internationalFriendliness: "外国人生活適性",
    style: "街のおしゃれさ",
    nature: "公園・自然",
    healthcare: "病院",
    fitness: "ジム",
  },
  grades: {
    excellent: "とても良い",
    good: "良い",
    fair: "普通",
    poor: "弱い",
  },
  rentTypes: {
    oneRoom: "1R",
    oneK: "1K",
    oneLDK: "1LDK",
    twoLDK: "2LDK",
  },
  presets: {
    balanced: "バランス",
    single: "一人暮らし",
    family: "ファミリー",
    quiet: "静かさ重視",
    value: "コスパ重視",
    international: "外国人向け",
  },
  offices: {
    shinjuku: "新宿",
    shibuya: "渋谷",
    tokyo: "東京",
    shinagawa: "品川",
    otemachi: "大手町",
    toranomon: "虎ノ門",
    roppongi: "六本木",
  },
  crowdingLevels: {
    1: "空いている",
    2: "やや空いている",
    3: "普通",
    4: "混雑",
    5: "非常に混雑",
  },
};

const en: Dictionary = {
  siteName: "Tokyo Living Compass",
  tagline: "Find the Tokyo neighborhood that fits you.",
  nav: { stations: "Stations", find: "Find your area", compare: "Compare" },
  home: {
    lead: "Decide where to live in Tokyo based on your office, budget and lifestyle. Choose the neighborhood before you start looking at apartments.",
    findCta: "Find areas near your office",
    browseCta: "Browse all stations",
    featuredHeading: "Stations covered",
  },
  station: {
    overall: "Overall",
    rent: "Typical rent",
    commute: "Commute",
    lines: "Lines",
    firstTrain: "Trains originate here",
    crowding: "Morning crowding",
    scores: "Station scores",
    facilities: "Nearby",
    supermarkets: "Supermarkets",
    commercial: "Shopping",
    goodFor: "Good for",
    notFor: "Not for",
    residentComment: "From someone who lives in Tokyo",
    similar: "Similar stations",
    compareWith: "Compare with this station",
    perMonth: "/month",
    minutes: "min",
    transfers: "transfers",
    noTransfer: "direct",
    yes: "Yes",
    no: "No",
    backToList: "Back to all stations",
  },
  list: {
    heading: "All stations",
    count: "stations",
    sortBy: "Sort by",
    perspective: "Ranked for",
  },
  find: {
    heading: "Find where to live, starting from your office",
    lead: "Enter your office, budget and commute limits. We rank the stations that actually meet them.",
    office: "Office",
    maxRent: "Maximum rent",
    rentType: "Layout",
    maxMinutes: "Maximum commute",
    maxTransfers: "Maximum transfers",
    priority: "What matters to you",
    submit: "Find stations",
    results: "Results",
    noResults:
      "No station meets these conditions. Try raising the rent limit or allowing a longer commute.",
    fit: "Fit",
    why: "Why it works",
    weakness: "Trade-offs",
  },
  compare: {
    heading: "Compare stations",
    winner: "Better",
    tie: "Even",
  },
  dataQuality: {
    seedWarning:
      "The data on this page is a development placeholder, not a sourced figure.",
  },
  rentSource: {
    missing: "No source recorded for these rent figures yet.",
    askingCaveat:
      "These are asking rents; the rent actually agreed is often lower.",
    basis: {
      asking: "Asking rent",
      contracted: "Contracted rent",
      paid: "Rent currently paid",
    },
    statistic: { median: "median", mean: "mean" },
    method: {
      "vendor-station-area": "Aggregated by the source over the station area",
      "radius-800m-weighted":
        "Weighted average of districts within 800m of the station",
      manual: "Compiled by hand",
    },
  },
  axes: {
    rentValue: "Rent value",
    commute: "Commute",
    transitConvenience: "Transit options",
    shopping: "Groceries",
    food: "Restaurants",
    cafe: "Cafés",
    nightlife: "Nightlife",
    safety: "Safety",
    quietness: "Quietness",
    family: "Families",
    singleLife: "Living alone",
    internationalFriendliness: "Foreigner-friendly",
    style: "Style",
    nature: "Parks & nature",
    healthcare: "Healthcare",
    fitness: "Gyms",
  },
  grades: {
    excellent: "Excellent",
    good: "Good",
    fair: "Average",
    poor: "Weak",
  },
  rentTypes: {
    oneRoom: "Studio (1R)",
    oneK: "1K",
    oneLDK: "1LDK",
    twoLDK: "2LDK",
  },
  presets: {
    balanced: "Balanced",
    single: "Living alone",
    family: "Family",
    quiet: "Quiet",
    value: "Value",
    international: "Foreign residents",
  },
  offices: {
    shinjuku: "Shinjuku",
    shibuya: "Shibuya",
    tokyo: "Tokyo Station",
    shinagawa: "Shinagawa",
    otemachi: "Otemachi",
    toranomon: "Toranomon",
    roppongi: "Roppongi",
  },
  crowdingLevels: {
    1: "Comfortable",
    2: "Fairly comfortable",
    3: "Moderate",
    4: "Crowded",
    5: "Very crowded",
  },
};

const DICTIONARIES: Record<ActiveLocale, Dictionary> = { ja, en };

export function getDictionary(locale: ActiveLocale): Dictionary {
  return DICTIONARIES[locale];
}
