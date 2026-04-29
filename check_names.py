import json, sys
sys.stdout.reconfigure(encoding="utf-8")

with open("game_names.json", "r", encoding="utf-8") as f:
    names = json.load(f)

# 从 timeline_data 获取英文名做对照
with open("timeline_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

en_names = {}
for y, yd in data["yearly"].items():
    for g in yd.get("top5", []):
        if g.get("appid"):
            en_names[g["appid"]] = g["name"]
    for g in yd.get("best_by_genre", []):
        if g.get("appid"):
            en_names[g["appid"]] = g["name"]

# 日文名和英文原名相同的
jp_same = []
jp_diff = []
for appid, v in names.items():
    en = en_names.get(int(appid), "")
    jp = v.get("japanese", "")
    if en and jp == en:
        jp_same.append((appid, en))
    else:
        jp_diff.append((appid, en, jp))

print(f"日文名与英文相同: {len(jp_same)}/247")
print(f"日文名有差异（翻译或改写）: {len(jp_diff)}/247")
print()
if jp_same:
    print("日文名与英文相同的游戏:")
    for appid, en in jp_same:
        print(f"  {appid}: {en}")
