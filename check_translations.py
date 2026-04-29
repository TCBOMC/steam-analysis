"""检查247个显示游戏的翻译匹配来源，标记模糊匹配（高风险）"""
import pandas as pd
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

ext = pd.read_csv('game_names_merged.csv')

def normalize(name):
    if pd.isna(name) or not str(name).strip():
        return ''
    s = str(name).strip().lower()
    s = re.sub(r'[\u00ae\u2122\u00a9]', '', s)  # ®™©
    s = re.sub(r'\s+', ' ', s)
    return s

ext_index = {}
for _, row in ext.iterrows():
    n = normalize(row['en_name'])
    if n:
        zh = str(row['zh_name']).strip() if pd.notna(row['zh_name']) else ''
        ja = str(row['ja_name']).strip() if pd.notna(row['ja_name']) else ''
        ext_index[n] = (zh, ja)

def try_ext_match_debug(en_name):
    norm = normalize(en_name)
    if not norm:
        return None, 'none'
    # 精确匹配
    if norm in ext_index:
        zh, ja = ext_index[norm]
        entry = {}
        if zh: entry['schinese'] = zh
        if ja: entry['japanese'] = ja
        return entry, 'exact'
    # 模糊匹配
    patterns = [
        re.sub(r'[:\-\u2013\u2014].*$', '', norm),
        re.sub(r' (edition|version|goty|the game|hd|remastered|definitive|deluxe|premium|standard|gold|platinum|ultimate|collection).*$', '', norm),
        re.sub(r' (steam|pack|bundle).*$', '', norm),
    ]
    for candidate in patterns:
        candidate = candidate.strip()
        if candidate and candidate in ext_index:
            zh, ja = ext_index[candidate]
            entry = {}
            if zh: entry['schinese'] = zh
            if ja: entry['japanese'] = ja
            return entry, f'fuzzy ({candidate})'
    return None, 'none'

with open('timeline_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

displayed = {}
for y, yd in data['yearly'].items():
    for g in yd.get('top5', []):
        if g.get('appid'):
            displayed[g['appid']] = g['name']
    for g in yd.get('best_by_genre', []):
        if g.get('appid'):
            displayed[g['appid']] = g['name']

# 先输出模糊匹配的（高风险）
print('=== 模糊匹配的游戏（高风险，需逐个检查） ===')
fuzzy_items = []
for appid, en_name in sorted(displayed.items(), key=lambda x: int(x[0])):
    result, method = try_ext_match_debug(en_name)
    if 'fuzzy' in method:
        zh = result.get('schinese', '') if result else ''
        ja = result.get('japanese', '') if result else ''
        fuzzy_items.append((appid, en_name, zh, ja, method))
        print(f'  {appid} | {en_name} | {zh} | {ja} | {method}')

print(f'\n模糊匹配总数: {len(fuzzy_items)}')

# 输出全部247个到文件
with open('translation_check.csv', 'w', encoding='utf-8-sig') as f:
    f.write('appid,en_name,zh_name,ja_name,match_method\n')
    for appid, en_name in sorted(displayed.items(), key=lambda x: int(x[0])):
        result, method = try_ext_match_debug(en_name)
        if result:
            zh = result.get('schinese', '')
            ja = result.get('japanese', '')
            f.write(f'{appid},"{en_name}","{zh}","{ja}",{method}\n')
        else:
            f.write(f'{appid},"{en_name}","","","none"\n')

print(f'已输出到 translation_check.csv')
