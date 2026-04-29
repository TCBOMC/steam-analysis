"""
Steam时代编年史 - 数据分析脚本 v2
按年份切分数据，生成：偏好画像、词云数据、推荐排名、跨时间趋势
"""

import pandas as pd
import numpy as np
from scipy import stats
from collections import Counter
import json
import re
import warnings
warnings.filterwarnings('ignore')


from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# 游戏专用停用词（通用列表不覆盖的领域高频词）
GAME_STOP_WORDS = {
    # 通用游戏词
    "game", "games", "gameplay", "play", "playing", "player", "players",
    "steam", "action", "adventure", "features", "feature", "include",
    "includes", "including", "experience", "control", "controls", "level",
    "levels", "based", "version", "available", "supports", "yourself",
    "system", "mode", "person", "become", "becomes",
    # 营销套话 / 文本高频填充词（无区分度）
    "unique", "original", "classic", "realistic", "story", "stories",
    "new", "world", "time", "like", "fun", "key", "explore", "enemies",
    "life", "war", "different", "way", "make", "use", "just", "characters",
    "battle", "take", "find", "set", "need", "best", "real", "full",
    "various", "help", "after", "while", "turn", "choose", "put", "get",
    "go", "going", "come", "many", "much", "well", "back", "still",
    "even", "now", "long", "great", "little", "own", "got", "made",
    "around", "across", "through", "things", "something", "everything",
    "anything", "nothing", "thing", "know", "think", "good", "want",
    "give", "day", "days", "look", "looking", "see", "work", "works",
    "keep", "start", "started", "right", "left", "high", "low", "big",
    "small", "old", "young", "man", "men", "people", "place", "places",
    "part", "parts", "hand", "hands", "point", "points", "build",
    "builds", "building", "run", "running", "try", "tried", "trying",
    # 游戏描述万能填充词（无区分度）
    "combat", "friends", "character", "fight", "items", "powerful", "weapons", "unlock",

}

ALL_STOP = set(ENGLISH_STOP_WORDS) | GAME_STOP_WORDS


def extract_words(text, min_len=3):
    """从英文文本中提取关键词（去除停用词、HTML标签、短词）"""
    if not text or not isinstance(text, str) or len(text) < 10:
        return []
    # 去除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 只保留字母和空格
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    words = text.lower().split()
    return [w for w in words if w not in ALL_STOP and len(w) >= min_len]


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, (np.bool_,)): return bool(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)


# ============================================================
# 数据加载与清洗（JSON 格式）
# ============================================================
df = pd.read_json(
    r"C:\Users\TRSEIMC\.cache\kagglehub\datasets\fronkongames\steam-games-dataset\versions\31\games.json",
    orient="index"
)
# 重置索引，使 AppID 成为一列
df = df.reset_index().rename(columns={"index": "appid"})

df["total_reviews"] = df["positive"] + df["negative"]
df["positive_ratio"] = df["positive"] / df["total_reviews"]
df = df[df["total_reviews"] >= 50].copy()
df["release_date"] = pd.to_datetime(df["release_date"], format="%b %d, %Y", errors="coerce")
df["year"] = df["release_date"].dt.year
df = df.dropna(subset=["year"]).copy()
# genre：JSON 中是列表，取第一个；空列表或 NaN 归为 Other
def get_main_genre(g):
    if isinstance(g, list) and len(g) > 0:
        return g[0]
    return "Other"
df["main_genre"] = df["genres"].apply(get_main_genre)
# average_playtime 别名
df["average_playtime"] = df["average_playtime_forever"]
df["median_playtime"] = df["average_playtime_forever"]

def owners_mid(s):
    parts = str(s).split("-")
    if len(parts) == 2:
        return (int(parts[0]) + int(parts[1])) / 2
    return int(s)
df["owners_mid"] = df["estimated_owners"].apply(owners_mid)
df = df[df["price"] <= 200].copy()

df.rename(columns={"positive": "positive_ratings", "negative": "negative_ratings"}, inplace=True)

print(f"有效数据: {df.shape[0]} 款游戏, 年份 {int(df['year'].min())}-{int(df['year'].max())}")

