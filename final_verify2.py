import json, sys
sys.stdout.reconfigure(encoding='utf-8')
names = json.load(open('game_names.json', 'r', encoding='utf-8'))

checks = [
    ('659', 'Portal 2', '传送门 2'),
    ('8500', 'EVE Online', '星战前夜'),
    ('49520', 'Borderlands 2', '无主之地 2'),
    ('218620', 'PAYDAY 2', '收获日 2'),
    ('960090', 'Bloons TD 6', '气球塔防 6'),
    ('1085660', 'Destiny 2', '命运 2'),
    ('1237970', 'Titanfall 2', '泰坦天降 2'),
    ('204360', 'Castle Crashers', '城堡破坏者'),
    ('289070', 'Civ VI', '文明 6'),
    ('324680', 'Impossible Creatures', '不可能的生物'),
    ('431960', 'Wallpaper Engine', '壁纸引擎'),
    ('646570', 'Slay the Spire', '杀戮尖塔'),
    ('2358720', 'Black Myth', '黑神话'),
    ('1466860', 'Age of Empires', '帝国时代'),
    ('3830', 'Psychonauts', '脑航员'),
    ('4000', 'Garry', '盖瑞模组'),
    ('242760', 'Forest', '森林'),
    ('252490', 'Rust', '腐蚀'),
    ('292030', 'Witcher 3', '巫师 3'),
    ('322170', 'Geometry Dash', '几何冲刺'),
    ('1966720', 'Lethal Company', '致命公司'),
    ('1028630', 'Cricket 19', '板球'),
    ('1085510', 'Garfield Kart', '加菲猫'),
    ('22380', 'Fallout: New Vegas', '新维加斯'),
    ('256290', 'Child of Light', '光之子'),
]

print('=== 最终验证 ===')
all_ok = True
for appid, hint, expect in checks:
    e = names.get(appid, {})
    zh = e.get('schinese', '(MISSING)')
    ok = expect in zh
    if not ok:
        all_ok = False
    print(f'  [{"OK" if ok else "FAIL"}] {appid} | {zh}  (expect ...{expect}...)')

print(f'\nAll passed: {all_ok}')
