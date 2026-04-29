"""预取 Steam 游戏的多语言名称，保存为 game_names.json

策略：逐个请求 store.steampowered.com/api/appdetails，
通过 Clash 代理访问，带重试机制。
"""
import json
import time
import requests
import sys
import os

# 代理配置（通过本地 Clash 代理访问 Steam）
PROXY = os.environ.get("HTTPS_PROXY", "http://127.0.0.1:7897")
PROXIES = {"http": PROXY, "https": PROXY}

LANGS = ["schinese", "japanese"]
API_URL = "https://store.steampowered.com/api/appdetails?appids={appid}&l={lang}&cc=us"
MAX_RETRIES = 3
RETRY_DELAY = 3
REQUEST_DELAY = 1.0  # 逐个请求之间的间隔

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

# 从 timeline_data.json 收集所有需要翻译的 appid
with open(os.path.join(DATA_DIR, "timeline_data.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

appids = set()
for y, yd in data["yearly"].items():
    for g in yd.get("top5", []):
        if g.get("appid"):
            appids.add(g["appid"])
    for g in yd.get("best_by_genre", []):
        if g.get("appid"):
            appids.add(g["appid"])

# 也加上年度 summary 的 top1
for y, yd in data["yearly"].items():
    top1 = yd.get("top1_appid")
    if top1:
        appids.add(top1)

appids = sorted(appids)
print(f"共 {len(appids)} 个唯一 appid 需要获取翻译名称")
print(f"代理: {PROXY}")

names = {}  # {appid_str: {schinese: "...", japanese: "..."}}

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json",
})
session.proxies = PROXIES

def fetch_one(appid, lang):
    """请求单个游戏的单语种名称，带重试"""
    url = API_URL.format(appid=appid, lang=lang)
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 200:
                j = resp.json()
                app_data = j.get(str(appid), {})
                if app_data.get("success") and app_data.get("data"):
                    return app_data["data"].get("name", "")
                return ""  # success=false, 游戏不存在或区域锁
            elif resp.status_code == 429:
                # 被限速，等更久
                wait = RETRY_DELAY * (attempt + 2)
                print(f"    429 限速，等待 {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                return ""
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (attempt + 1)
                print(f"    连接错误，{wait}s 后重试 ({attempt+1}/{MAX_RETRIES}): {type(e).__name__}", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"    最终失败: {type(e).__name__}", file=sys.stderr)
                return ""
    return ""

# 逐个请求每个 appid
total = len(appids)
start_time = time.time()

for i, appid in enumerate(appids):
    appid_str = str(appid)
    if appid_str not in names:
        names[appid_str] = {}

    for lang in LANGS:
        name = fetch_one(appid, lang)
        if name:
            names[appid_str][lang] = name

    # 进度
    done = i + 1
    if done % 10 == 0 or done == total:
        elapsed = time.time() - start_time
        rate = done / elapsed if elapsed > 0 else 0
        cn = sum(1 for v in names.values() if "schinese" in v)
        jp = sum(1 for v in names.values() if "japanese" in v)
        print(f"  进度: {done}/{total} ({done*100//total}%) | 中文名: {cn} | 日文名: {jp} | {rate:.1f}个/s")

    time.sleep(REQUEST_DELAY)

elapsed = time.time() - start_time
has_cn = sum(1 for v in names.values() if "schinese" in v)
has_jp = sum(1 for v in names.values() if "japanese" in v)
missing = [a for a in appids if str(a) not in names or not names[str(a)]]
print(f"\n完成! 耗时 {elapsed:.1f}s")
print(f"  共 {total} 个游戏")
print(f"  中文名: {has_cn}/{total}")
print(f"  日文名: {has_jp}/{total}")
if missing:
    print(f"  完全缺失: {missing[:20]}{'...' if len(missing) > 20 else ''}")

with open(os.path.join(DATA_DIR, "game_names.json"), "w", encoding="utf-8") as f:
    json.dump(names, f, ensure_ascii=False, indent=2)

sz = len(json.dumps(names, ensure_ascii=False))
print(f"data/game_names.json ({sz // 1024} KB)")
