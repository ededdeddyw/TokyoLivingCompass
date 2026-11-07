/**
 * 条件で駅を消していく道具（/[locale]/choose）の文言。
 * 量が多いので dictionaries.ts から分け、Dictionary の choose に入れて渡す。
 *
 * 浸水の条件は、何の浸水か・何を前提にした想定かを省かない（CLAUDE.md ルール32・45）。
 * 治安の条件は、警視庁の統計の件数として書き、「危険」「安全」と評価しない。
 */
import type { ActiveLocale } from "./i18n";

export type ChooseText = {
  title: string;
  lead: string;
  homeCta: string;
  remaining: string;
  of: string;
  next: string;
  back: string;
  skip: string;
  showResults: string;
  any: string;
  noOffice: string;
  minutesOption: string;
  transfersOption: string;
  transfersZero: string;
  rentOption: string;
  steps: {
    office: { q: string; note: string };
    minutes: { q: string; note: string };
    transfers: { q: string; note: string };
    rent: { q: string; note: string };
    flood: { q: string; note: string; any: string; deep: string; inZone: string };
    hightide: { q: string; note: string; any: string; inZone: string };
    living: { q: string; note: string; slope: string; lines: string; motorway: string; safety: string };
  };
  results: {
    heading: string;
    conditionsHeading: string;
    noConditions: string;
    relax: string;
    relaxNone: string;
    remove: string;
    edit: string;
    reset: string;
    copy: string;
    copied: string;
    empty: string;
    unknownLabel: string;
    commuteValue: string;
    walkValue: string;
    rentValue: string;
    rentMissing: string;
    sortedByCommute: string;
    sortedByOverall: string;
  };
  /** 結果の画面に出す、条件の札の文言。{n} などは値に置き換える */
  chips: {
    commute: string;
    transfers: string;
    transfersZero: string;
    rent: string;
    floodDeep: string;
    floodInZone: string;
    hightide: string;
    slope: string;
    lines: string;
    motorway: string;
    safety: string;
  };
  /** 「判定できない条件」に出す短い名前 */
  unknownNames: Record<
    "commute" | "transfers" | "rent" | "flood" | "hightide" | "slope" | "lines" | "motorway" | "safety",
    string
  >;
  hazardNote: string;
};

