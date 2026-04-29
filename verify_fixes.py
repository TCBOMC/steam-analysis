import json,sys
sys.stdout.reconfigure(encoding='utf-8')
names=json.load(open('game_names.json','r',encoding='utf-8'))

checks = [
    ('204360',  '城堡破坏者'),
    ('289070',  '文明 6'),
    ('324680',  '不可能的生物'),
    ('431960',  '壁纸引擎'),
    ('646570',  '杀戮尖塔'),
    ('1466860', '帝国时代'),
    ('1486350', 'VRoid Studio'),
    ('2358720', '黑神话'),
    ('2670630', '超市模拟器'),
    ('2142790', 'Fields of Mistria'),
    ('2386460', 'Tree It'),
    ('1625080', 'Have a Nice Dream'),
]
all_ok=True
for appid, expect in checks:
    e=names.get(appid,{})
    zh=e.get('schinese','(MISSING)')
    ok=expect in zh
    if not ok: all_ok=False
    status='OK' if ok else 'FAIL'
    print(f'  [{status}] {appid} | {zh}')
print(f'\nAll passed: {all_ok}')
