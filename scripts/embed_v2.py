"""生成单文件版：将timeline_data.json和game_names.json嵌入index_v2.html"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

os.chdir(ROOT)

with open("data/timeline_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("src/index_v2.html", "r", encoding="utf-8") as f:
    html = f.read()

# 嵌入主数据
embed = '<script>\nconst EMBEDDED_DATA = ' + json.dumps(data, ensure_ascii=False) + ';\n</script>\n'

# 嵌入翻译名称（如果存在）
names_embed = ''
names_path = os.path.join("data", "game_names.json")
if os.path.exists(names_path):
    with open(names_path, "r", encoding="utf-8") as f:
        names = json.load(f)
    if names:
        names_embed = '<script>\nconst GAME_NAMES = ' + json.dumps(names, ensure_ascii=False) + ';\n</script>\n'

# 替换body开头
html = html.replace('<body>', '<body>\n' + embed + names_embed)

with open("index_standalone.html", "w", encoding="utf-8") as f:
    f.write(html)

sz = os.path.getsize("index_standalone.html")
print(f"Generated index_standalone.html ({sz/1024:.0f} KB)")
