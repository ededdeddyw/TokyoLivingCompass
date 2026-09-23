import type { ActiveLocale } from "./i18n";
import type { ExitTag, RentMethod, RentType, ScoreAxis, StationTag } from "./schema";
import type { Grade } from "./scoring";
import type { WeightPreset } from "./weights";

/** UI 文言。駅の散文（data/content）とは別管理（docs/04-i18n.md §6）。 */

export type Dictionary = {
  siteName: string;
  /**
   * 検索結果に出す見出し。本文の tagline をそのまま使うと長すぎて途中で切られ、
   * どの駅の何の話か分からなくなる。何が読めるページなのかを短く書く。
   */
  /**
   * トップページの見出し。Next の title.template は、そのテンプレートを
   * 定義した階層のページ自身には効かない。トップだけはサイト名を自分で書く。
   */
  seoHomeTitle: string;
  seoStationTitle: string;
  /** 勤務先からの逆引きページの見出し。 */
  seoWorkTitle: string;
  /** 2駅を比べるページの見出し。 */
  seoCompareTitle: string;
  tagline: string;
  nav: { stations: string; find: string; compare: string };
  /** 運営者情報ページ（docs/05-seo.md §5）。 */
  about: {
    heading: string;
    operatorLabel: string;
    operatorName: string;
    contactLabel: string;
    whatThisIs: string;
    sourcesHeading: string;
    sources: string[];
    disclaimerHeading: string;
    disclaimers: string[];
    updatedLabel: string;
  };
  home: {
    lead: string;
    findCta: string;
    browseCta: string;
    featuredHeading: string;
  };
  station: {
    overall: string;
    /** 同じ乗換駅の、表示名に選ばなかった駅名を出すときの文言。 */
    alsoKnownAs: string;
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
    compiledComment: string;
    compiledCommentNote: string;
    compiledCommentSources: string;
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
    excludedForMissingRent: string;
  };
  roster: {
    heading: string;
    lead: string;
    stations: string;
    lines: string;
    allLines: string;
    profiled: string;
    filterByLine: string;
  };
  compare: {
    heading: string;
    winner: string;
    tie: string;
  };
  depth: {
    heading: string;
    faces: string;
    morning: string;
    daytime: string;
    night: string;
    weekend: string;
    terrain: string;
    slope: Record<"flat" | "some" | "hilly", string>;
    noiseSources: string;
    groceries: string;
    tier: Record<"discount" | "standard" | "premium", string>;
    walkMinutes: string;
    residents: string;
    housingStock: string;
    hazards: string;
    stationNote: string;
    nightWalk: string;
    rentReason: string;
    neighbours: string;
    alternatives: string;
    outlook: string;
    exits: string;
    family: string;
    medical: string;
    rentRange: string;
    rentDrivers: string;
    unwritten: string;
  };
  dataQuality: {
    seedWarning: string;
    notAvailable: string;
    noScoresYet: string;
    rosterOnly: string;
  };
  commuteNote: string;
  hazardNote: string;
  rentBands: {
    title: string;
    band: string;
    attribution: string;
    wideSpreadNote: string;
    provisional: string;
  };
  rentHistory: {
    title: string;
    period: string;
    range: string;
  };
  rentSource: {
    missing: string;
    askingCaveat: string;
    basis: Record<"asking" | "contracted" | "paid", string>;
    statistic: Record<"median" | "mean", string>;
    method: Record<RentMethod, string>;
  };
  tags: Record<StationTag, string>;
  exitTags: Record<ExitTag, string>;
  axes: Record<ScoreAxis, string>;
  grades: Record<Grade, string>;
  rentTypes: Record<RentType, string>;
  presets: Record<WeightPreset, string>;
  offices: Record<string, string>;
  crowdingLevels: Record<1 | 2 | 3 | 4 | 5, string>;
};

