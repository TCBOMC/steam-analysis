import json,sys
sys.stdout.reconfigure(encoding='utf-8')
names=json.load(open('game_names.json','r',encoding='utf-8'))
data=json.load(open('timeline_data.json','r',encoding='utf-8'))

# 收集所有 displayed appid
displayed={}
for y,yd in data['yearly'].items():
    for g in yd.get('top5',[])+yd.get('best_by_genre',[]):
        if g.get('appid'):
            displayed[g['appid']]=g['name']

issues=[]
for appid,en_name in sorted(displayed.items(), key=lambda x:int(x[0])):
    a=str(appid)
    e=names.get(a,{})
    zh=e.get('schinese','(MISSING)')
    ja=e.get('japanese','')
    # 检查中文名是否包含明显的另一个游戏名
    # 重点检查之前出问题的映射
    checks = {
        '2358720': '黑神话',
        '289070': '文明',
        '1466860': '帝国时代',
        '1486350': 'VRoid',
        '1625080': 'Nice Dream',
        '2142790': 'Mistria',
        '2386460': 'Tree It',
        '2670630': '超市',
        '292030': '巫师',
        '3830': '脑航员',
        '4000': '盖瑞',
        '22380': '新维加斯',
        '242760': '森林',
        '252490': '腐蚀',
        '256290': '光之子',
        '322170': '几何冲刺',
        '1028630': '板球',
        '1085510': '加菲猫',
        '1966720': '致命公司',
        '204360': '城堡破坏者',
        '646570': '杀戮尖塔',
        '431960': '壁纸引擎',
    }
    if a in checks:
        if checks[a] not in zh:
            issues.append(f'FAIL {appid} {en_name} -> {zh} (expected: {checks[a]})')

if issues:
    print('ISSUES FOUND:')
    for i in issues:
        print(f'  {i}')
else:
    print(f'ALL {len(displayed)} translations verified OK')