const ja: ChooseText = {
  title: "条件に合わない駅を消していく",
  lead: "「この条件の駅は困る」という条件を1つずつ選ぶと、合わない駅が消えていきます。選ぶたびに、残りの駅数が変わります。",
  homeCta: "困る条件から駅を絞る",
  remaining: "残り{n}駅",
  of: "（{total}駅のうち）",
  next: "次へ",
  back: "戻る",
  skip: "この質問は飛ばす",
  showResults: "残った駅を見る",
  any: "問わない",
  noOffice: "決まっていない・通勤しない",
  minutesOption: "{n}分まで",
  transfersOption: "{n}回まで",
  transfersZero: "乗り換えなし",
  rentOption: "{n}万円まで",
  steps: {
    office: {
      q: "どこへ通勤しますか",
      note: "いちばん近いオフィス街を選んでください。次の2つの質問で、通勤時間と乗り換えの上限を決めます。",
    },
    minutes: {
      q: "通勤時間は何分までなら続けられますか",
      note: "電車に乗っている時間の目安です。駅まで歩く時間と、ホームで待つ時間は入っていません。",
    },
    transfers: {
      q: "乗り換えは何回までなら続けられますか",
      note: "直通運転で乗り換えずに行ける場合は、乗り換えに数えていません。",
    },
    rent: {
      q: "家賃はいくらまでですか",
      note: "駅のまわりの家賃相場の帯の上限で判定します。相場が出ていない駅は消さずに残し、判定できない条件として示します。",
    },
    flood: {
      q: "大雨のときの浸水の想定を、どこまで気にしますか",
      note: "駅の地点の想定で判定します。住む住所の想定は、駅から少し離れるだけで変わります。",
      any: "気にしない",
      deep: "駅の地点の想定が3m以上の駅は外す",
      inZone: "駅の地点が浸水想定区域に入る駅は外す",
    },
    hightide: {
      q: "高潮のときの浸水の想定を、気にしますか",
      note: "台風などで海面が高くなったときの想定です。駅の地点で判定します。",
      any: "気にしない",
      inZone: "駅の地点が高潮の浸水想定区域に入る駅は外す",
    },
    living: {
      q: "暮らしの中で、困ることはありますか",
      note: "当てはまるものをすべて選んでください。選ばなければ、その条件では消しません。",
      slope: "坂が多い駅は困る",
      lines: "使える路線が1本だけの駅は困る（止まったときにほかの路線へ逃げられない）",
      motorway: "駅から歩いて3分ほどの範囲に高速道路が通る駅は困る（車の音が昼も夜も続く）",
      safety: "警視庁の統計で、粗暴犯・凶悪犯・侵入窃盗の件数が多いほうの2割の駅は外したい",
    },
  },
  results: {
    heading: "条件に合う駅",
    conditionsHeading: "選んだ条件",
    noConditions: "まだ条件を選んでいません。",
    relax: "外すと{n}駅戻ります",
    relaxNone: "外しても戻る駅はありません",
    remove: "この条件を外す",
    edit: "質問からやり直す",
    reset: "条件をすべて外す",
    copy: "この条件のURLをコピー",
    copied: "コピーしました",
    empty: "条件に合う駅がありません。上の条件のうち、外すと戻る駅の多いものからゆるめてみてください。",
    unknownLabel: "判定できない条件",
    commuteValue: "{office}へ{minutes}分・乗り換え{transfers}回",
    walkValue: "{office}へ歩いて{minutes}分",
    rentValue: "{type}{low}万〜{high}万円",
    rentMissing: "{type}の相場は出ていません",
    sortedByCommute: "通勤時間の短い順に並べています。",
    sortedByOverall: "すべての評価軸を均等に見た総合評価の高い順に並べています。",
  },
  chips: {
    commute: "{office}へ{n}分以内",
    transfers: "乗り換え{n}回以内",
    transfersZero: "乗り換えなし",
    rent: "{type}の家賃相場が{n}万円以下",
    floodDeep: "大雨のときの浸水の想定が3m以上の駅を外す",
    floodInZone: "大雨のときの浸水想定区域に入る駅を外す",
    hightide: "高潮の浸水想定区域に入る駅を外す",
    slope: "坂が多い駅を外す",
    lines: "路線が1本だけの駅を外す",
    motorway: "高速道路が近い駅を外す",
    safety: "粗暴犯などの件数が多いほうの2割を外す",
  },
  unknownNames: {
    commute: "通勤時間",
    transfers: "乗り換え",
    rent: "家賃",
    flood: "大雨のときの浸水",
    hightide: "高潮",
    slope: "坂",
    lines: "路線",
    motorway: "高速道路",
    safety: "治安",
  },
  hazardNote:
    "浸水想定区域は、区のハザードマップにもとづく、想定しうる最大規模の雨や高潮を前提にした試算です。住む住所が決まったら、区のハザードマップで確かめてください。",
};