const ja: Dictionary = {
  siteName: "Tokyo Living Compass",
  seoHomeTitle: "東京の住みやすさ比較｜Tokyo Living Compass",
  seoStationTitle: "{name}の住みやすさ｜家賃・通勤・坂・浸水想定",
  seoWorkTitle: "{office}勤務なら、どこに住むべきか",
  seoCompareTitle: "{a}と{b}、どちらに住むか｜家賃・通勤・環境の比較",
  tagline: "東京で、あなたに一番合う街を見つける。",
  nav: { stations: "駅を見る", find: "駅を探す", compare: "駅を比べる" },
  about: {
    heading: "このサイトについて",
    operatorLabel: "運営者",
    operatorName: "日本で最高の場所に住もう",
    contactLabel: "連絡先",
    whatThisIs:
      "東京23区の458駅について、家賃・通勤時間・土地の高低・浸水想定・周辺施設を集め、" +
      "住む街を決めるために比べられる形にしたサイトです。物件を探す前に、" +
      "どの街に住むかを決めるために使ってください。",
    sourcesHeading: "数字の出どころ",
    sources: [
      "家賃: LIFULL HOME'S・Yahoo!不動産・アットホームが公開する駅ごとの相場を平均し、1万円刻みに丸めた値（当社調べ）",
      "所要時間: 駅間の距離と路線の種別から計算した推定値。乗車時間を基準にし、乗り換え1回につき5分を加えている",
      "土地の高低: 国土地理院の標高API。駅と半径400mの8方位、計9地点を読み取った値",
      "浸水想定: 重ねるハザードマップ（国土交通省・国土地理院）の想定最大規模の区域",
      "周辺施設: OpenStreetMap contributors（ODbL）",
      "駅・路線: 駅データ.jp ほか公開データ",
    ],
    disclaimerHeading: "読むときに知っておいてほしいこと",
    disclaimers: [
      "家賃は募集賃料の平均です。実際に契約する金額はこれより下がることがあります。" +
        "同じ駅でも、築年数・駅からの距離・通りに面しているかで大きく変わります。",
      "浸水想定区域は、想定しうる最大規模の雨や台風を前提にした試算です。" +
        "ふだん浸水する場所という意味でも、区域の外なら浸水しないという意味でもありません。" +
        "住む場所を決める前に、住所ごとに区のハザードマップで確認してください。",
      "所要時間は計算した推定値で、実際の時刻表に基づくものではありません。" +
        "快速や特急などの優等列車は考慮していません。",
      "店名や施設名は OpenStreetMap に登録されている情報です。" +
        "閉店や移転が反映されていない場合があります。",
      "このサイトは不動産の取引を行いません。物件の紹介・仲介もしていません。",
    ],
    updatedLabel: "最終更新",
  },
  home: {
    lead: "勤務先・予算・暮らし方から、東京のどこに住むべきかを決めるためのサービスです。物件を探す前に、街を決める。",
    findCta: "勤務先から駅を探す",
    browseCta: "駅一覧を見る",
    featuredHeading: "掲載中の駅",
  },
  station: {
    overall: "総合評価",
    alsoKnownAs: "{names}も同じ乗換駅として扱っています",
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
    compiledComment: "この街の特色のまとめ",
    compiledCommentNote:
      "この節は、公開されている情報を集めてまとめたものです。実際に住んだ人が書いたものではありません。",
    compiledCommentSources: "もとにした情報",
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
    excludedForMissingRent:
      "通勤条件は満たすものの、家賃相場が未取得のため判定できなかった駅が {count} 件あります。",
  },
  roster: {
    heading: "掲載候補の全駅",
    lead: "都営線・東京メトロ・JR山手線・中央線・中央総武線と、23区を通る私鉄各線の駅を洗い出したものです。駅名・所在区・路線までを持ち、詳細プロフィールはここから順に作っていきます。",
    stations: "駅",
    lines: "路線",
    allLines: "すべての路線",
    profiled: "詳細ページあり",
    filterByLine: "路線でしぼる",
  },
  compare: {
    heading: "駅を比べる",
    winner: "優位",
    tie: "同等",
  },
  depth: {
    heading: "住むと分かること",
    faces: "朝・昼・夜・週末のようす",
    morning: "朝",
    daytime: "昼",
    night: "夜",
    weekend: "週末",
    terrain: "坂・高低差",
    slope: { flat: "ほぼ平坦", some: "坂がある", hilly: "起伏が大きい" },
    noiseSources: "音が気になりうる場所",
    groceries: "日常の買い物",
    tier: { discount: "安い", standard: "標準", premium: "高い" },
    walkMinutes: "徒歩",
    residents: "住んでいる人の層",
    housingStock: "物件の傾向",
    hazards: "災害リスク",
    stationNote: "駅の使い勝手",
    nightWalk: "夜の帰り道",
    rentReason: "家賃がこの水準である理由",
    neighbours: "近くの駅との違い",
    alternatives: "この駅と迷いやすい駅",
    outlook: "これからどう変わるか",
    exits: "出口で変わる街の顔",
    family: "子育て",
    medical: "医療",
    rentRange: "同じ駅でも家賃に幅がある",
    rentDrivers: "差を生む要因",
    unwritten: "未記入",
  },
  dataQuality: {
    seedWarning:
      "このページのデータは開発用の推定値です。出典に基づく確定値ではありません。",
    notAvailable: "—",
    noScoresYet: "この駅のスコアはまだ測定していません。",
    rosterOnly: "この駅はまだ駅名・所在区・路線と所要時間しかありません。",
  },
  commuteNote:
    "所要時間は駅間距離と路線種別から計算した推定値です（乗車時間ベース、乗換5分で算入）。優等列車は考慮していません。",
  rentBands: {
    title: "家賃の目安（当社調べ）",
    band: "{low}万〜{high}万円",
    attribution:
      "{sources} が公開している駅ごとの掲載相場を平均し、1万円刻みに丸めた値です（{date} 時点・当社調べ）。いずれも募集賃料のため、実際の成約額はこれより下がることがあります。",
    wideSpreadNote:
      "* を付けた間取りは、出典によって3万円以上の開きがあります。集計する範囲や対象物件がサイトごとに違うためで、帯の中に収まらない物件も相応にあります。",
    provisional:
      "この数値は掲載元のページを開いての確認が済んでいない暫定値です。公開前に確認します。",
  },
  hazardNote:
    "浸水想定区域とは、想定しうる最大規模の雨や台風が起きた場合に浸水すると試算された範囲です。ふだんから浸水する場所という意味ではなく、また区域の外なら浸水しないという意味でもありません。想定される深さは同じ駅でも区画ごとに違うため、住む場所を決める前に、区が公開しているハザードマップで住所ごとに確認してください。",
  rentHistory: {
    title: "家賃の推移",
    period: "時点",
    range: "{from} から {to} までの推移",
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
      "multi-site-average": "複数サイトが公開する駅別の相場を平均",
      manual: "手集計",
    },
  },
  tags: {
      majorHub: "大きな繁華街",
    someBustle: "やや繁華街",
      lively: "にぎやか",
      quiet: "静か",
      shoppingEasy: "買い物が近い",
      diningRich: "外食の店が多い",
      cafeRich: "カフェが多い",
      lateNight: "夜遅くまで開いている店がある",
      parkNear: "公園が近い",
      flat: "坂がない",
      hilly: "坂が多い",
      goodValue: "通勤の速さのわりに家賃が安い",
      pricey: "通勤の速さのわりに家賃が高い",
      fastToCenter: "都心へ速い",
      manyLines: "路線が多い",
      singleLine: "1路線だけ",
      floodArea: "浸水想定区域に入る地点が多い",
      lowFlood: "浸水想定区域に入る地点が少ない",
      familyFriendly: "子育て向きの環境",
      singleFriendly: "一人暮らし向き",
      medicalRich: "医療機関が多い",
    },
  exitTags: {
      shoppingStreet: "商店街",
      departmentStore: "大型商業施設",
      diningCluster: "飲食店が集まる",
      barStreet: "飲み屋街",
      residential: "住宅街",
      quietResidential: "閑静な住宅街",
      office: "オフィス街",
    entertainment: "繁華街",
    culture: "美術館・ホール",
      school: "学校が多い",
      park: "公園",
      waterfront: "水辺",
      factory: "町工場・倉庫",
      hospital: "病院",
      uphill: "坂を上る",
      downhill: "坂を下る",
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
    disaster: "浸水想定の小ささ",
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
  seoHomeTitle: "Where to live in Tokyo — Tokyo Living Compass",
  seoStationTitle: "Living in {name}: rent, commute, slopes, flood risk",
  seoWorkTitle: "Where to live if you work in {office}",
  seoCompareTitle: "{a} or {b}: comparing rent, commute and surroundings",
  tagline: "Find the Tokyo neighborhood that fits you.",
  nav: { stations: "Stations", find: "Find your area", compare: "Compare" },
  about: {
    heading: "About this site",
    operatorLabel: "Operated by",
    operatorName: "日本で最高の場所に住もう (Nihon de saikou no basho ni sumou)",
    contactLabel: "Contact",
    whatThisIs:
      "For all 458 stations in Tokyo's 23 wards, this site gathers rent, journey times, " +
      "the lie of the land, projected flood depths and nearby facilities, and puts them in a " +
      "form you can compare. It is for deciding which neighbourhood to live in, before you " +
      "start looking at flats.",
    sourcesHeading: "Where the figures come from",
    sources: [
      "Rent: the per-station averages published by LIFULL HOME'S, Yahoo! Real Estate and at home, averaged together and rounded down to the nearest ¥10,000 (our own survey)",
      "Journey times: estimates computed from inter-station distance and line type, based on in-vehicle time, with 5 minutes allowed per change",
      "Elevation: the elevation API of the Geospatial Information Authority of Japan, read at nine points (the station and eight compass directions 400 m out)",
      "Flood projections: the national hazard map (MLIT and the Geospatial Information Authority of Japan), for the largest scenario modelled",
      "Nearby facilities: OpenStreetMap contributors (ODbL)",
      "Stations and lines: ekidata.jp and other published data",
    ],
    disclaimerHeading: "What to know before you read",
    disclaimers: [
      "Rents are averages of asking rents. What tenants finally agree can be lower. Within the same station area the figure moves a great deal with the age of the building, the walk from the station, and whether the flat faces a main road.",
      "A projected inundation area is an estimate based on the largest rainfall or typhoon the authorities plan for. It does not mean the area floods routinely, nor that areas outside it never flood. Before deciding where to live, check your specific address on the ward's own hazard map.",
      "Journey times are computed estimates, not taken from timetables. Express and rapid services are not modelled.",
      "Shop and facility names come from OpenStreetMap. Closures and relocations may not be reflected.",
      "This site does not deal in property. It neither lists nor brokers flats.",
    ],
    updatedLabel: "Last updated",
  },
  home: {
    lead: "Decide where to live in Tokyo based on your office, budget and lifestyle. Choose the neighborhood before you start looking at apartments.",
    findCta: "Find areas near your office",
    browseCta: "Browse all stations",
    featuredHeading: "Stations covered",
  },
  station: {
    overall: "Overall",
    alsoKnownAs: "{names} is treated as the same interchange",
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
    compiledComment: "What this neighbourhood is like",
    compiledCommentNote:
      "This section is compiled from published sources. It is not written by someone who has lived here.",
    compiledCommentSources: "Compiled from",
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
    excludedForMissingRent:
      "{count} more stations meet your commute limits but have no rent data yet, so they could not be checked against your budget.",
  },
  roster: {
    heading: "Every station we plan to cover",
    lead: "All stations on the Toei and Tokyo Metro subways, the JR Yamanote, Chuo and Chuo-Sobu lines, and the private railways running through the 23 wards. Each entry has its name, ward and lines; full profiles are being written from this list.",
    stations: "stations",
    lines: "lines",
    allLines: "All lines",
    profiled: "with a full profile",
    filterByLine: "Filter by line",
  },
  compare: {
    heading: "Compare stations",
    winner: "Better",
    tie: "Even",
  },
  depth: {
    heading: "What you only learn by living there",
    faces: "How the area changes through the day",
    morning: "Morning",
    daytime: "Daytime",
    night: "Night",
    weekend: "Weekend",
    terrain: "Slopes",
    slope: { flat: "Mostly flat", some: "Some slopes", hilly: "Hilly" },
    noiseSources: "Possible sources of noise",
    groceries: "Everyday shopping",
    tier: { discount: "Cheap", standard: "Standard", premium: "Upmarket" },
    walkMinutes: "walk",
    residents: "Who lives here",
    housingStock: "What the housing is like",
    hazards: "Disaster risk",
    stationNote: "Using the station",
    nightWalk: "Walking home at night",
    rentReason: "Why rent sits where it does",
    neighbours: "How the nearest stations differ",
    alternatives: "Stations you may be weighing this one against",
    outlook: "How it is changing",
    exits: "How the area differs by exit",
    family: "Raising children",
    medical: "Healthcare",
    rentRange: "Rent varies within the same station",
    rentDrivers: "What drives the difference",
    unwritten: "Not written yet",
  },
  dataQuality: {
    seedWarning:
      "The data on this page is a development placeholder, not a sourced figure.",
    notAvailable: "—",
    noScoresYet: "Scores for this station have not been measured yet.",
    rosterOnly:
      "So far this station only has its name, ward, lines and commute times.",
  },
  commuteNote:
    "Times are estimates computed from inter-station distance and line type (in-vehicle time, 5 minutes allowed per transfer). Express services are not modelled.",
  rentBands: {
    title: "Typical rent (our own survey)",
    band: "¥{low}0k–{high}0k",
    attribution:
      "Average of the per-station asking rents published by {sources}, rounded to the nearest ¥10,000 (as of {date}, our own survey). These are asking rents; the rent actually agreed is often lower.",
    wideSpreadNote:
      "Layouts marked * differ by more than ¥30,000 between sources, because each site aggregates a different set of listings. A fair number of homes fall outside the band.",
    provisional:
      "These figures have not yet been checked against the source pages and are provisional.",
  },
  hazardNote:
    "A flood hazard zone is the area a ward estimates would flood under the largest rainfall or typhoon it plans for. It does not mean the area floods routinely, nor that areas outside it never flood. Estimated depths differ block by block within the same station area, so check your specific address on the ward's own hazard map before deciding where to live.",
  rentHistory: {
    title: "How rents have moved",
    period: "Period",
    range: "Change from {from} to {to}",
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
      "multi-site-average":
        "Average of the per-station figures published by several sites",
      manual: "Compiled by hand",
    },
  },
  tags: {
      majorHub: "Major entertainment district",
    someBustle: "Somewhat busy",
      lively: "Lively",
      quiet: "Quiet",
      shoppingEasy: "Shops close by",
      diningRich: "Plenty of places to eat",
      cafeRich: "Plenty of cafes",
      lateNight: "Places open late",
      parkNear: "Parks nearby",
      flat: "Flat ground",
      hilly: "Hilly",
      goodValue: "Good value for the commute",
      pricey: "Expensive for the commute",
      fastToCenter: "Quick into the centre",
      manyLines: "Several lines",
      singleLine: "One line only",
      floodArea: "Much of the area is in the flood projection",
      lowFlood: "Little of the area is in the flood projection",
      familyFriendly: "Suits families",
      singleFriendly: "Suits living alone",
      medicalRich: "Many medical facilities",
    },
  exitTags: {
      shoppingStreet: "Shopping street",
      departmentStore: "Large shopping complex",
      diningCluster: "Restaurants cluster here",
      barStreet: "Bar street",
      residential: "Housing",
      quietResidential: "Quiet residential streets",
      office: "Offices",
    entertainment: "Entertainment district",
    culture: "Museum or concert hall",
      school: "Schools",
      park: "Park",
      waterfront: "Waterfront",
      factory: "Small factories and warehouses",
      hospital: "Hospital",
      uphill: "Uphill",
      downhill: "Downhill",
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
    disaster: "Low flood projection",
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


const zhHans: Dictionary = {
  siteName: "Tokyo Living Compass",
  seoHomeTitle: "东京居住条件比较｜Tokyo Living Compass",
  seoStationTitle: "{name}的居住条件｜租金·通勤·坡道·浸水想定",
  seoWorkTitle: "在{office}上班的话，该住哪里",
  seoCompareTitle: "{a}还是{b}｜租金·通勤·环境的比较",
  tagline: "找到适合你的东京街区。",
  nav: { stations: "车站一览", find: "找住处", compare: "比较" },
  about: {
    heading: "关于本站",
    operatorLabel: "运营者",
    operatorName: "日本で最高の場所に住もう",
    contactLabel: "联系方式",
    whatThisIs:
      "本站收集东京23区458个车站的租金、通勤时间、地势高低、浸水想定和周边设施，" +
      "整理成可以互相比较的形式。请在找房子之前，用它来决定住在哪个街区。",
    sourcesHeading: "数字的来源",
    sources: [
      "租金：取 LIFULL HOME'S、Yahoo!不动产、at home 三家公布的分车站行情的平均值，并向下取整到1万日元（本公司调查）",
      "通勤时间：按站间距离和线路种类计算的估算值。以乘车时间为准，每次换乘计入5分钟",
      "地势高低：日本国土地理院的海拔API。读取了车站和半径400米的八个方位，共九个点",
      "浸水想定：重叠灾害地图（国土交通省·国土地理院）按可能出现的最大规模推算的区域",
      "周边设施：OpenStreetMap contributors（ODbL）",
      "车站·线路：车站数据.jp 等公开数据",
    ],
    disclaimerHeading: "阅读前请知悉",
    disclaimers: [
      "租金是招租价格的平均值。实际签约的金额可能低于此。即使是同一个车站，房龄、离车站的距离、是否临街，都会让金额差出很多。",
      "浸水想定区域，是按所设想的最大降雨或台风推算出的范围。它既不表示这里平时就会淹水，也不表示区域之外就不会淹。在决定住处之前，请按具体地址查看所在区发布的灾害地图。",
      "通勤时间是计算出的估算值，不是依据实际时刻表。未考虑快速、特急等优等列车。",
      "店名和设施名来自 OpenStreetMap，可能没有反映歇业或搬迁。",
      "本站不从事不动产交易，也不介绍或中介房源。",
    ],
    updatedLabel: "最后更新",
  },
  home: {
    lead: "按公司位置、预算和生活方式，决定在东京住哪里。先定下住的街区，再去看房子。",
    findCta: "从公司位置找街区",
    browseCta: "查看全部车站",
    featuredHeading: "收录的车站",
  },
  station: {
    overall: "综合",
    alsoKnownAs: "{names}也作为同一换乘站处理",
    rent: "租金行情",
    commute: "通勤",
    lines: "线路",
    firstTrain: "本站始发",
    crowding: "早高峰拥挤度",
    scores: "各项评分",
    facilities: "周边设施",
    supermarkets: "超市",
    commercial: "购物",
    goodFor: "适合的人",
    notFor: "不适合的人",
    residentComment: "住在东京的人怎么说",
    compiledComment: "这个街区的特色小结",
    compiledCommentNote:
      "本节是汇总公开信息整理而成，并非实际住过的人所写。",
    compiledCommentSources: "参考的信息",
    similar: "条件相近的车站",
    compareWith: "与这个车站比较",
    perMonth: "／月",
    minutes: "分钟",
    transfers: "次换乘",
    noTransfer: "直达",
    yes: "有",
    no: "无",
    backToList: "返回车站一览",
  },
  list: {
    heading: "全部车站",
    count: "个车站",
    sortBy: "排序",
    perspective: "按什么排序",
  },
  find: {
    heading: "从公司位置出发，找该住哪里",
    lead: "填入公司位置、预算和通勤上限，我们按实际满足条件的车站排序。",
    office: "公司位置",
    maxRent: "租金上限",
    rentType: "户型",
    maxMinutes: "通勤时间上限",
    maxTransfers: "换乘次数上限",
    priority: "你看重什么",
    submit: "查找车站",
    results: "结果",
    noResults: "没有符合这些条件的车站。可以提高租金上限，或者放宽通勤时间。",
    fit: "契合度",
    why: "为什么合适",
    weakness: "需要取舍的地方",
    excludedForMissingRent:
      "另有{count}个车站满足通勤条件，但还没有租金数据，无法与预算对照。",
  },
  roster: {
    heading: "计划收录的全部车站",
    lead: "包括都营地铁和东京地铁的全部车站，JR山手线、中央线、中央·总武线，以及经过23区的各条私营铁路。每个条目都有车站名、所在区和线路，详细内容正按这份名单逐个补写。",
    stations: "个车站",
    lines: "条线路",
    allLines: "全部线路",
    profiled: "已写完详细内容",
    filterByLine: "按线路筛选",
  },
  compare: {
    heading: "比较车站",
    winner: "更好",
    tie: "相当",
    },
  depth: {
    heading: "住下来才知道的事",
    faces: "一天之中街区的变化",
    morning: "早晨",
    daytime: "白天",
    night: "夜晚",
    weekend: "周末",
    terrain: "坡道",
    slope: { flat: "基本平坦", some: "有缓坡", hilly: "起伏较大" },
    noiseSources: "可能的噪音来源",
    groceries: "日常采买",
    tier: { discount: "便宜", standard: "普通", premium: "高档" },
    walkMinutes: "步行",
    residents: "住的是哪些人",
    housingStock: "房子的类型",
    hazards: "灾害风险",
    stationNote: "车站用起来如何",
    nightWalk: "夜里回家的路",
    rentReason: "租金为何是这个水平",
    neighbours: "与邻近车站的差别",
    alternatives: "会与这里放在一起比较的车站",
    outlook: "今后会怎么变",
    exits: "不同出口的差别",
    family: "养育孩子",
    medical: "医疗",
    rentRange: "同一车站内的租金差别",
    rentDrivers: "差别来自哪里",
    unwritten: "尚未写",
  },
  dataQuality: {
    seedWarning: "本页的数据是开发用的占位值，不是有出处的数字。",
    notAvailable: "—",
    noScoresYet: "这个车站的各项评分还没有测算。",
    rosterOnly: "目前这个车站只有车站名、所在区、线路和所需时间。",
  },
  commuteNote:
    "所需时间是按站间距离和线路种类计算的估算值（以乘车时间为准，每次换乘计入5分钟），未考虑快速和特急等优等列车。",
  rentBands: {
    title: "租金行情（本公司调查）",
    band: "{low}万～{high}万日元",
    attribution:
      "取{sources}公布的分车站招租价格的平均值，向下取整到1万日元（{date}时点，本公司调查）。均为招租价格，实际成交的金额往往更低。",
    wideSpreadNote:
      "带*的户型，各家来源相差3万日元以上。这是因为各网站统计的房源范围不同，落在区间之外的房子也不少。",
    provisional: "这些数字尚未对照原始页面确认，属于暂定值。",
  },
  hazardNote:
    "浸水想定区域，是各区按所设想的最大降雨或台风推算出的、可能被水淹的范围。它既不表示这里平时就会淹水，也不表示区域之外就不会淹。即使是同一个车站周边，推算的水深也会因街区而异，所以在决定住处之前，请按具体地址查看所在区发布的灾害地图。",
  rentHistory: {
    title: "租金的变化",
    period: "期间",
    range: "从{from}到{to}的变化",
  },
  rentSource: {
    missing: "这些租金数字还没有记录出处。",
    askingCaveat: "这些是招租价格，实际成交的金额往往更低。",
    basis: {
      asking: "招租价格",
      contracted: "成交价格",
      paid: "实际在付的租金",
    },
    statistic: { median: "中位数", mean: "平均值" },
    method: {
      "vendor-station-area": "由数据提供方按车站周边汇总",
      "radius-800m-weighted": "车站800米以内各街区的加权平均",
      "multi-site-average": "多家网站公布的分车站数值的平均",
      manual: "人工整理",
    },
  },
  tags: {
      majorHub: "大型繁华街",
    someBustle: "略显繁华",
      lively: "热闹",
      quiet: "安静",
      shoppingEasy: "买东西方便",
      diningRich: "餐饮店多",
      cafeRich: "咖啡馆多",
      lateNight: "有营业到深夜的店",
      parkNear: "公园近",
      flat: "没有坡",
      hilly: "坡道多",
      goodValue: "相对通勤速度租金便宜",
      pricey: "相对通勤速度租金偏高",
      fastToCenter: "到市中心快",
      manyLines: "线路多",
      singleLine: "只有一条线",
      floodArea: "进入浸水想定区域的地点多",
      lowFlood: "进入浸水想定区域的地点少",
      familyFriendly: "适合育儿",
      singleFriendly: "适合独居",
      medicalRich: "医疗机构多",
    },
  exitTags: {
      shoppingStreet: "商店街",
      departmentStore: "大型商业设施",
      diningCluster: "餐饮店聚集",
      barStreet: "酒馆街",
      residential: "住宅区",
      quietResidential: "安静的住宅区",
      office: "办公区",
    entertainment: "繁华街",
    culture: "美术馆·音乐厅",
      school: "学校多",
      park: "公园",
      waterfront: "水边",
      factory: "小工厂和仓库",
      hospital: "医院",
      uphill: "上坡",
      downhill: "下坡",
    },
  axes: {
    rentValue: "租金性价比",
    commute: "通勤",
    transitConvenience: "换乘便利",
    shopping: "日常采买",
    food: "餐饮",
    cafe: "咖啡馆",
    nightlife: "夜间营业",
    safety: "治安",
    quietness: "安静程度",
    family: "育儿",
    singleLife: "单身生活",
    internationalFriendliness: "对外国人的友好度",
    style: "街区气质",
    nature: "公园和绿地",
    healthcare: "医疗",
    fitness: "健身房",
    disaster: "浸水预估较小",
  },
  grades: {
    excellent: "很好",
    good: "较好",
    fair: "一般",
    poor: "较弱",
  },
  rentTypes: {
    oneRoom: "一室户（1R）",
    oneK: "1K",
    oneLDK: "1LDK",
    twoLDK: "2LDK",
  },
  presets: {
    balanced: "均衡",
    single: "单身生活",
    family: "家庭",
    quiet: "安静",
    value: "性价比",
    international: "外国居民",
  },
  offices: {
    shinjuku: "新宿",
    shibuya: "涩谷",
    tokyo: "东京站",
    shinagawa: "品川",
    otemachi: "大手町",
    toranomon: "虎之门",
    roppongi: "六本木",
  },
  crowdingLevels: {
    1: "宽松",
    2: "比较宽松",
    3: "一般",
    4: "拥挤",
    5: "非常拥挤",
  },
};

const ko: Dictionary = {
  siteName: "Tokyo Living Compass",
  seoHomeTitle: "도쿄 거주 여건 비교｜Tokyo Living Compass",
  seoStationTitle: "{name} 거주 여건｜임대료·출퇴근·언덕·침수 상정",
  seoWorkTitle: "{office}에서 일한다면 어디에 살까",
  seoCompareTitle: "{a}와 {b}, 어디에 살까｜임대료·출퇴근·환경 비교",
  tagline: "나에게 맞는 도쿄의 동네를 찾는다.",
  nav: { stations: "역 목록", find: "살 곳 찾기", compare: "비교" },
  about: {
    heading: "이 사이트에 대하여",
    operatorLabel: "운영자",
    operatorName: "日本で最高の場所に住もう",
    contactLabel: "연락처",
    whatThisIs:
      "도쿄 23구의 458개 역에 대해 임대료, 출퇴근 시간, 땅의 높낮이, 침수 상정, 주변 시설을 모아 " +
      "서로 비교할 수 있는 형태로 정리한 사이트입니다. 집을 찾기 전에, 어느 동네에 살지를 " +
      "정하는 데 써 주세요.",
    sourcesHeading: "숫자의 출처",
    sources: [
      "임대료: LIFULL HOME'S, Yahoo!부동산, at home이 공개하는 역별 시세를 평균 내어 1만 엔 단위로 내림한 값(당사 조사)",
      "출퇴근 시간: 역 사이의 거리와 노선 종류로 계산한 추정값. 승차 시간을 기준으로 하고, 환승 1회당 5분을 더했다",
      "땅의 높낮이: 일본 국토지리원의 표고 API. 역과 반경 400m의 여덟 방위, 모두 아홉 지점을 읽은 값",
      "침수 상정: 가사네루 해저드맵(국토교통성·국토지리원)의 상정 최대 규모 구역",
      "주변 시설: OpenStreetMap contributors(ODbL)",
      "역·노선: 에키데이터.jp 등 공개 데이터",
    ],
    disclaimerHeading: "읽기 전에 알아 두었으면 하는 것",
    disclaimers: [
      "임대료는 모집 임대료의 평균입니다. 실제로 계약하는 금액은 이보다 낮아질 수 있습니다. 같은 역이라도 건축 연수, 역에서의 거리, 큰길에 면해 있는지에 따라 크게 달라집니다.",
      "침수 상정 구역은 상정할 수 있는 최대 규모의 비나 태풍을 전제로 한 추산입니다. 평소에 물에 잠기는 곳이라는 뜻도, 구역 밖이면 잠기지 않는다는 뜻도 아닙니다. 살 곳을 정하기 전에 주소별로 구청이 내놓은 재해 지도에서 확인해 주세요.",
      "출퇴근 시간은 계산한 추정값이며, 실제 시각표에 따른 것이 아닙니다. 쾌속이나 특급 같은 우등 열차는 반영하지 않았습니다.",
      "가게 이름과 시설 이름은 OpenStreetMap에 등록된 정보입니다. 폐업이나 이전이 반영되지 않았을 수 있습니다.",
      "이 사이트는 부동산 거래를 하지 않습니다. 매물 소개나 중개도 하지 않습니다.",
    ],
    updatedLabel: "최종 수정",
  },
  home: {
    lead: "회사 위치와 예산, 생활 방식에 맞춰 도쿄에서 살 곳을 정한다. 집을 보러 다니기 전에, 살 동네부터 정한다.",
    findCta: "회사 위치에서 동네 찾기",
    browseCta: "역 전체 보기",
    featuredHeading: "다루고 있는 역",
  },
  station: {
    overall: "종합",
    alsoKnownAs: "{names}도 같은 환승역으로 다룹니다",
    rent: "임대료 시세",
    commute: "출퇴근",
    lines: "노선",
    firstTrain: "이 역에서 출발",
    crowding: "아침 혼잡도",
    scores: "항목별 점수",
    facilities: "주변 시설",
    supermarkets: "슈퍼마켓",
    commercial: "쇼핑",
    goodFor: "맞는 사람",
    notFor: "맞지 않는 사람",
    residentComment: "도쿄에 사는 사람의 이야기",
    compiledComment: "이 동네의 특색 정리",
    compiledCommentNote:
      "이 절은 공개된 정보를 모아 정리한 것입니다. 실제로 살아 본 사람이 쓴 글이 아닙니다.",
    compiledCommentSources: "참고한 정보",
    similar: "조건이 비슷한 역",
    compareWith: "이 역과 비교",
    perMonth: "／월",
    minutes: "분",
    transfers: "회 환승",
    noTransfer: "직통",
    yes: "있음",
    no: "없음",
    backToList: "역 목록으로 돌아가기",
  },
  list: {
    heading: "역 전체",
    count: "개 역",
    sortBy: "정렬",
    perspective: "무엇을 기준으로",
  },
  find: {
    heading: "회사 위치에서 시작해 살 곳을 찾는다",
    lead: "회사 위치와 예산, 출퇴근 시간의 상한을 넣으면 실제로 조건을 채우는 역을 순서대로 보여준다.",
    office: "회사 위치",
    maxRent: "임대료 상한",
    rentType: "구조",
    maxMinutes: "출퇴근 시간 상한",
    maxTransfers: "환승 횟수 상한",
    priority: "무엇을 중요하게 보는가",
    submit: "역 찾기",
    results: "결과",
    noResults: "이 조건에 맞는 역이 없다. 임대료 상한을 올리거나 출퇴근 시간을 늘려 보자.",
    fit: "적합도",
    why: "맞는 이유",
    weakness: "감수해야 할 점",
    excludedForMissingRent:
      "출퇴근 조건은 채우지만 임대료 데이터가 아직 없어 예산과 대조하지 못한 역이 {count}개 더 있다.",
  },
  roster: {
    heading: "다룰 예정인 역 전체",
    lead: "도영지하철과 도쿄메트로의 모든 역, JR 야마노테선·주오선·주오소부선, 그리고 23구를 지나는 사철 각 노선을 포함한다. 각 항목에는 역 이름과 소재 구, 노선이 들어 있고, 자세한 내용은 이 목록을 따라 차례로 쓰고 있다.",
    stations: "개 역",
    lines: "개 노선",
    allLines: "전체 노선",
    profiled: "자세한 내용까지 작성",
    filterByLine: "노선으로 좁히기",
  },
  compare: {
    heading: "역 비교",
    winner: "더 나음",
    tie: "비슷함",
  },
  depth: {
    heading: "살아 봐야 아는 것",
    faces: "하루 동안 동네가 바뀌는 모습",
    morning: "아침",
    daytime: "낮",
    night: "밤",
    weekend: "주말",
    terrain: "언덕",
    slope: { flat: "거의 평탄", some: "완만한 언덕", hilly: "높낮이 차이가 큼" },
    noiseSources: "소음이 날 만한 곳",
    groceries: "일상 장보기",
    tier: { discount: "저렴", standard: "보통", premium: "고급" },
    walkMinutes: "도보",
    residents: "어떤 사람들이 사는가",
    housingStock: "어떤 집이 많은가",
    hazards: "재해 위험",
    stationNote: "역을 쓸 때",
    nightWalk: "밤에 집으로 가는 길",
    rentReason: "임대료가 이 수준인 이유",
    neighbours: "가까운 역과의 차이",
    alternatives: "이 역과 함께 놓고 고민하게 되는 역",
    outlook: "앞으로 어떻게 바뀌는가",
    exits: "출구에 따른 차이",
    family: "아이를 키우기",
    medical: "의료",
    rentRange: "같은 역 안에서의 임대료 차이",
    rentDrivers: "차이가 생기는 이유",
    unwritten: "아직 쓰지 않음",
  },
  dataQuality: {
    seedWarning: "이 페이지의 데이터는 개발용 임시값이며, 출처가 있는 숫자가 아니다.",
    notAvailable: "—",
    noScoresYet: "이 역의 항목별 점수는 아직 산출하지 않았다.",
    rosterOnly: "지금 이 역에는 역 이름과 소재 구, 노선, 소요 시간만 들어 있다.",
  },
  commuteNote:
    "소요 시간은 역 사이의 거리와 노선 종류로 계산한 추정값이다(승차 시간 기준, 환승 1회당 5분 산입). 쾌속이나 특급 같은 우등 열차는 반영하지 않았다.",
  rentBands: {
    title: "임대료 시세(당사 조사)",
    band: "{low}만~{high}만 엔",
    attribution:
      "{sources}이 공개하는 역별 모집 임대료를 평균 내어 1만 엔 단위로 내림한 값이다({date} 기준, 당사 조사). 모두 모집 임대료이므로, 실제로 계약되는 금액은 이보다 낮은 경우가 많다.",
    wideSpreadNote:
      "*가 붙은 구조는 출처마다 값이 3만 엔 이상 벌어진다. 사이트마다 집계하는 매물의 범위가 달라서이며, 이 구간을 벗어나는 집도 적지 않다.",
    provisional: "이 숫자들은 아직 출처 페이지와 대조하지 않은 잠정값이다.",
  },
  hazardNote:
    "침수 상정 구역이란, 구청이 상정하는 최대 규모의 비나 태풍이 왔을 때 물에 잠길 것으로 추산한 범위다. 평소에 물에 잠기는 곳이라는 뜻도, 구역 밖이면 잠기지 않는다는 뜻도 아니다. 같은 역 주변이라도 구획마다 상정되는 깊이가 다르므로, 살 곳을 정하기 전에 주소별로 구청이 내놓은 재해 지도에서 확인하기 바란다.",
  rentHistory: {
    title: "임대료의 변화",
    period: "기간",
    range: "{from}부터 {to}까지의 변화",
  },
  rentSource: {
    missing: "이 임대료 숫자에는 아직 출처가 기록되어 있지 않다.",
    askingCaveat: "모집 임대료이므로, 실제로 계약되는 금액은 이보다 낮은 경우가 많다.",
    basis: {
      asking: "모집 임대료",
      contracted: "계약 임대료",
      paid: "실제로 내고 있는 임대료",
    },
    statistic: { median: "중앙값", mean: "평균값" },
    method: {
      "vendor-station-area": "제공처가 역 주변 단위로 집계",
      "radius-800m-weighted": "역에서 800m 안 각 구역의 가중 평균",
      "multi-site-average": "여러 사이트가 공개하는 역별 값의 평균",
      manual: "사람이 정리",
    },
  },
  tags: {
      majorHub: "큰 번화가",
    someBustle: "다소 번화함",
      lively: "북적임",
      quiet: "조용함",
      shoppingEasy: "장 보기 가까움",
      diningRich: "외식할 가게가 많음",
      cafeRich: "카페가 많음",
      lateNight: "밤늦게까지 여는 가게가 있음",
      parkNear: "공원이 가까움",
      flat: "언덕이 없음",
      hilly: "언덕이 많음",
      goodValue: "통근 속도에 비해 임대료가 저렴",
      pricey: "통근 속도에 비해 임대료가 비쌈",
      fastToCenter: "도심까지 빠름",
      manyLines: "노선이 많음",
      singleLine: "노선이 하나뿐",
      floodArea: "침수 예상 구역에 드는 지점이 많음",
      lowFlood: "침수 예상 구역에 드는 지점이 적음",
      familyFriendly: "육아에 맞는 환경",
      singleFriendly: "1인 가구에 맞음",
      medicalRich: "의료기관이 많음",
    },
  exitTags: {
      shoppingStreet: "상점가",
      departmentStore: "대형 상업시설",
      diningCluster: "음식점이 모여 있음",
      barStreet: "술집 거리",
      residential: "주택가",
      quietResidential: "조용한 주택가",
      office: "오피스 거리",
    entertainment: "번화가",
    culture: "미술관·홀",
      school: "학교가 많음",
      park: "공원",
      waterfront: "물가",
      factory: "작은 공장과 창고",
      hospital: "병원",
      uphill: "오르막",
      downhill: "내리막",
    },
  axes: {
    rentValue: "임대료 대비 가치",
    commute: "출퇴근",
    transitConvenience: "환승 편의",
    shopping: "일상 장보기",
    food: "음식점",
    cafe: "카페",
    nightlife: "밤에 여는 가게",
    safety: "치안",
    quietness: "조용함",
    family: "육아",
    singleLife: "1인 생활",
    internationalFriendliness: "외국인이 지내기 좋은 정도",
    style: "동네 분위기",
    nature: "공원과 녹지",
    healthcare: "의료",
    fitness: "헬스장",
    disaster: "침수 예상이 작음",
  },
  grades: {
    excellent: "매우 좋음",
    good: "좋음",
    fair: "보통",
    poor: "약함",
  },
  rentTypes: {
    oneRoom: "원룸(1R)",
    oneK: "1K",
    oneLDK: "1LDK",
    twoLDK: "2LDK",
  },
  presets: {
    balanced: "균형",
    single: "1인 생활",
    family: "가족",
    quiet: "조용함",
    value: "가격 대비",
    international: "외국인 거주자",
  },
  offices: {
    shinjuku: "신주쿠",
    shibuya: "시부야",
    tokyo: "도쿄역",
    shinagawa: "시나가와",
    otemachi: "오테마치",
    toranomon: "도라노몬",
    roppongi: "롯폰기",
  },
  crowdingLevels: {
    1: "여유로움",
    2: "비교적 여유로움",
    3: "보통",
    4: "혼잡",
    5: "매우 혼잡",
  },
};

const DICTIONARIES: Record<ActiveLocale, Dictionary> = {
  ja,
  en,
  "zh-Hans": zhHans,
  ko,
};

export function getDictionary(locale: ActiveLocale): Dictionary {
  return DICTIONARIES[locale];
}
