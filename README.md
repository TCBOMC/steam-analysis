# Steam 时代编年史

Steam 平台游戏数据的交互式可视化分析，覆盖 **2006–2025 年**共 20 年、超过 30,000 款游戏。

## 在线预览

直接打开 `index_standalone.html` 即可在浏览器中查看完整交互界面。

## 功能

- **时间轴**：拖动或点击浏览 2006–2025 年的 Steam 游戏生态变迁，默认定位最新年份
- **多语言切换**：支持中文 / 英文 / 日文，247 款推荐游戏名全覆盖翻译
- **年度画像**：每年度的游戏数量、价格、好评率、游玩时长等核心指标
- **类型分布**：各类型游戏的数量与好评率对比
- **价格分析**：价格区间分布及各区间的好评率
- **标签词云**：基于 Steam 用户标签投票 + 游戏描述文本，悬停显示真实出现次数，已过滤万能填充词（combat/fight/items 等）
- **综合推荐**：加权评分算法（好评率 30% + 热度 30% + 游玩深度 20% + 价格合理性 10% + 影响力 10%），每年 TOP 5 及各类型最佳
- **时期洞察**：年度综合推荐与趋势总结，游戏名跟随语言切换
- **跨年趋势**：游戏数量、价格、好评率、类型兴衰的时间序列变化

## 项目结构

```
steam-analysis/
├── index_standalone.html       # 单机版（所有数据内嵌，直接打开即用）
├── index_v2.html               # 模板版（通过 embed_v2.py 注入数据生成单机版）
├── timeline_data.json          # 分析结果数据
├── game_names.json             # 247款游戏多语言翻译（中/日）
├── analysis_v2.py              # 数据分析脚本
├── build_game_names_final.py   # 游戏名翻译构建脚本（285条手动映射 + 外部数据）
├── embed_v2.py                 # 数据注入脚本（JSON → HTML）
├── data_module*.json           # 统计分析模块数据（描述统计/假设检验/相关性/方差分析/贝叶斯）
├── explore.py                  # 数据探索脚本
└── index.html                  # 旧版页面
```

## 数据源

- **Kaggle**: [fronkongames/steam-games-dataset](https://www.kaggle.com/datasets/fronkongames/steam-games-dataset)（2026 年 1 月更新，覆盖至 2025 年 4 月）
- 筛选条件：评价数 ≥ 50，价格 ≤ $200

## 如何重新生成数据

```bash
# 1. 下载数据集（需先 pip install kagglehub）
python -c "import kagglehub; kagglehub.dataset_download('fronkongames/steam-games-dataset')"

# 2. 运行分析（需要修改 analysis_v2.py 中的 JSON 路径指向下载位置）
python analysis_v2.py

# 3. （可选）重新构建游戏名翻译
python build_game_names_final.py

# 4. 生成单机 HTML
python embed_v2.py
```

## 技术栈

- **数据**: Python / Pandas / NumPy / SciPy
- **可视化**: 原生 HTML + CSS + JavaScript（Chart.js + ECharts 词云）
- **部署**: 单文件 HTML，无需服务器

## License

MIT
