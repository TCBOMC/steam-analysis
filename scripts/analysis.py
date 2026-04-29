"""
Steam游戏评分影响因素统计探索 - 数据分析与JSON生成
生成5个模块的数据文件，供前端ECharts可视化使用
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import ttest_ind, f_oneway, pearsonr, spearmanr
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
import json
import warnings
warnings.filterwarnings('ignore')

# 自定义JSON编码器处理numpy类型
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# ============================================================
# 1. 数据加载与清洗
# ============================================================
df = pd.read_csv("steam_store_games.csv")
print(f"原始数据: {df.shape[0]} 行, {df.shape[1]} 列")

# 计算好评率
df["total_reviews"] = df["positive_ratings"] + df["negative_ratings"]
df["positive_ratio"] = df["positive_ratings"] / df["total_reviews"]

# 筛选条件：评价数>=50
df = df[df["total_reviews"] >= 50].copy()
print(f"筛选后(评价>=50): {df.shape[0]} 行")

# 解析日期
df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
df["year"] = df["release_date"].dt.year
df["month"] = df["release_date"].dt.month
df["game_age"] = 2024 - df["year"]  # 游戏年龄（到2024年）

# 提取主类型（取第一个genre）
df["main_genre"] = df["genres"].apply(lambda x: x.split(";")[0] if pd.notna(x) else "Unknown")

# owners字段取中值
def owners_to_mid(s):
    parts = str(s).split("-")
    if len(parts) == 2:
        return (int(parts[0]) + int(parts[1])) / 2
    return int(s)
df["owners_mid"] = df["owners"].apply(owners_to_mid)

# 排除极端价格
df = df[df["price"] <= 200].copy()

print(f"最终数据: {df.shape[0]} 行")
print(f"年份范围: {df['year'].min()} - {df['year'].max()}")

# ============================================================
# 2. 模块1: 描述性统计
# ============================================================
print("\n=== 模块1: 描述性统计 ===")

# 关键指标
key_metrics = {
    "total_games": int(df.shape[0]),
    "avg_price": round(float(df["price"].mean()), 2),
    "median_price": round(float(df["price"].median()), 2),
    "avg_positive_ratio": round(float(df["positive_ratio"].mean()) * 100, 1),
    "median_positive_ratio": round(float(df["positive_ratio"].median()) * 100, 1),
    "avg_playtime": round(float(df["average_playtime"].mean()), 1),
    "median_playtime": round(float(df["median_playtime"].median()), 1),
    "avg_reviews": round(float(df["total_reviews"].mean()), 0),
    "std_price": round(float(df["price"].std()), 2),
    "skew_price": round(float(df["price"].skew()), 2),
    "std_positive_ratio": round(float(df["positive_ratio"].std()) * 100, 1),
}

# 每年游戏数量
yearly = df.groupby("year").size().reset_index(name="count")
yearly = yearly[(yearly["year"] >= 2005) & (yearly["year"] <= 2024)]
yearly_counts = [{"year": int(r["year"]), "count": int(r["count"])} for _, r in yearly.iterrows()]

# 价格分布（直方图数据）
price_bins = [0, 5, 10, 15, 20, 30, 40, 60, 200]
price_hist, _ = np.histogram(df["price"], bins=price_bins)
price_labels = ["$0-5", "$5-10", "$10-15", "$15-20", "$20-30", "$30-40", "$40-60", "$60-200"]
price_distribution = [{"range": price_labels[i], "count": int(price_hist[i])} for i in range(len(price_labels))]

# 好评率分布
ratio_bins = np.arange(0, 1.05, 0.05)
ratio_hist, _ = np.histogram(df["positive_ratio"], bins=ratio_bins)
ratio_labels = [f"{int(ratio_bins[i]*100)}-{int(ratio_bins[i+1]*100)}%" for i in range(len(ratio_bins)-1)]
ratio_distribution = [{"range": ratio_labels[i], "count": int(ratio_hist[i])} for i in range(len(ratio_labels))]

# 类型分布
genre_counts = df["main_genre"].value_counts().head(12)
genre_distribution = [{"genre": g, "count": int(c)} for g, c in genre_counts.items()]

# 价格-好评率散点图（采样3000点用于展示）
scatter_sample = df[["price", "positive_ratio", "main_genre", "name"]].sample(
    min(3000, len(df)), random_state=42
)
scatter_data = [
    {
        "price": round(float(r["price"]), 2),
        "positive_ratio": round(float(r["positive_ratio"]) * 100, 1),
        "genre": r["main_genre"],
        "name": r["name"]
    }
    for _, r in scatter_sample.iterrows()
]

module1_data = {
    "key_metrics": key_metrics,
    "yearly_counts": yearly_counts,
    "price_distribution": price_distribution,
    "ratio_distribution": ratio_distribution,
    "genre_distribution": genre_distribution,
    "scatter_sample": scatter_data,
}

with open("data_module1_descriptive.json", "w", encoding="utf-8") as f:
    json.dump(module1_data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
print("  -> data_module1_descriptive.json saved")

# ============================================================
# 3. 模块2: 假设检验 - 独立游戏 vs 大厂游戏
# ============================================================
print("\n=== 模块2: 假设检验 ===")

# 判断大厂：同一开发者发布游戏数>=N
dev_counts = df.groupby("developer").size().reset_index(name="game_count")
df = df.merge(dev_counts, on="developer", how="left")

# 对不同阈值计算t检验
threshold_results = []
for threshold in [2, 3, 5, 7, 10, 15, 20]:
    indie = df[df["game_count"] < threshold]["positive_ratio"]
    major = df[df["game_count"] >= threshold]["positive_ratio"]

    if len(indie) < 30 or len(major) < 30:
        continue

    t_stat, p_value = ttest_ind(major, indie, equal_var=False)
    cohens_d = (major.mean() - indie.mean()) / np.sqrt(
        ((len(major)-1)*major.std()**2 + (len(indie)-1)*indie.std()**2) / (len(major)+len(indie)-2)
    )

    threshold_results.append({
        "threshold": threshold,
        "indie_n": int(len(indie)),
        "major_n": int(len(major)),
        "indie_mean": round(float(indie.mean() * 100), 1),
        "major_mean": round(float(major.mean() * 100), 1),
        "indie_std": round(float(indie.std() * 100), 1),
        "major_std": round(float(major.std() * 100), 1),
        "t_statistic": round(float(t_stat), 3),
        "p_value": round(float(p_value), 4),
        "cohens_d": round(float(cohens_d), 3),
        "significant": p_value < 0.05,
    })

# 用默认阈值(5)做详细分析
default_threshold = 5
indie = df[df["game_count"] < default_threshold]
major = df[df["game_count"] >= default_threshold]

# 箱线图数据（按百分位数）
def box_stats(series):
    q1, q25, median, q75, q99 = np.percentile(series, [1, 25, 50, 75, 99])
    return {
        "min": round(float(q1), 3),
        "q1": round(float(q25), 3),
        "median": round(float(median), 3),
        "q3": round(float(q75), 3),
        "max": round(float(q99), 3),
        "mean": round(float(series.mean()), 3),
        "std": round(float(series.std()), 3),
        "n": int(len(series)),
    }

box_data = {
    "indie": box_stats(indie["positive_ratio"]),
    "major": box_stats(major["positive_ratio"]),
}

module2_data = {
    "threshold_results": threshold_results,
    "default_threshold": default_threshold,
    "box_data": box_data,
    "hypothesis": {
        "h0": "独立游戏与大厂游戏的好评率均值无显著差异",
        "h1": "独立游戏与大厂游戏的好评率均值存在显著差异",
        "method": "Welch's t-test (双样本t检验，不假设等方差)",
    }
}

with open("data_module2_hypothesis.json", "w", encoding="utf-8") as f:
    json.dump(module2_data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
print("  -> data_module2_hypothesis.json saved")

# ============================================================
# 4. 模块3: 相关与回归分析
# ============================================================
print("\n=== 模块3: 相关与回归 ===")

# 选择自变量
features = ["price", "game_age", "average_playtime", "total_reviews"]
feature_labels = {
    "price": "价格",
    "game_age": "游戏年龄(年)",
    "average_playtime": "平均游玩时长(小时)",
    "total_reviews": "评价总数",
}

# 相关系数矩阵
corr_vars = ["price", "game_age", "average_playtime", "total_reviews", "positive_ratio"]
corr_labels = ["价格", "游戏年龄", "游玩时长", "评价总数", "好评率"]
corr_matrix = df[corr_vars].corr()
corr_data = {
    "variables": corr_labels,
    "matrix": [[round(float(corr_matrix.iloc[i, j]), 3) for j in range(len(corr_vars))] for i in range(len(corr_vars))]
}

# Pearson和Spearman相关
pearson_results = []
spearman_results = []
for var in features:
    mask = df[var].notna() & df["positive_ratio"].notna()
    r_p, p_p = pearsonr(df.loc[mask, var], df.loc[mask, "positive_ratio"])
    r_s, p_s = spearmanr(df.loc[mask, var], df.loc[mask, "positive_ratio"])
    pearson_results.append({"variable": feature_labels[var], "r": round(float(r_p), 3), "p_value": round(float(p_p), 4)})
    spearman_results.append({"variable": feature_labels[var], "rho": round(float(r_s), 3), "p_value": round(float(p_s), 4)})

# 多重线性回归
df_reg = df[features + ["positive_ratio"]].dropna().copy()
df_reg["log_reviews"] = np.log1p(df_reg["total_reviews"])  # log变换
X_vars = ["price", "game_age", "average_playtime", "log_reviews"]
var_labels_cn = ["价格", "游戏年龄", "游玩时长", "log(评价数)"]

X = df_reg[X_vars].values
y = df_reg["positive_ratio"].values

model = LinearRegression()
model.fit(X, y)

# 手动计算统计量
y_pred = model.predict(X)
residuals = y - y_pred
n = len(y)
p = len(X_vars)
r_squared = model.score(X, y)
adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p - 1)

# F检验
ss_reg = np.sum((y_pred - y.mean()) ** 2)
ss_res = np.sum(residuals ** 2)
ms_reg = ss_reg / p
ms_res = ss_res / (n - p - 1)
f_stat = ms_reg / ms_res
f_p_value = 1 - stats.f.cdf(f_stat, p, n - p - 1)

# 系数标准误和t检验
X_with_intercept = np.column_stack([np.ones(n), X])
try:
    from statsmodels.regression.linear_model import OLS
    import statsmodels.api as sm
    sm_model = sm.OLS(y, X_with_intercept).fit()
    coef_std_errors = sm_model.bse.tolist()
    coef_pvalues = sm_model.pvalues.tolist()
    coef_ci = [(round(float(sm_model.conf_int()[i, 0]), 4), round(float(sm_model.conf_int()[i, 1]), 4)) for i in range(len(sm_model.params))]
except:
    # 手动计算
    XtX_inv = np.linalg.inv(X_with_intercept.T @ X_with_intercept)
    mse = ss_res / (n - p - 1)
    coef_std_errors = np.sqrt(np.diag(XtX_inv) * mse).tolist()
    coef_t = (sm_model.params / np.sqrt(np.diag(XtX_inv) * mse))
    coef_pvalues = [2 * (1 - stats.t.cdf(abs(t), n - p - 1)) for t in coef_t]
    coef_ci = []

coef_names = ["截距"] + var_labels_cn
coefficients = []
for i, name in enumerate(coef_names):
    coefficients.append({
        "name": name,
        "coefficient": round(float(sm_model.params[i]) * 100, 2) if i > 0 else round(float(sm_model.params[i]), 4),
        "std_error": round(float(sm_model.bse[i]) * 100, 2) if i > 0 else round(float(sm_model.bse[i]), 4),
        "p_value": round(float(sm_model.pvalues[i]), 4),
        "ci_lower": round(float(sm_model.conf_int()[i, 0]) * 100, 2) if i > 0 else round(float(sm_model.conf_int()[i, 0]), 4),
        "ci_upper": round(float(sm_model.conf_int()[i, 1]) * 100, 2) if i > 0 else round(float(sm_model.conf_int()[i, 1]), 4),
        "significant": sm_model.pvalues[i] < 0.05,
    })

# 散点图数据（采样）
scatter_pairs = {}
for var in features:
    mask = df[var].notna()
    sample = df[mask].sample(min(1500, mask.sum()), random_state=42)
    scatter_pairs[var] = [
        {"x": round(float(r[var]), 2), "y": round(float(r["positive_ratio"]) * 100, 1), "name": r["name"]}
        for _, r in sample.iterrows()
    ]

module3_data = {
    "correlation_matrix": corr_data,
    "pearson": pearson_results,
    "spearman": spearman_results,
    "regression": {
        "r_squared": round(float(r_squared), 4),
        "adj_r_squared": round(float(adj_r_squared), 4),
        "f_statistic": round(float(f_stat), 2),
        "f_p_value": round(float(f_p_value), 6),
        "n": int(n),
        "coefficients": coefficients,
    },
    "scatter_pairs": scatter_pairs,
}

with open("data_module3_correlation.json", "w", encoding="utf-8") as f:
    json.dump(module3_data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
print("  -> data_module3_correlation.json saved")

# ============================================================
# 5. 模块4: ANOVA - 不同类型评分差异
# ============================================================
print("\n=== 模块4: ANOVA ===")

# 选样本量>=100的类型
genre_counts_filtered = df["main_genre"].value_counts()
major_genres = genre_counts_filtered[genre_counts_filtered >= 100].index.tolist()
df_anova = df[df["main_genre"].isin(major_genres)].copy()

# 各组统计
genre_stats = {}
for genre in sorted(major_genres):
    group = df_anova[df_anova["main_genre"] == genre]["positive_ratio"]
    genre_stats[genre] = {
        "n": int(len(group)),
        "mean": round(float(group.mean() * 100), 1),
        "std": round(float(group.std() * 100), 1),
        "median": round(float(group.median() * 100), 1),
    }

# 单因素ANOVA
groups = [df_anova[df_anova["main_genre"] == g]["positive_ratio"].values for g in sorted(major_genres)]
f_stat_anova, p_value_anova = f_oneway(*groups)

# Tukey HSD
tukey_data = pairwise_tukeyhsd(
    df_anova["positive_ratio"],
    df_anova["main_genre"],
    alpha=0.05
)

# 提取显著差异对
tukey_pairs = []
genres_sorted = sorted(major_genres)
genre_idx = {g: i for i, g in enumerate(genres_sorted)}

# 构建Tukey矩阵
tukey_matrix = [[0]*len(genres_sorted) for _ in range(len(genres_sorted))]
for i in range(len(tukey_data.groupsunique)):
    for j in range(i+1, len(tukey_data.groupsunique)):
        g1 = tukey_data.groupsunique[i]
        g2 = tukey_data.groupsunique[j]
        # 找到对应的p值
        idx = 0
        count = 0
        for ii in range(len(tukey_data.groupsunique)):
            for jj in range(ii+1, len(tukey_data.groupsunique)):
                if ii == i and jj == j:
                    break
                count += 1
            else:
                continue
            break
        # 直接从reject中获取
        for k in range(len(tukey_data.reject)):
            pair = tukey_data._results_table.data[k+1]
            if (pair[0] == g1 and pair[1] == g2) or (pair[0] == g2 and pair[1] == g1):
                p_val = float(pair[3])
                reject = bool(pair[5] == "True")
                i1 = genres_sorted.index(g1) if g1 in genres_sorted else -1
                i2 = genres_sorted.index(g2) if g2 in genres_sorted else -1
                if i1 >= 0 and i2 >= 0:
                    tukey_matrix[i1][i2] = round(p_val, 4)
                    tukey_matrix[i2][i1] = round(p_val, 4)
                tukey_pairs.append({
                    "group1": g1, "group2": g2,
                    "mean_diff": round(float(pair[2]) * 100, 1),
                    "p_value": round(p_val, 4),
                    "reject": reject,
                })
                break

# 箱线图数据
genre_box_data = {}
for genre in sorted(major_genres):
    group = df_anova[df_anova["main_genre"] == genre]["positive_ratio"]
    q1, q25, median, q75, q99 = np.percentile(group, [1, 25, 50, 75, 99])
    genre_box_data[genre] = {
        "min": round(float(q1) * 100, 1),
        "q1": round(float(q25) * 100, 1),
        "median": round(float(median) * 100, 1),
        "q3": round(float(q75) * 100, 1),
        "max": round(float(q99) * 100, 1),
    }

module4_data = {
    "genres": genres_sorted,
    "genre_stats": genre_stats,
    "anova": {
        "f_statistic": round(float(f_stat_anova), 2),
        "p_value": round(float(p_value_anova), 6),
        "significant": p_value_anova < 0.05,
    },
    "tukey_pairs": tukey_pairs,
    "tukey_matrix": {"genres": genres_sorted, "matrix": tukey_matrix},
    "genre_box_data": genre_box_data,
}

with open("data_module4_anova.json", "w", encoding="utf-8") as f:
    json.dump(module4_data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
print("  -> data_module4_anova.json saved")

# ============================================================
# 6. 模块5: 贝叶斯分析
# ============================================================
print("\n=== 模块5: 贝叶斯 ===")

# 基于类型的贝叶斯分析
# 对于每个主要类型，计算好评率的分布参数

bayes_genre_data = {}
for genre in sorted(major_genres):
    group = df_anova[df_anova["main_genre"] == genre]["positive_ratio"]
    mean_ratio = float(group.mean())
    std_ratio = float(group.std())
    n_obs = int(len(group))

    # 用Beta分布作为共轭先验
    # 从数据估计Beta分布参数（method of moments）
    alpha = mean_ratio * (mean_ratio * (1 - mean_ratio) / (std_ratio ** 2) - 1)
    beta = (1 - mean_ratio) * (mean_ratio * (1 - mean_ratio) / (std_ratio ** 2) - 1)

    # 先验：弱先验 (alpha_prior=2, beta_prior=2) -> Beta(2,2) 均值0.5
    alpha_prior = 2
    beta_prior = 2

    # 后验 = 先验 + 数据
    success = int(group.sum() * 100)  # 近似
    failure = int((1 - group).sum() * 100)

    # 简化：用观测到的均值和样本量构建后验
    # 后验Beta(alpha_prior + k, beta_prior + n-k), k= successes, n=trials
    k = int(mean_ratio * n_obs)
    alpha_post = alpha_prior + k
    beta_post = beta_prior + (n_obs - k)

    # 生成分布曲线数据点
    x = np.linspace(0, 1, 100)
    # 先验分布
    prior_y = stats.beta.pdf(x, alpha_prior, beta_prior)
    # 后验分布
    posterior_y = stats.beta.pdf(x, alpha_post, beta_post)

    # 逐步更新 (观察1次, 10次, 100次, 全部)
    update_steps = []
    for step_n in [1, 10, 100, n_obs]:
        step_k = int(mean_ratio * step_n)
        a_step = alpha_prior + step_k
        b_step = beta_prior + (step_n - step_k)
        step_y = stats.beta.pdf(x, a_step, b_step)
        update_steps.append({
            "n_obs": step_n,
            "alpha": round(float(a_step), 1),
            "beta": round(float(b_step), 1),
            "mean": round(float(a_step / (a_step + b_step)) * 100, 1),
            "std": round(float(np.sqrt(a_step * b_step / ((a_step + b_step)**2 * (a_step + b_step + 1))) * 100), 1),
            "distribution": [
                {"x": round(float(xi), 3), "y": round(float(yi), 4)}
                for xi, yi in zip(x, step_y)
            ],
        })

    bayes_genre_data[genre] = {
        "n_obs": n_obs,
        "observed_mean": round(mean_ratio * 100, 1),
        "observed_std": round(std_ratio * 100, 1),
        "prior": {
            "alpha": alpha_prior,
            "beta": beta_prior,
            "distribution": [
                {"x": round(float(xi), 3), "y": round(float(yi), 4)}
                for xi, yi in zip(x, prior_y)
            ],
        },
        "posterior": {
            "alpha": round(float(alpha_post), 1),
            "beta": round(float(beta_post), 1),
            "mean": round(float(alpha_post / (alpha_post + beta_post)) * 100, 1),
            "distribution": [
                {"x": round(float(xi), 3), "y": round(float(yi), 4)}
                for xi, yi in zip(x, posterior_y)
            ],
        },
        "update_steps": update_steps,
    }

# 价格区间的贝叶斯分析
price_ranges = [
    ("免费 (0)", 0, 0.01),
    ("$1-5", 0.01, 5.01),
    ("$5-10", 5.01, 10.01),
    ("$10-20", 10.01, 20.01),
    ("$20-30", 20.01, 30.01),
    ("$30+", 30.01, 1000),
]

bayes_price_data = {}
x = np.linspace(0, 1, 100)
prior_y = stats.beta.pdf(x, 2, 2)

for label, lo, hi in price_ranges:
    group = df[(df["price"] >= lo) & (df["price"] < hi)]["positive_ratio"]
    if len(group) < 30:
        continue
    mean_ratio = float(group.mean())
    n_obs = int(len(group))
    k = int(mean_ratio * n_obs)
    alpha_post = 2 + k
    beta_post = 2 + (n_obs - k)
    posterior_y = stats.beta.pdf(x, alpha_post, beta_post)

    bayes_price_data[label] = {
        "n_obs": n_obs,
        "observed_mean": round(mean_ratio * 100, 1),
        "posterior_mean": round(float(alpha_post / (alpha_post + beta_post)) * 100, 1),
        "distribution": [
            {"x": round(float(xi), 3), "y": round(float(yi), 4)}
            for xi, yi in zip(x, posterior_y)
        ],
    }

module5_data = {
    "explanation": {
        "prior": "使用Beta(2,2)作为弱先验，表示对游戏好评率没有强烈预设偏见",
        "method": "贝叶斯更新：后验 = 先验 + 观测数据。每次观测到同类游戏的好评数据，后验分布就会更新",
        "interpretation": "后验分布越窄，不确定性越小；后验均值越接近观测均值，说明数据越有说服力",
    },
    "genre_data": bayes_genre_data,
    "price_data": bayes_price_data,
}

with open("data_module5_bayesian.json", "w", encoding="utf-8") as f:
    json.dump(module5_data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
print("  -> data_module5_bayesian.json saved")

print("\n=== 全部完成! ===")
print("生成的数据文件:")
print("  1. data_module1_descriptive.json - 描述性统计")
print("  2. data_module2_hypothesis.json - 假设检验")
print("  3. data_module3_correlation.json - 相关与回归")
print("  4. data_module4_anova.json - 方差分析")
print("  5. data_module5_bayesian.json - 贝叶斯分析")
