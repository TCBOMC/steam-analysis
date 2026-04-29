"""
将5个JSON数据文件合并嵌入到HTML中，生成单文件版本
"""
import json
import os

os.chdir(r"c:\Users\TRSEIMC\WorkBuddy\20260428204258\steam-analysis")

# 读取HTML
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 读取5个JSON
json_files = {
    "MODULE1": "data_module1_descriptive.json",
    "MODULE2": "data_module2_hypothesis.json",
    "MODULE3": "data_module3_correlation.json",
    "MODULE4": "data_module4_anova.json",
    "MODULE5": "data_module5_bayesian.json",
}

for key, file in json_files.items():
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    json_str = json.dumps(data, ensure_ascii=False)
    # 替换fetch调用为直接赋值
    placeholder = f"['{key.lower()}', '{file}']"
    # We need to inline the data - let me do this differently

# Actually, let me just embed the data as a script tag
embed_script = "<script>\nconst EMBEDDED_DATA = {\n"
for key, file in json_files.items():
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    embed_script += f"  {key.lower()}: {json.dumps(data, ensure_ascii=False)},\n"
embed_script += "};\n</script>\n"

# Replace the fetch-based loader
old_loader = """async function loadData() {
    const files = [
        ['module1', 'data_module1_descriptive.json'],
        ['module2', 'data_module2_hypothesis.json'],
        ['module3', 'data_module3_correlation.json'],
        ['module4', 'data_module4_anova.json'],
        ['module5', 'data_module5_bayesian.json'],
    ];
    const promises = files.map(([key, file]) =>
        fetch(file).then(r => r.json()).then(d => DATA[key] = d)
    );
    await Promise.all(promises);
    initAllModules();
}"""

new_loader = """function loadData() {
    Object.assign(DATA, EMBEDDED_DATA);
    initAllModules();
}"""

html = html.replace(old_loader, new_loader)

# Insert embedded data script before </head>
html = html.replace("</head>", embed_script + "</head>")

with open("index_standalone.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Generated index_standalone.html ({os.path.getsize('index_standalone.html') / 1024 / 1024:.1f} MB)")
print("Done!")