const en: ChooseText = {
  title: "Rule out stations that don't work for you",
  lead: "Pick the conditions you can't live with, one at a time, and stations that fail them drop out. The count of remaining stations updates as you go.",
  homeCta: "Narrow down by deal-breakers",
  remaining: "{n} stations left",
  of: " (of {total})",
  next: "Next",
  back: "Back",
  skip: "Skip this question",
  showResults: "See remaining stations",
  any: "Doesn't matter",
  noOffice: "Not decided / no commute",
  minutesOption: "Up to {n} min",
  transfersOption: "Up to {n}",
  transfersZero: "No transfers",
  rentOption: "Up to ¥{n}0,000",
  steps: {
    office: {
      q: "Where do you commute to?",
      note: "Choose the nearest business district. The next two questions set limits on travel time and transfers.",
    },
    minutes: {
      q: "How long a commute can you keep up?",
      note: "Approximate time on the train. Walking to the station and waiting on the platform are not included.",
    },
    transfers: {
      q: "How many transfers can you keep up?",
      note: "Through services that let you stay on the same train are not counted as transfers.",
    },
    rent: {
      q: "What is your rent budget?",
      note: "Judged by the upper end of the local rent range. Stations without a rent range are kept and marked as not judged.",
    },
    flood: {
      q: "How much do heavy-rain flood projections matter to you?",
      note: "Judged at the station itself. Projections for your actual address can differ a short walk away.",
      any: "Doesn't matter",
      deep: "Exclude stations projected to flood 3 m or deeper",
      inZone: "Exclude stations inside a projected flood zone",
    },
    hightide: {
      q: "Do storm-surge flood projections matter to you?",
      note: "Projections for when typhoons raise the sea level. Judged at the station itself.",
      any: "Doesn't matter",
      inZone: "Exclude stations inside a projected storm-surge flood zone",
    },
    living: {
      q: "Anything else you can't live with?",
      note: "Select all that apply. Unselected items are not used to rule stations out.",
      slope: "Lots of hills",
      lines: "Only one line (no other line to fall back on when it stops)",
      motorway: "An expressway within about 3 minutes' walk (traffic noise day and night)",
      safety: "In the top 20% for violent crime, serious crime and burglary in Tokyo police statistics",
    },
  },
  results: {
    heading: "Stations that pass",
    conditionsHeading: "Your conditions",
    noConditions: "No conditions selected yet.",
    relax: "Removing this brings back {n}",
    relaxNone: "Removing this brings none back",
    remove: "Remove this condition",
    edit: "Start the questions again",
    reset: "Clear all conditions",
    copy: "Copy link to these conditions",
    copied: "Copied",
    empty: "No station passes. Try relaxing the condition that brings back the most stations.",
    unknownLabel: "Not judged",
    commuteValue: "{minutes} min to {office}, {transfers} transfer(s)",
    walkValue: "{minutes} min walk to {office}",
    rentValue: "{type} ¥{low}0,000–{high}0,000",
    rentMissing: "No {type} rent range",
    sortedByCommute: "Sorted by shortest commute.",
    sortedByOverall: "Sorted by overall score with all criteria weighted equally.",
  },
  chips: {
    commute: "Within {n} min of {office}",
    transfers: "Up to {n} transfer(s)",
    transfersZero: "No transfers",
    rent: "{type} rent up to ¥{n}0,000",
    floodDeep: "Exclude heavy-rain flood projections of 3 m or more",
    floodInZone: "Exclude heavy-rain flood zones",
    hightide: "Exclude storm-surge flood zones",
    slope: "Exclude hilly stations",
    lines: "Exclude single-line stations",
    motorway: "Exclude stations near an expressway",
    safety: "Exclude the top 20% for violent crime and similar",
  },
  unknownNames: {
    commute: "commute",
    transfers: "transfers",
    rent: "rent",
    flood: "heavy-rain flooding",
    hightide: "storm surge",
    slope: "hills",
    lines: "lines",
    motorway: "expressway",
    safety: "crime",
  },
  hazardNote:
    "Projected flood zones come from the wards' hazard maps and assume the largest conceivable rainfall or storm surge. Once you have an address, check it on the ward's hazard map.",
};