# ============================================================
# 按年份生成全部数据
# ============================================================
# 起始年份：2006年以前的游戏评价数极少（被50条筛选过滤掉了），从2006开始
YEAR_MIN = 2006
YEAR_MAX = int(df["year"].max())
all_years = list(range(YEAR_MIN, YEAR_MAX + 1))

# 全局数据（用于归一化）
global_price_median = df["price"].median()
global_playtime_median = df["average_playtime"].median()
global_reviews_median = df["total_reviews"].median()

yearly_data = {}

for year in all_years:
    dy = df[df["year"] == year].copy()
    if len(dy) < 10:
        continue

    n = len(dy)

    # ---- 基本指标 ----
    key_metrics = {
        "n_games": n,
        "avg_price": round(float(dy["price"].mean()), 2),
        "median_price": round(float(dy["price"].median()), 2),
        "avg_positive_ratio": round(float(dy["positive_ratio"].mean()) * 100, 1),
        "median_positive_ratio": round(float(dy["positive_ratio"].median()) * 100, 1),
        "avg_playtime": round(float(dy["average_playtime"].mean()), 1),
        "median_playtime": round(float(dy["median_playtime"].median()), 1),
        "avg_reviews": round(float(dy["total_reviews"].mean()), 0),
        "total_reviews": int(dy["total_reviews"].sum()),
        "avg_owners": round(float(dy["owners_mid"].mean()), 0),
    }

    # ---- 类型分布 ----
    genre_counts = dy["main_genre"].value_counts().head(15)
    genre_dist = {g: int(c) for g, c in genre_counts.items()}

    # 各类型好评率
    genre_ratings = {}
    for g in genre_dist:
        grp = dy[dy["main_genre"] == g]["positive_ratio"]
        genre_ratings[g] = {
            "mean": round(float(grp.mean()) * 100, 1),
            "median": round(float(grp.median()) * 100, 1),
            "n": int(len(grp)),
        }

    # ---- 价格分布 ----
    price_bins = [0, 5, 10, 15, 20, 30, 50, 200]
    price_hist, _ = np.histogram(dy["price"], bins=price_bins)
    price_labels = ["免费-5", "5-10", "10-15", "15-20", "20-30", "30-50", "50+"]
    price_dist = {price_labels[i]: int(price_hist[i]) for i in range(len(price_labels))}

    # 各价格区间好评率
    price_ratings = {}
    for label, lo, hi in zip(price_labels, price_bins[:-1], price_bins[1:]):
        grp = dy[(dy["price"] >= lo) & (dy["price"] < hi)]["positive_ratio"]
        if len(grp) >= 5:
            price_ratings[label] = round(float(grp.mean()) * 100, 1)

    # ---- 词云数据：标签 + 简介关键词 + 评测关键词 ----
    tag_counter = Counter()   # Steam 标签（原始投票权重）
    text_counter = Counter()  # 文本关键词（来自描述/评测）

    # 标签
    for tags_dict in dy["tags"].dropna():
        if isinstance(tags_dict, dict):
            for tag, w in tags_dict.items():
                tag = tag.strip()
                if tag and len(tag) >= 2:
                    tag_counter[tag] += int(w)

    # 文本关键词：合并 short_description + about_the_game + reviews
    for text in dy["short_description"].dropna():
        for w in extract_words(text):
            text_counter[w] += 2  # 简介词权重 ×2
    for text in dy["about_the_game"].dropna():
        for w in extract_words(text):
            text_counter[w] += 1
    for text in dy["reviews"].dropna():
        for w in extract_words(text):
            text_counter[w] += 3  # 评测词权重 ×3

    # 归一化合并：标签和文本各自取 TOP80，然后分别归一化到 [0, 100] 再合并
    # 这样标签的投票数和文本的出现次数不会互相压制
    top_tags_raw = tag_counter.most_common(80)
    top_text_raw = text_counter.most_common(80)

    def normalize(counter_raw):
        if not counter_raw:
            return []
        max_val = max(v for _, v in counter_raw)
        if max_val == 0:
            return [(w, 0) for w, _ in counter_raw]
        return [(w, round(v / max_val * 100)) for w, v in counter_raw]

    norm_tags = normalize(top_tags_raw)
    norm_text = normalize(top_text_raw)

    # 合并：标签词 ×0.5 + 文本词 ×1.0（文本词权重更高，更有参考价值）
    merged = Counter()
    for w, v in norm_tags:
        merged[w] += v * 0.5
    for w, v in norm_text:
        # 如果该词已经是标签词，额外加成（标签+文本同时出现说明特别重要）
        if w in dict(norm_tags):
            merged[w] += v * 0.5  # 标签已有 0.5，再加 0.5 使其在合并后总权重 = 1.0
        else:
            merged[w] += v * 1.0

    top_tags = merged.most_common(80)
    # 构建原始计数映射（标签 + 文本合并）
    raw_counts = Counter()
    for w, v in top_tags_raw:
        raw_counts[w] += v
    for w, v in top_text_raw:
        raw_counts[w] += v
    wordcloud_data = [{"word": t, "value": round(c), "count": raw_counts[t]} for t, c in top_tags]

    # ---- 游玩时长分布 ----
    playtime_bins = [0, 1, 5, 20, 50, 200]
    playtime_hist, _ = np.histogram(dy["average_playtime"], bins=playtime_bins)
    playtime_labels = ["<1h", "1-5h", "5-20h", "20-50h", "50h+"]
    playtime_dist = {playtime_labels[i]: int(playtime_hist[i]) for i in range(len(playtime_labels))}

    # ---- 推荐算法 ----
    # 综合得分 = 0.30×好评率 + 0.30×热度 + 0.20×游玩深度 + 0.10×价格合理 + 0.10×影响力
    # 核心思路：好评率代表质量，热度代表声量，两者结合才是"真正受欢迎"
    def compute_score(row, year_data):
        # 好评率：直接标准化到0-100
        score_rating = float(row["positive_ratio"]) * 100

        # 热度：log(评论数)归一化，评论越多=越多人关注
        max_log_reviews = np.log1p(dy["total_reviews"].max())
        score_popularity = (np.log1p(row["total_reviews"]) / max_log_reviews) * 100 if max_log_reviews > 0 else 0

        # 游玩深度：平均游玩时长归一化，玩得久=粘性强
        max_playtime = dy["average_playtime"].max()
        score_depth = (float(row["average_playtime"]) / max_playtime * 100) if max_playtime > 0 else 0

        # 价格合理性：当年中位数附近得分最高
        year_median = dy["price"].median()
        if year_median > 0:
            price_dev = abs(float(row["price"]) - year_median) / year_median
            score_price = max(100 - price_dev * 40, 0)
        else:
            score_price = 50

        # 影响力：拥有者数量归一化，反映玩家基数
        max_owners = dy["owners_mid"].max()
        score_impact = (float(row["owners_mid"]) / max_owners * 100) if max_owners > 0 else 0

        total = (0.30 * score_rating + 0.30 * score_popularity + 0.20 * score_depth +
                 0.10 * score_price + 0.10 * score_impact)
        return round(total, 2)

    dy = dy.copy()
    dy["score"] = dy.apply(lambda r: compute_score(r, yearly_data), axis=1)

    # TOP 5 综合
    top5 = dy.nlargest(5, "score")[["appid", "name", "main_genre", "price", "positive_ratio", "total_reviews", "average_playtime", "score"]].reset_index(drop=True)
    top5_list = []
    for _, r in top5.iterrows():
        top5_list.append({
            "rank": int(len(top5_list)) + 1,
            "appid": int(r["appid"]),
            "name": r["name"],
            "genre": r["main_genre"],
            "price": round(float(r["price"]), 2),
            "positive_ratio": round(float(r["positive_ratio"]) * 100, 1),
            "reviews": int(r["total_reviews"]),
            "playtime": round(float(r["average_playtime"]), 1),
            "score": round(float(r["score"]), 1),
        })

    # 每类型最佳（仅取当年有5款以上的类型）
    best_by_genre = []
    for g, cnt in genre_dist.items():
        if cnt < 5:
            continue
        grp = dy[dy["main_genre"] == g]
        best = grp.loc[grp["score"].idxmax()]
        best_by_genre.append({
            "appid": int(best["appid"]),
            "genre": g,
            "name": best["name"],
            "score": round(float(best["score"]), 1),
            "positive_ratio": round(float(best["positive_ratio"]) * 100, 1),
            "price": round(float(best["price"]), 2),
            "n_in_genre": cnt,
        })
    best_by_genre.sort(key=lambda x: x["score"], reverse=True)

    # ---- 偏好画像 ----
    # 最火类型
    top_genre = genre_counts.index[0]
    # 偏好价位
    best_price_range = max(price_ratings, key=price_ratings.get) if price_ratings else "未知"
    best_price_rating = max(price_ratings.values()) if price_ratings else 0
    # 最长游玩类型
    genre_playtime = {}
    for g in genre_dist:
        grp = dy[dy["main_genre"] == g]["average_playtime"]
        if len(grp) >= 3:
            genre_playtime[g] = float(grp.mean())
    longest_genre = max(genre_playtime, key=genre_playtime.get) if genre_playtime else "未知"

    # 好评率趋势（与前一年对比）
    prev_year_data = df[df["year"] == year - 1]["positive_ratio"]
    trend = "—"
    if len(prev_year_data) >= 10:
        prev_mean = prev_year_data.mean()
        curr_mean = dy["positive_ratio"].mean()
        diff = (curr_mean - prev_mean) / prev_mean * 100
        if diff > 2:
            trend = f"↑ 较上年提升{abs(diff):.1f}%"
        elif diff < -2:
            trend = f"↓ 较上年下降{abs(diff):.1f}%"
        else:
            trend = "→ 与上年持平"

    # 最受欢迎标签
    top3_tags = [t for t, _ in top_tags[:3]]

    profile = {
        "top_genre": top_genre,
        "top_genre_count": int(genre_counts[top_genre]),
        "top_genre_pct": round(float(genre_counts[top_genre] / n * 100), 1),
        "preferred_price_range": best_price_range,
        "preferred_price_rating": best_price_rating,
        "longest_playtime_genre": longest_genre,
        "longest_playtime_hours": round(genre_playtime.get(longest_genre, 0), 1),
        "trend": trend,
        "top_tags": top3_tags,
    }

    # ---- 结论生成 ----
    conclusions = [
        f"{year}年共上架{n}款游戏，整体好评率中位数{key_metrics['median_positive_ratio']}%",
        f"最受欢迎的类型是{top_genre}，占当年游戏的{profile['top_genre_pct']}%",
        f"玩家最偏好的价格区间为${best_price_range}，该区间好评率{best_price_rating}%",
        f"平均游玩时长最长的类型是{longest_genre}（{profile['longest_playtime_hours']}小时）",
        f"当年最热门的游戏标签：{top3_tags[0]}、{top3_tags[1]}、{top3_tags[2]}",
        f"好评率整体趋势：{trend}",
    ]
    if top5_list:
        conclusions.append(f"综合推荐TOP1：{top5_list[0]['name']}（{top5_list[0]['genre']}，好评率{top5_list[0]['positive_ratio']}%，评分{top5_list[0]['score']}）")

    yearly_data[str(year)] = {
        "year": year,
        "metrics": key_metrics,
        "genre_distribution": genre_dist,
        "genre_ratings": genre_ratings,
        "price_distribution": price_dist,
        "price_ratings": price_ratings,
        "wordcloud": wordcloud_data,
        "playtime_distribution": playtime_dist,
        "top5": top5_list,
        "best_by_genre": best_by_genre,
        "profile": profile,
        "conclusions": conclusions,
    }

