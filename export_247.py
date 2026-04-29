import json,sys
sys.stdout.reconfigure(encoding='utf-8')
data=json.load(open('timeline_data.json','r',encoding='utf-8'))
names=json.load(open('game_names.json','r',encoding='utf-8'))
s=set()
for y,yd in data['yearly'].items():
    for g in yd.get('top5',[])+yd.get('best_by_genre',[]):
        if g.get('appid'):
            s.add((g['appid'],g['name']))
lines=[]
for a,n in sorted(s,key=lambda x:int(x[0])):
    e=names.get(str(a),{})
    zh=e.get('schinese','(MISSING)')
    ja=e.get('japanese','')
    lines.append(f'{a}|{n}|{zh}|{ja}')
with open('check_247.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f'Written {len(lines)} entries')
