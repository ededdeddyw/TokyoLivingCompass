#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国土交通省「重ねるハザードマップ」のタイルから、駅ごとの浸水想定を読み取る。

  python3 scripts/build-hazard.py

洪水浸水想定区域（想定最大規模）の地図タイルを取得し、駅の座標にあたる画素の色から
想定される浸水の深さを判定する。色と深さの対応は国土地理院が公開している凡例による。

災害の記述は、書き方ひとつで読み手の受け取り方が変わる（CLAUDE.md ルール32）。
ここで得られるのは「ハザードマップにそう描かれている」という事実だけで、
危険か安全かの判断ではない。駅ページにもその趣旨の注記を必ず添える。

出典: 重ねるハザードマップ（https://disaportal.gsi.go.jp/）
出力: data/computed/hazard.json
"""
import json
import math
import os
import time
import urllib.request
from collections import Counter

from PIL import Image
import io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
CACHE = os.path.join(ROOT, "data", "poi", "hazard-tiles")
OUT = os.path.join(ROOT, "data", "computed", "hazard.json")

ZOOM = 15
UA = "Mozilla/5.0 (compatible; TokyoLivingCompass/1.0; +hazard lookup)"
PAUSE = 0.3
RING_M = 400   # 駅からこの距離の8方位も見る。駅前だけで判断しないため

LAYERS = {
    "flood": "01_flood_l2_shinsuishin_data",       # 洪水（想定最大規模）
    "hightide": "03_hightide_l2_shinsuishin_data",  # 高潮（想定最大規模）
    "tsunami": "04_tsunami_newlegend_data",         # 津波
}

# 浸水深の凡例（国土地理院）。RGB → 想定される深さ。
DEPTH_BY_RGB = {
    (247, 245, 169): "0.5m未満",
    (255, 216, 192): "0.5〜3m",
    (255, 183, 183): "3〜5m",
    (255, 145, 145): "5〜10m",
    (242, 133, 201): "10〜20m",
    (220, 122, 220): "20m以上",
}
# 実際のタイルは凡例色に近い値で描かれることがあるため、最も近い色に寄せる
LEGEND = list(DEPTH_BY_RGB.items())


def tile_and_pixel(lat, lon, z=ZOOM):
    n = 2 ** z
    fx = (lon + 180.0) / 360.0 * n
    fy = (1.0 - math.log(math.tan(math.radians(lat))
                         + 1 / math.cos(math.radians(lat))) / math.pi) / 2.0 * n
    x, y = int(fx), int(fy)
    return x, y, min(255, int((fx - x) * 256)), min(255, int((fy - y) * 256))


def get_tile(layer, x, y):
    path = os.path.join(CACHE, layer, str(x), f"{y}.png")
    if os.path.exists(path):
        return Image.open(path).convert("RGBA") if os.path.getsize(path) else None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    url = f"https://disaportaldata.gsi.go.jp/raster/{LAYERS[layer]}/{ZOOM}/{x}/{y}.png"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as res:
            body = res.read()
        open(path, "wb").write(body)
        time.sleep(PAUSE)
        return Image.open(io.BytesIO(body)).convert("RGBA")
    except Exception:
        # 想定区域が1つもない範囲のタイルは存在しない。そこは「想定外」を意味する。
        open(path, "wb").close()
        time.sleep(PAUSE)
        return None


def depth_of(rgba):
    r, g, b, a = rgba
    if a < 32:
        return None  # 塗られていない = 想定区域の外
    best, dist = None, 1e9
    for rgb, label in LEGEND:
        d = (r - rgb[0]) ** 2 + (g - rgb[1]) ** 2 + (b - rgb[2]) ** 2
        if d < dist:
            best, dist = label, d
    # 凡例のどの色からも離れていれば、判定しない
    return best if dist <= 3000 else None


def sample(layer, lat, lon):
    """駅の地点と、その周囲8方位を見る。駅前だけで判断しないため。"""
    points = [(lat, lon)]
    for bearing in range(0, 360, 45):
        b = math.radians(bearing)
        dlat = RING_M * math.cos(b) / 111000.0
        dlon = RING_M * math.sin(b) / (111000.0 * math.cos(math.radians(lat)))
        points.append((lat + dlat, lon + dlon))

    found = []
    for la, lo in points:
        x, y, px, py = tile_and_pixel(la, lo)
        im = get_tile(layer, x, y)
        found.append(depth_of(im.getpixel((px, py))) if im else None)
    inside = [f for f in found if f]
    return {
        "atStation": found[0],
        "aroundCount": len(inside),
        "aroundTotal": len(found),
        "deepest": max(inside, key=lambda d: LEGEND_ORDER.index(d)) if inside else None,
    }


LEGEND_ORDER = [lbl for _, lbl in LEGEND]


def main():
    stations = json.load(open(ROSTER, encoding="utf-8"))
    out = {}
    for i, st in enumerate(stations, 1):
        rec = {}
        for layer in LAYERS:
            rec[layer] = sample(layer, st["lat"], st["lon"])
        out[st["slug"]] = rec
        if i % 25 == 0:
            print(f"  [{i}/{len(stations)}] 判定済み")
            json.dump({"meta": META, "stations": out},
                      open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    json.dump({"meta": META, "stations": out},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2, sort_keys=True)
    n = sum(1 for v in out.values() if v["flood"]["aroundCount"])
    print(f"\n{len(out)}駅を判定した。うち洪水の想定区域にかかるのは {n}駅")


META = {
    "source": "重ねるハザードマップ（国土交通省・国土地理院）",
    "sourceUrl": "https://disaportal.gsi.go.jp/",
    "layers": {"flood": "洪水浸水想定区域（想定最大規模）",
               "hightide": "高潮浸水想定区域（想定最大規模）",
               "tsunami": "津波浸水想定"},
    "method": f"ズーム{ZOOM}のタイルから、駅と周囲8方位{RING_M}mの計9点を読み取る",
    "caveat": "地図に描かれている想定を読み取ったものであり、危険・安全の判断ではない。"
              "住所ごとの確認は区のハザードマップで行う。"
              "内水氾濫は全国共通のタイルが公開されていないため、ここには含まれない。",
    "retrievedAt": time.strftime("%Y-%m-%d"),
}

if __name__ == "__main__":
    main()