const zhHans: ChooseText = {
  title: "排除不合适的车站",
  lead: "逐个选择“这种车站我不能接受”的条件，不符合的车站就会被排除。每选一项，剩余车站数都会更新。",
  homeCta: "按不能接受的条件筛选车站",
  remaining: "剩余{n}个车站",
  of: "（共{total}个）",
  next: "下一步",
  back: "返回",
  skip: "跳过此问题",
  showResults: "查看剩余车站",
  any: "不限",
  noOffice: "未定・不通勤",
  minutesOption: "{n}分钟以内",
  transfersOption: "{n}次以内",
  transfersZero: "不换乘",
  rentOption: "{n}万日元以内",
  steps: {
    office: {
      q: "您去哪里通勤？",
      note: "请选择最近的办公区。接下来的两个问题将设定通勤时间和换乘次数的上限。",
    },
    minutes: {
      q: "通勤时间最多可以接受多少分钟？",
      note: "乘车时间的大致值，不包括步行到车站和在站台等车的时间。",
    },
    transfers: {
      q: "最多可以接受换乘几次？",
      note: "通过直通运行无需换乘的情况，不计为换乘。",
    },
    rent: {
      q: "房租预算是多少？",
      note: "以车站周边房租行情区间的上限来判断。没有行情数据的车站不会被排除，而是标记为无法判断。",
    },
    flood: {
      q: "您有多在意大雨时的浸水预测？",
      note: "以车站所在地点的预测来判断。实际住址的预测，离车站稍远一点就可能不同。",
      any: "不在意",
      deep: "排除车站地点预测浸水3米以上的车站",
      inZone: "排除车站地点位于浸水预测区域内的车站",
    },
    hightide: {
      q: "您在意高潮时的浸水预测吗？",
      note: "台风等导致海平面升高时的预测。以车站所在地点来判断。",
      any: "不在意",
      inZone: "排除车站地点位于高潮浸水预测区域内的车站",
    },
    living: {
      q: "生活中还有不能接受的情况吗？",
      note: "请选择所有符合的项目。未选择的项目不会用于排除车站。",
      slope: "坡道多",
      lines: "只有1条线路（停运时无法改乘其他线路）",
      motorway: "步行约3分钟范围内有高速公路（昼夜都有车声）",
      safety: "根据警视厅统计，暴力犯罪・凶恶犯罪・入室盗窃件数较多的前20%",
    },
  },
  results: {
    heading: "符合条件的车站",
    conditionsHeading: "已选条件",
    noConditions: "尚未选择条件。",
    relax: "去掉此条件可恢复{n}个车站",
    relaxNone: "去掉此条件也不会恢复车站",
    remove: "去掉此条件",
    edit: "重新回答问题",
    reset: "清除所有条件",
    copy: "复制此条件的链接",
    copied: "已复制",
    empty: "没有符合条件的车站。请从上面去掉后恢复车站最多的条件开始放宽。",
    unknownLabel: "无法判断的条件",
    commuteValue: "到{office}{minutes}分钟・换乘{transfers}次",
    walkValue: "步行到{office}{minutes}分钟",
    rentValue: "{type}{low}万〜{high}万日元",
    rentMissing: "没有{type}的房租行情",
    sortedByCommute: "按通勤时间从短到长排列。",
    sortedByOverall: "按各评价项目平均计算的综合评价从高到低排列。",
  },
  chips: {
    commute: "到{office}{n}分钟以内",
    transfers: "换乘{n}次以内",
    transfersZero: "不换乘",
    rent: "{type}房租行情{n}万日元以下",
    floodDeep: "排除大雨浸水预测3米以上的车站",
    floodInZone: "排除位于大雨浸水预测区域的车站",
    hightide: "排除位于高潮浸水预测区域的车站",
    slope: "排除坡道多的车站",
    lines: "排除只有1条线路的车站",
    motorway: "排除靠近高速公路的车站",
    safety: "排除暴力犯罪等件数较多的前20%",
  },
  unknownNames: {
    commute: "通勤时间",
    transfers: "换乘",
    rent: "房租",
    flood: "大雨浸水",
    hightide: "高潮",
    slope: "坡道",
    lines: "线路",
    motorway: "高速公路",
    safety: "治安",
  },
  hazardNote:
    "浸水预测区域根据各区的灾害地图，以可设想的最大规模降雨或高潮为前提进行估算。确定住址后，请在区的灾害地图上确认。",
};

