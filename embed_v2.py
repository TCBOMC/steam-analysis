"""生成单文件版：将timeline_data.json嵌入index_v2.html"""
import json
import os

os.chdir(r"c:\Users\TRSEIMC\WorkBuddy\20260428204258\steam-analysis")

with open("timeline_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("index_v2.html", "r", encoding="utf-8") as f:
    html = f.read()

# 将数据作为全局变量注入
embed = '<script>\nconst EMBEDDED_DATA = ' + json.dumps(data, ensure_ascii=False) + ';\n</script>\n'

# 替换body开头
html = html.replace('<body>', '<body>\n' + embed)

with open("index_standalone.html", "w", encoding="utf-8") as f:
    f.write(html)

sz = os.path.getsize("index_standalone.html")
print(f"Generated index_standalone.html ({sz/1024:.0f} KB)")