# ============================================================
# 跨时间趋势数据
# ============================================================
trend_data = {
    "years": all_years,
    "n_games": [yearly_data.get(str(y), {}).get("metrics", {}).get("n_games", 0) for y in all_years],
    "median_price": [yearly_data.get(str(y), {}).get("metrics", {}).get("median_price", 0) for y in all_years],
    "median_positive_ratio": [yearly_data.get(str(y), {}).get("metrics", {}).get("median_positive_ratio", 0) for y in all_years],
    "avg_playtime": [yearly_data.get(str(y), {}).get("metrics", {}).get("avg_playtime", 0) for y in all_years],
}

# 主要类型的时间趋势
all_genres = set()
for yd in yearly_data.values():
    if yd:
        all_genres.update(yd["genre_distribution"].keys())
# 取出现年份>=5的类型
genre_freq = Counter()
for yd in yearly_data.values():
    if yd:
        for g in yd["genre_distribution"]:
            genre_freq[g] += 1
major_genres = sorted([g for g, c in genre_freq.items() if c >= 5])[:10]

genre_trend = {}
for g in major_genres:
    genre_trend[g] = [yearly_data.get(str(y), {}).get("genre_distribution", {}).get(g, 0) for y in all_years]

# 每类型好评率时间趋势
genre_rating_trend = {}
for g in major_genres:
    genre_rating_trend[g] = [yearly_data.get(str(y), {}).get("genre_ratings", {}).get(g, {}).get("mean", None) for y in all_years]