const ko: ChooseText = {
  title: "조건에 맞지 않는 역 지워 나가기",
  lead: "\"이런 역은 곤란하다\"는 조건을 하나씩 고르면 맞지 않는 역이 사라집니다. 고를 때마다 남은 역의 수가 바뀝니다.",
  homeCta: "곤란한 조건으로 역 좁히기",
  remaining: "남은 역 {n}곳",
  of: " ({total}곳 중)",
  next: "다음",
  back: "이전",
  skip: "이 질문은 건너뛰기",
  showResults: "남은 역 보기",
  any: "상관없음",
  noOffice: "정하지 않음・통근하지 않음",
  minutesOption: "{n}분까지",
  transfersOption: "{n}회까지",
  transfersZero: "환승 없음",
  rentOption: "{n}만 엔까지",
  steps: {
    office: {
      q: "어디로 통근합니까?",
      note: "가장 가까운 오피스 지역을 고르세요. 다음 두 질문에서 통근 시간과 환승 횟수의 상한을 정합니다.",
    },
    minutes: {
      q: "통근 시간은 몇 분까지 계속할 수 있습니까?",
      note: "전철에 타고 있는 시간의 기준입니다. 역까지 걷는 시간과 승강장에서 기다리는 시간은 포함하지 않습니다.",
    },
    transfers: {
      q: "환승은 몇 번까지 계속할 수 있습니까?",
      note: "직통 운전으로 갈아타지 않고 갈 수 있는 경우는 환승으로 세지 않습니다.",
    },
    rent: {
      q: "월세는 얼마까지입니까?",
      note: "역 주변 월세 시세 범위의 상한으로 판정합니다. 시세가 없는 역은 지우지 않고, 판정할 수 없는 조건으로 표시합니다.",
    },
    flood: {
      q: "폭우 때의 침수 상정을 어느 정도 신경 씁니까?",
      note: "역 지점의 상정으로 판정합니다. 실제 주소의 상정은 역에서 조금만 떨어져도 달라집니다.",
      any: "신경 쓰지 않음",
      deep: "역 지점의 상정이 3m 이상인 역은 제외",
      inZone: "역 지점이 침수 상정 구역에 들어가는 역은 제외",
    },
    hightide: {
      q: "해일(고조) 때의 침수 상정을 신경 씁니까?",
      note: "태풍 등으로 해수면이 높아졌을 때의 상정입니다. 역 지점으로 판정합니다.",
      any: "신경 쓰지 않음",
      inZone: "역 지점이 고조 침수 상정 구역에 들어가는 역은 제외",
    },
    living: {
      q: "생활하면서 곤란한 것이 있습니까?",
      note: "해당하는 것을 모두 고르세요. 고르지 않은 조건으로는 지우지 않습니다.",
      slope: "언덕이 많은 역은 곤란",
      lines: "이용할 수 있는 노선이 1개뿐인 역은 곤란(멈췄을 때 다른 노선으로 갈 수 없음)",
      motorway: "역에서 걸어서 3분 정도 범위에 고속도로가 지나는 역은 곤란(차 소리가 밤낮으로 이어짐)",
      safety: "경시청 통계에서 폭력범・흉악범・침입 절도 건수가 많은 상위 20%의 역은 제외",
    },
  },
  results: {
    heading: "조건에 맞는 역",
    conditionsHeading: "고른 조건",
    noConditions: "아직 조건을 고르지 않았습니다.",
    relax: "빼면 {n}곳이 돌아옵니다",
    relaxNone: "빼도 돌아오는 역이 없습니다",
    remove: "이 조건 빼기",
    edit: "질문부터 다시 하기",
    reset: "조건 모두 빼기",
    copy: "이 조건의 URL 복사",
    copied: "복사했습니다",
    empty: "조건에 맞는 역이 없습니다. 위의 조건 중 빼면 돌아오는 역이 많은 것부터 완화해 보세요.",
    unknownLabel: "판정할 수 없는 조건",
    commuteValue: "{office}까지 {minutes}분・환승 {transfers}회",
    walkValue: "{office}까지 걸어서 {minutes}분",
    rentValue: "{type} {low}만〜{high}만 엔",
    rentMissing: "{type} 시세가 없습니다",
    sortedByCommute: "통근 시간이 짧은 순으로 나열했습니다.",
    sortedByOverall: "모든 평가 항목을 균등하게 본 종합 평가가 높은 순으로 나열했습니다.",
  },
  chips: {
    commute: "{office}까지 {n}분 이내",
    transfers: "환승 {n}회 이내",
    transfersZero: "환승 없음",
    rent: "{type} 월세 시세 {n}만 엔 이하",
    floodDeep: "폭우 침수 상정 3m 이상인 역 제외",
    floodInZone: "폭우 침수 상정 구역에 들어가는 역 제외",
    hightide: "고조 침수 상정 구역에 들어가는 역 제외",
    slope: "언덕이 많은 역 제외",
    lines: "노선이 1개뿐인 역 제외",
    motorway: "고속도로가 가까운 역 제외",
    safety: "폭력범 등 건수가 많은 상위 20% 제외",
  },
  unknownNames: {
    commute: "통근 시간",
    transfers: "환승",
    rent: "월세",
    flood: "폭우 침수",
    hightide: "고조",
    slope: "언덕",
    lines: "노선",
    motorway: "고속도로",
    safety: "치안",
  },
  hazardNote:
    "침수 상정 구역은 각 구의 해저드 맵에 따른, 상정할 수 있는 최대 규모의 비나 고조를 전제로 한 추산입니다. 살 주소가 정해지면 구의 해저드 맵에서 확인하세요.",
};

export const CHOOSE_TEXT: Record<ActiveLocale, ChooseText> = { ja, en, "zh-Hans": zhHans, ko };
