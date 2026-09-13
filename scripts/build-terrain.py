#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国土地理院の標高APIから、駅ごとの起伏を計算する。

  python3 scripts/build-terrain.py

駅を中心に8方位・半径400mの点と駅の真上、合わせて9点の標高を取り、
その差から「ほぼ平坦／坂がある／起伏が大きい」を決める。

これまで terrain.slope は書き手の印象で書いていた。
標高という測れる値に置き換えることで、根拠のある記述にする（CLAUDE.md ルール35）。

出典: 国土地理院 標高API（https://maps.gsi.go.jp/development/elevation_s.html）
出力: data/computed/terrain.json
"""
import json
import math
import os
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
CACHE = os.path.join(ROOT, "data", "poi", "elevation-cache.json")
OUT = os.path.join(ROOT, "data", "computed", "terrain.json")

API = "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php"
RING_M = 400          # 駅からこの距離の8方位を見る
PAUSE = 0.12          # 連続して叩かないための待ち時間

# 標高差から起伏を決めるしきい値（メートル）。
# 東京23区は台地と低地の差がおよそ20m前後あり、
# 谷筋に駅がある場合は周囲との差が大きく出る。
FLAT_MAX = 8.0
SOME_MAX = 20.0


def offset(lat, lon, bearing_deg, dist_m):
    """指定の方角・距離だけ離れた地点の緯度経度を返す。"""
    r = 6371000.0
    b = math.radians(bearing_deg)
    p1 = math.radians(lat)
    l1 = math.radians(lon)
    p2 = math.asin(math.sin(p1) * math.cos(dist_m / r)
                   + math.cos(p1) * math.sin(dist_m / r) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(dist_m / r) * math.cos(p1),
                         math.cos(dist_m / r) - math.sin(p1) * math.sin(p2))
    return round(math.degrees(p2), 6), round(math.degrees(l2), 6)


def elevation(lat, lon, cache):
    key = f"{lat:.6f},{lon:.6f}"
    if key in cache:
        return cache[key]
    url = f"{API}?lon={lon}&lat={lat}&outtype=JSON"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as res:
                data = json.loads(res.read().decode())
            value = data.get("elevation")
            # 海上など標高が取れない地点は "-----" が返る
            cache[key] = value if isinstance(value, (int, float)) else None
            time.sleep(PAUSE)
            return cache[key]
        except Exception as err:  # noqa: BLE001
            if attempt == 2:
                print(f"    × {key}: {err}")
                cache[key] = None
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def classify(spread):
    if spread is None:
        return None
    if spread < FLAT_MAX:
        return "flat"
    if spread < SOME_MAX:
        return "some"
    return "hilly"


def main():
    stations = json.load(open(ROSTER, encoding="utf-8"))
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)

    out = {}
    for i, st in enumerate(stations, 1):
        points = [(st["lat"], st["lon"])]
        points += [offset(st["lat"], st["lon"], b, RING_M) for b in range(0, 360, 45)]
        values = [elevation(la, lo, cache) for la, lo in points]
        got = [v for v in values if v is not None]
        if len(got) < 5:
            print(f"  [{i}/{len(stations)}] {st['nameJa']}: 標高が取れず、判定しない")
            continue
        station_elev = values[0]
        spread = max(got) - min(got)
        out[st["slug"]] = {
            "slope": classify(spread),
            "stationElevationM": station_elev,
            "minM": round(min(got), 1),
            "maxM": round(max(got), 1),
            "spreadM": round(spread, 1),
            # 駅が周囲より低ければ谷、高ければ台地の上
            "stationIsLow": (station_elev is not None
                             and station_elev - min(got) < spread * 0.3),
        }
        if i % 25 == 0:
            print(f"  [{i}/{len(stations)}] 計算済み")
            json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {
                "source": "国土地理院 標高API",
                "sourceUrl": "https://maps.gsi.go.jp/development/elevation_s.html",
                "method": f"駅と、半径{RING_M}mの8方位、計9点の標高差で判定",
                "thresholds": {"flat": f"< {FLAT_MAX}m",
                               "some": f"{FLAT_MAX}〜{SOME_MAX}m",
                               "hilly": f"≧ {SOME_MAX}m"},
                "retrievedAt": time.strftime("%Y-%m-%d"),
            },
            "stations": out,
        }, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    counts = {}
    for v in out.values():
        counts[v["slope"]] = counts.get(v["slope"], 0) + 1
    print(f"\n{len(out)}/{len(stations)}駅を判定した → data/computed/terrain.json")
    print("  " + " / ".join(f"{k}: {v}駅" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
