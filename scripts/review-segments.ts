/**
 * 8区分それぞれの上位駅を並べて、人が目で確かめるための一覧を出す。
 *
 * 区分ごとの順位は重みつき平均と足切りで決まる（src/lib/scoring.ts の
 * rankBySegment、docs/14-audience-segments.md §3.1）。機械の判定が
 * 街の実態と合っているかは、人が駅名を見ないと分からない。
 *
 * 足切りで後ろへ回した駅のうち、点数が高かったものも併せて出す。
 * 落としてはいけない駅を落としていないかを確かめるためである。
 *
 *   npm run --silent review:segments > out.md
 */
import { rankBySegment, axisFloors } from "../src/lib/scoring";
import { SEGMENT_GATES, SEGMENT_KEYS, splitSegment } from "../src/lib/weights";
import type { ScoreAxis } from "../src/lib/schema";
import { getAllStations } from "../src/lib/stations";
import { getDictionary } from "../src/lib/dictionaries";

const TOP = 20;
const GATED_SHOWN = 8;

const dict = getDictionary("ja");
const stations = getAllStations();
const floors = axisFloors(stations);

const label = (key: string) => {
  const sides = splitSegment(key as never);
  if (!sides) return dict.balancedLabel;
  return [sides.household, sides.night, sides.money]
    .map((o) => dict.segmentOptions[o])
    .join(" × ");
};

const axisName = (axis: ScoreAxis) => dict.axes[axis];

const yen = (v?: number) => (v === undefined ? "—" : `${(v / 10000).toFixed(1)}万`);

const COLUMNS: ScoreAxis[] = [
  "rentLow",
  "commute",
  "safety",
  "quietness",
  "family",
  "nightlife",
  "singleLife",
];

const out: string[] = [];
out.push("# 8区分の上位駅（目で確かめるための一覧）");
out.push("");
out.push(
  "`npm run --silent review:segments` が出力する。区分ごとの重みと足切りは " +
    "docs/14-audience-segments.md §3.1 にある。",
);
out.push("");
out.push("足切りの境目（軸ごとに、スコアが入っている駅の下から3割の位置）:");
out.push("");
out.push("| 軸 | 境目 |");
out.push("|---|---|");
for (const axis of new Set(Object.values(SEGMENT_GATES))) {
  out.push(`| ${axisName(axis)} | ${floors[axis] ?? "—"} |`);
}
out.push("");

for (const key of SEGMENT_KEYS) {
  const ranked = rankBySegment(stations, key);
  const passed = ranked.filter((r) => r.gatedBy.length === 0);
  const gated = ranked.filter((r) => r.gatedBy.length > 0);

  out.push("---");
  out.push("");
  out.push(`## ${label(key)}`);
  out.push("");
  out.push(
    `足切りを通った駅 ${passed.length} / 後ろへ回した駅 ${gated.length}（\`?view=${key}\`）`,
  );
  out.push("");
  out.push(
    `| # | 駅 | 区 | 総合 | ワンルーム | ${COLUMNS.map(axisName).join(" | ")} |`,
  );
  out.push(`|---|---|---|---|---|${COLUMNS.map(() => "---").join("|")}|`);
  passed.slice(0, TOP).forEach((r, i) => {
    const s = r.station;
    const cells = COLUMNS.map((a) => s.scores[a] ?? "—").join(" | ");
    out.push(
      `| ${i + 1} | ${s.nameJa} | ${s.wardNameJa} | ${r.overall?.toFixed(1) ?? "—"} | ` +
        `${yen(s.rent?.oneRoom)} | ${cells} |`,
    );
  });
  out.push("");
  out.push(`**足切りで後ろへ回した駅のうち、点数が高かった${GATED_SHOWN}駅**`);
  out.push("");
  out.push("| 駅 | 総合 | 引っかかった軸と点 |");
  out.push("|---|---|---|");
  gated
    .slice(0, GATED_SHOWN)
    .forEach((r) =>
      out.push(
        `| ${r.station.nameJa} | ${r.overall?.toFixed(1) ?? "—"} | ` +
          r.gatedBy
            .map((a) => `${axisName(a)} ${r.station.scores[a]}（境目 ${floors[a]}）`)
            .join("、") +
          " |",
      ),
    );
  out.push("");
}

console.log(out.join("\n"));