trend_data["major_genres"] = major_genres
trend_data["genre_count_trend"] = genre_trend
trend_data["genre_rating_trend"] = genre_rating_trend

# ============================================================
# 附录表格
# ============================================================
# 各年份汇总表
yearly_summary = []
for y in all_years:
    yd = yearly_data.get(str(y))
    if not yd:
        continue
    m = yd["metrics"]
    p = yd["profile"]
    yearly_summary.append({
        "year": y,
        "n_games": m["n_games"],
        "median_price": m["median_price"],
        "median_positive_ratio": m["median_positive_ratio"],
        "avg_playtime": m["avg_playtime"],
        "total_reviews": m["total_reviews"],
        "top_genre": p["top_genre"],
        "top_genre_pct": p["top_genre_pct"],
        "preferred_price": p["preferred_price_range"],
        "trend": p["trend"],
        "top1_game": yd["top5"][0]["name"] if yd["top5"] else "",
        "top1_score": yd["top5"][0]["score"] if yd["top5"] else 0,
        "top1_appid": yd["top5"][0]["appid"] if yd["top5"] else 0,
    })

# 算法说明
algorithm_desc = {
    "name": "Steam时代综合推荐算法",
    "formula": "综合得分 = 0.30×好评率 + 0.30×热度 + 0.20×游玩深度 + 0.10×价格合理 + 0.10×影响力",
    "weights": [
        {"factor": "好评率", "weight": 0.30, "desc": "玩家好评比例，直接标准化到0-100"},
        {"factor": "热度指数", "weight": 0.30, "desc": "log(评价数)归一化，反映玩家关注度与讨论度"},
        {"factor": "游玩深度", "weight": 0.20, "desc": "平均游玩时长归一化，反映游戏粘性与质量"},
        {"factor": "价格合理性", "weight": 0.10, "desc": "距离当年中位数越近得分越高，反映价格接受度"},
        {"factor": "影响力", "weight": 0.10, "desc": "拥有者数量归一化，反映玩家基数"},
    ],
    "note": "好评率和热度各占30%权重，确保推荐结果同时体现游戏质量和声量。每个年份独立计算，反映当时的玩家偏好。",
}

# ============================================================
# 保存
# ============================================================
output = {
    "yearly": yearly_data,
    "trends": trend_data,
    "yearly_summary": yearly_summary,
    "algorithm": algorithm_desc,
    "year_range": [YEAR_MIN, YEAR_MAX],
}

with open("timeline_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)

print(f"\n完成! timeline_data.json ({len(json.dumps(output, ensure_ascii=False)) // 1024} KB)")
print(f"年份范围: {YEAR_MIN}-{YEAR_MAX}")
print(f"有效年份: {[y for y in all_years if yearly_data.get(str(y))]}")

# 验证
for y in [2014, 2015, 2016, 2017]:
    yd = yearly_data.get(str(y))
    if yd:
        print(f"\n--- {y}年 ---")
        print(f"  游戏数: {yd['metrics']['n_games']}")
        print(f"  TOP1: {yd['top5'][0]['name']} (score={yd['top5'][0]['score']})")
        print(f"  词云TOP5: {[w['word'] for w in yd['wordcloud'][:5]]}")
        print(f"  结论: {yd['conclusions'][0]}")
