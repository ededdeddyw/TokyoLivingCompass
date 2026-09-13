#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenStreetMap から、駅の周辺施設（スーパー・病院・クリニック・薬局・公園）を取得する。

  python3 scripts/fetch-pois.py            # 未取得のタイルだけ取る
  python3 scripts/fetch-pois.py --refresh  # 取得済みも取り直す

駅ごとに問い合わせると448回になり、Overpass のサーバーに負担をかける。
そこで対象範囲をタイルに分けて一度だけ取得し、駅への割り当ては手元で計算する。

出力:
  data/poi/raw/<タイル>.json   Overpass の生の応答（キャッシュ）
  data/computed/pois.json      駅ごとに、半径800m以内の施設と徒歩分数

データは OpenStreetMap（ODbL）による。店名をここから取ることで、
書き手の記憶ではなく実在するデータに紐づけられる（CLAUDE.md ルール35）。
"""
import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
RAW_DIR = os.path.join(ROOT, "data", "poi", "raw")  # 束ごとに枝分かれする
OUT_FILE = os.path.join(ROOT, "data", "computed", "pois.json")

# 公開ミラー。上から順に試し、落ちていれば次へ回す。
# 応答の速さと安定を実測して並べた。落ちていれば次のミラーへ回す。
# 送るのは緯度経度の範囲だけで、リポジトリの内容は送らない。
ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

# 取得する施設。キーが分類名、値が Overpass のタグ条件。
# 一度に全部を問い合わせると Overpass が時間切れになるため、2つの束に分ける。
# 束ごとにキャッシュの置き場を分け、あとで重ねて使う。
GROUPS = {
    "life": {
        "supermarket": ['["shop"="supermarket"]'],
        "hospital": ['["amenity"="hospital"]'],
        "clinic": ['["amenity"="clinic"]', '["amenity"="doctors"]'],
        "pharmacy": ['["amenity"="pharmacy"]'],
        "park": ['["leisure"="park"]'],
    },
    "food": {
        "restaurant": ['["amenity"="restaurant"]'],
        "cafe": ['["amenity"="cafe"]'],
        "bar": ['["amenity"="bar"]', '["amenity"="pub"]'],
        "gym": ['["leisure"="fitness_centre"]'],
    },
}
CATEGORIES = {k: v for g in GROUPS.values() for k, v in g.items()}

# 施設の種類で「周辺」と呼べる距離が違う。スーパーは歩いて通う距離、
# 総合病院は自転車や電車で行く距離で見る。
RADIUS_BY_CATEGORY = {
    "supermarket": 800,
    "clinic": 800,
    "pharmacy": 800,
    "restaurant": 800,
    "cafe": 800,
    "bar": 800,
    "gym": 1000,
    "park": 1200,
    "hospital": 2500,
}
RADIUS_M = max(RADIUS_BY_CATEGORY.values())
DETOUR = 1.3            # 直線距離に対する実際の歩行距離の見込み
WALK_M_PER_MIN = 80.0   # 不動産表示の慣行（徒歩1分＝80m）
TILE_DEG = 0.08         # タイルの一辺（緯度経度）
PAUSE_SEC = 5.0         # 連続して叩かないための待ち時間


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def walk_minutes(distance_m):
    """直線距離から徒歩分数を見積もる。実際の道のりは直線より長いので割り増す。"""
    return max(1, math.ceil(distance_m * DETOUR / WALK_M_PER_MIN))


def tiles(stations):
    """駅の分布を覆うタイルを作る。端の駅が欠けないよう余白を足す。"""
    lats = [s["lat"] for s in stations]
    lons = [s["lon"] for s in stations]
    margin = RADIUS_M / 111000.0 + 0.01  # 最も遠い種類（総合病院）に合わせる
    lat0, lat1 = min(lats) - margin, max(lats) + margin
    lon0, lon1 = min(lons) - margin, max(lons) + margin
    out = []
    lat = lat0
    while lat < lat1:
        lon = lon0
        while lon < lon1:
            out.append((round(lat, 4), round(lon, 4),
                        round(min(lat + TILE_DEG, lat1), 4),
                        round(min(lon + TILE_DEG, lon1), 4)))
            lon += TILE_DEG
        lat += TILE_DEG
    return out


def build_query(bbox, group):
    s, w, n, e = bbox
    box = f"({s},{w},{n},{e})"
    parts = []
    for filters in GROUPS[group].values():
        for f in filters:
            parts.append(f"node{f}{box};")
            parts.append(f"way{f}{box};")
    return "[out:json][timeout:120];(" + "".join(parts) + ");out center tags;"


def fetch(query):
    """ミラーを順に試す。すべて落ちていれば None を返す。"""
    last = None
    for ep in ENDPOINTS:
        try:
            req = urllib.request.Request(
                ep,
                data=urllib.parse.urlencode({"data": query}).encode(),
                headers={"User-Agent": "TokyoLivingCompass/1.0 (station POI collection)"},
            )
            with urllib.request.urlopen(req, timeout=180) as res:
                return json.loads(res.read().decode())
        except Exception as err:  # noqa: BLE001 — ミラーごとに落ち方が違う
            last = f"{ep}: {err}"
            print(f"    × {last}")
            time.sleep(PAUSE_SEC)
    print(f"    どのミラーも応答しなかった: {last}")
    return None


def fetch_box(box, group, depth=0):
    """
    1つの範囲を取る。施設が多い範囲は Overpass が時間切れになるので、
    落ちたら4つに割って取り直す。分割して取った結果はつなげて返す。
    """
    data = fetch(build_query(box, group))
    if data is not None:
        return data
    if depth >= 2:
        raise SystemExit(f"分割しても取得できなかった: {box}")
    s, w, n, e = box
    mlat, mlon = (s + n) / 2, (w + e) / 2
    print(f"    範囲を4分割して取り直す（{depth + 1}回目）")
    merged = []
    for sub in ((s, w, mlat, mlon), (s, mlon, mlat, e),
                (mlat, w, n, mlon), (mlat, mlon, n, e)):
        merged.extend(fetch_box(tuple(round(v, 4) for v in sub), group, depth + 1)["elements"])
        time.sleep(PAUSE_SEC)
    return {"elements": merged}


def category_of(tags):
    if tags.get("shop") == "supermarket":
        return "supermarket"
    a = tags.get("amenity")
    if a == "hospital":
        return "hospital"
    if a in ("clinic", "doctors"):
        return "clinic"
    if a == "pharmacy":
        return "pharmacy"
    if a in ("restaurant", "cafe", "bar", "pub"):
        return "bar" if a in ("bar", "pub") else a
    if tags.get("leisure") == "park":
        return "park"
    if tags.get("leisure") == "fitness_centre":
        return "gym"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="取得済みのタイルも取り直す")
    args = ap.parse_args()

    stations = json.load(open(ROSTER, encoding="utf-8"))
    os.makedirs(RAW_DIR, exist_ok=True)

    boxes = tiles(stations)
    print(f"{len(stations)}駅を {len(boxes)} タイルで覆う")

    elements = []
    for group in GROUPS:
      for i, box in enumerate(boxes, 1):
        name = "_".join(str(v).replace("-", "m") for v in box) + ".json"
        path = os.path.join(RAW_DIR, group, name) if group != "life" else os.path.join(RAW_DIR, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path) and not args.refresh:
            data = json.load(open(path, encoding="utf-8"))
            print(f"  [{group} {i}/{len(boxes)}] キャッシュ {len(data['elements'])}件")
        else:
            print(f"  [{group} {i}/{len(boxes)}] 取得中 {box}")
            data = fetch_box(box, group)
            json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"    {len(data['elements'])}件")
            time.sleep(PAUSE_SEC)
        elements.extend(data["elements"])

    # 重複（タイルの境界にまたがるもの）を取り除く
    seen = set()
    pois = []
    for el in elements:
        key = (el["type"], el["id"])
        if key in seen:
            continue
        seen.add(key)
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # 名前のない施設は載せられない
        # 閉店した店が名前だけ残っていることがある（「文化堂跡」など）。
        # 実在しない店を載せるのが最も重い失敗なので、疑わしいものは落とす。
        if any(w in name for w in ("跡", "閉店", "跡地", "旧")):
            continue
        if any(k.startswith(("disused:", "was:", "abandoned:")) for k in tags):
            continue
        # OSM は支店名を branch に分けて持つことがある。あれば店名に足す。
        branch = tags.get("branch")
        if branch and branch not in name:
            name = f"{name} {branch}"
        cat = category_of(tags)
        if not cat:
            continue
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        pois.append({
            "osmType": el["type"], "osmId": el["id"], "name": name,
            "category": cat, "lat": lat, "lon": lon,
            "brand": tags.get("brand"),
            "openingHours": tags.get("opening_hours"),
        })
    print(f"名前つきの施設: {len(pois)}件")

    # 駅ごとに半径内の施設を割り当て、近い順に並べる
    out = {}
    for st in stations:
        near = []
        for p in pois:
            limit = RADIUS_BY_CATEGORY[p["category"]]
            d = haversine_m(st["lat"], st["lon"], p["lat"], p["lon"])
            if d <= limit:
                near.append({**p, "distanceM": round(d),
                             "walkMinutes": walk_minutes(d)})
        near.sort(key=lambda x: x["distanceM"])
        if near:
            out[st["slug"]] = near

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {
                "source": "OpenStreetMap contributors (ODbL)",
                "radiusByCategory": RADIUS_BY_CATEGORY,
                "walkModel": f"直線距離 × {DETOUR} ÷ 分速{int(WALK_M_PER_MIN)}m、切り上げ",
                "retrievedAt": time.strftime("%Y-%m-%d"),
            },
            "stations": out,
        }, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    covered = len(out)
    print(f"\n{covered}/{len(stations)}駅に施設を割り当てた → data/computed/pois.json")


if __name__ == "__main__":
    main()
