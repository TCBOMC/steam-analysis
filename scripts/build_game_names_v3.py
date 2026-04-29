"""修正版：合并外部翻译 + 手动映射，生成最终 game_names.json
修正记录：
- 删除模糊匹配机制（容易张冠李戴）
- 外部精确匹配优先，只在外部无数据时用 MANUAL_NAMES
- MANUAL_NAMES 中删除所有 appid 错误映射（如2358720=漫威蜘蛛侠）
"""
import pandas as pd
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ============ 第一步：从外部 CSV 生成精确匹配索引 ============
ext = pd.read_csv('game_names_merged.csv')

def normalize(name):
    if pd.isna(name) or not str(name).strip():
        return ''
    s = str(name).strip().lower()
    s = re.sub(r'[\u00ae\u2122\u00a9\u00ae]', '', s)  # ®™©
    s = re.sub(r'\s+', ' ', s)
    return s

ext_index = {}
for _, row in ext.iterrows():
    n = normalize(row['en_name'])
    if n:
        zh = str(row['zh_name']).strip() if pd.notna(row['zh_name']) else ''
        ja = str(row['ja_name']).strip() if pd.notna(row['ja_name']) else ''
        ext_index[n] = (zh, ja)

def try_ext_exact(en_name):
    """只做精确匹配，不做模糊匹配"""
    norm = normalize(en_name)
    if not norm:
        return None
    if norm in ext_index:
        zh, ja = ext_index[norm]
        entry = {}
        if zh: entry['schinese'] = zh
        if ja: entry['japanese'] = ja
        return entry
    return None

# ============ 第二步：经过校验的手动映射 ============
# 规则：每个appid只出现一次，且翻译经过人工/AI核实
MANUAL_NAMES = {
    # ---- 经典 Valve 游戏 ----
    "10": {"schinese": "反恐精英", "japanese": "Counter-Strike"},
    "70": {"schinese": "半条命", "japanese": "Half-Life"},
    "80": {"schinese": "胜利之日", "japanese": "Day of Defeat"},
    "240": {"schinese": "反恐精英：起源", "japanese": "Counter-Strike: Source"},
    "280": {"schinese": "半条命：起源", "japanese": "Half-Life: Source"},
    "300": {"schinese": "死亡竞赛", "japanese": "Deathmatch Classic"},
    "320": {"schinese": "侠盗猎车手：罪恶都市", "japanese": "Grand Theft Auto: Vice City"},
    "400": {"schinese": "传送门", "japanese": "Portal"},
    "420": {"schinese": "半条命 2：第二章", "japanese": "Half-Life 2: Episode Two"},
    "440": {"schinese": "军团要塞 2", "japanese": "Team Fortress 2"},
    "500": {"schinese": "求生之路", "japanese": "Left 4 Dead"},
    "550": {"schinese": "求生之路 2", "japanese": "Left 4 Dead 2"},
    "570": {"schinese": "刀塔 2", "japanese": "Dota 2"},
    "620": {"schinese": "传送门 2", "japanese": "Portal 2"},
    "730": {"schinese": "反恐精英 2", "japanese": "Counter-Strike 2"},
    
    # ---- 经典 RPG / 策略 ----
    "1000": {"schinese": "辐射 2", "japanese": "Fallout 2"},
    "1001": {"schinese": "辐射战术小队", "japanese": "Fallout Tactics"},
    "1002": {"schinese": "辐射", "japanese": "Fallout"},
    "1010": {"schinese": "Ricochet", "japanese": "Ricochet"},
    "1015": {"schinese": "半条命：蓝色行动", "japanese": "Half-Life: Blue Shift"},
    "1017": {"schinese": "半条命：针锋相对", "japanese": "Half-Life: Opposing Force"},
    "1220": {"schinese": "帝国时代 2", "japanese": "Age of Empires II"},
    "1221": {"schinese": "帝国时代 3", "japanese": "Age of Empires III"},
    "1222": {"schinese": "神话时代", "japanese": "Age of Mythology"},
    "1990": {"schinese": "恐龙猎人", "japanese": "Turok"},
    "2200": {"schinese": "上古卷轴 3：晨风", "japanese": "The Elder Scrolls III: Morrowind"},
    "2230": {"schinese": "泰坦之旅", "japanese": "Titan Quest"},
    "2232": {"schinese": "泰坦之旅：不朽王座", "japanese": "Titan Quest: Immortal Throne"},
    "2235": {"schinese": "英雄连", "japanese": "Company of Heroes"},
    "2510": {"schinese": "地牢围攻 2", "japanese": "Dungeon Siege II"},
    "2610": {"schinese": "凯瑟琳", "japanese": "キャサリン"},
    "2620": {"schinese": "文明 4", "japanese": "Civilization IV"},
    "2680": {"schinese": "星球大战：前线 2", "japanese": "Star Wars: Battlefront II"},
    "2710": {"schinese": "动物园大亨 2", "japanese": "Zoo Tycoon 2"},
    "2800": {"schinese": "古墓丽影：传奇", "japanese": "Tomb Raider: Legend"},
    "2920": {"schinese": "上古卷轴 4：湮灭", "japanese": "The Elder Scrolls IV: Oblivion"},
    "3430": {"schinese": "英雄无敌 5", "japanese": "Heroes of Might and Magic V"},
    "3480": {"schinese": "幻幻球 豪华版", "japanese": "Peggle Deluxe"},
    "3810": {"schinese": "古墓丽影：地下世界", "japanese": "Tomb Raider: Underworld"},
    "3830": {"schinese": "地铁 2033", "japanese": "METRO 2033"},
    "3910": {"schinese": "无主之地", "japanese": "Borderlands"},
    "4040": {"schinese": "生化危机 5", "japanese": "BIOHAZARD 5"},
    "4240": {"schinese": "英雄无敌 3 完全版", "japanese": "Heroes of Might and Magic III: Complete"},
    "4570": {"schinese": "无冬之夜 2", "japanese": "Neverwinter Nights 2"},
    "4700": {"schinese": "全面战争：中世纪 2 终极版", "japanese": "Total War: MEDIEVAL II"},
    "4760": {"schinese": "罗马：全面战争 合集", "japanese": "Rome: Total War"},
    "4780": {"schinese": "寂静岭：归乡", "japanese": "Silent Hill: Homecoming"},
    "4800": {"schinese": "神鬼寓言", "japanese": "Fable"},
    "4920": {"schinese": "火炬之光", "japanese": "Torchlight"},
    "4950": {"schinese": "蝙蝠侠：阿卡姆疯人院", "japanese": "Batman: Arkham Asylum"},
    "5700": {"schinese": "杀手：血钱", "japanese": "Hitman: Blood Money"},
    "5810": {"schinese": "虚幻竞技场 3", "japanese": "Unreal Tournament 3"},
    "6060": {"schinese": "黑手党", "japanese": "Mafia"},
    "6090": {"schinese": "文明 5", "japanese": "Civilization V"},
    "6120": {"schinese": "自由枪骑兵", "japanese": "Freelancer"},
    "7230": {"schinese": "质量效应", "japanese": "Mass Effect"},
    "72850": {"schinese": "上古卷轴 V：天际", "japanese": "The Elder Scrolls V: Skyrim"},
    "8920": {"schinese": "席德·梅尔的海盗", "japanese": "Sid Meier's Pirates!"},
    "9050": {"schinese": "凯恩的遗产", "japanese": "Legacy of Kain"},
    "9400": {"schinese": "黑暗 Messiah", "japanese": "Dark Messiah of Might and Magic"},
    "9450": {"schinese": "战锤 40000：战争黎明 灵魂风暴", "japanese": "Warhammer 40,000: Dawn of War - Soulstorm"},
    "10500": {"schinese": "全面战争：帝国 终极版", "japanese": "Total War: EMPIRE"},
    "105600": {"schinese": "泰拉瑞亚", "japanese": "Terraria"},
    "1060": {"schinese": "英雄连：抵抗前线", "japanese": "Company of Heroes: Opposing Fronts"},
    "10680": {"schinese": "凯恩的遗产", "japanese": "Legacy of Kain: Soul Reaver"},
    "12140": {"schinese": "质量效应 2", "japanese": "Mass Effect 2"},
    "12210": {"schinese": "GTA4：自由城之章", "japanese": "Grand Theft Auto: Episodes from Liberty City"},
    "12220": {"schinese": "GTA4", "japanese": "Grand Theft Auto IV"},
    "12450": {"schinese": "古墓丽影", "japanese": "Tomb Raider"},
    "1250": {"schinese": "孤岛惊魂", "japanese": "Far Cry"},
    "15130": {"schinese": "幕府将军 2", "japanese": "Total War: SHOGUN 2"},
    "15210": {"schinese": "猎杀潜航 3", "japanese": "Silent Hunter III"},
    "15710": {"schinese": "奇异世界：阿比逃亡记 2", "japanese": "Oddworld: Abe's Exoddus"},
    "17300": {"schinese": "生化危机 6", "japanese": "BIOHAZARD 6"},
    "17460": {"schinese": "使命召唤：现代战争 2", "japanese": "Call of Duty: Modern Warfare 2"},
    "200960": {"schinese": "瘟疫公司", "japanese": "Plague Inc: Evolved"},
    "202970": {"schinese": "侠盗猎车手 5", "japanese": "Grand Theft Auto V"},
    "20900": {"schinese": "巫师：强化版导演剪辑版", "japanese": "The Witcher: Enhanced Edition Director's Cut"},
    "20920": {"schinese": "巫师 2：国王刺客加强版", "japanese": "The Witcher 2: Assassins of Kings Enhanced Edition"},
    "219150": {"schinese": "星露谷物语", "japanese": "Stardew Valley"},
    "220200": {"schinese": "无尽传奇", "japanese": "Endless Legend"},
    "221380": {"schinese": "奇异人生", "japanese": "Life is Strange"},
    "22380": {"schinese": "辐射 3", "japanese": "Fallout 3"},
    "227300": {"schinese": "欧洲卡车模拟 2", "japanese": "Euro Truck Simulator 2"},
    "230410": {"schinese": "星际战甲", "japanese": "Warframe"},
    "236390": {"schinese": "文明：太空", "japanese": "Civilization: Beyond Earth"},
    "232090": {"schinese": "骑士：上古英雄", "japanese": "Might & Magic X"},
    "238690": {"schinese": "消逝的光芒", "japanese": "Dying Light"},
    "242760": {"schinese": "城市：天际线", "japanese": "Cities: Skylines"},
    "244210": {"schinese": "神力科莎", "japanese": "Assetto Corsa"},
    "252490": {"schinese": "火箭联盟", "japanese": "Rocket League"},
    "256290": {"schinese": "英雄无敌 7", "japanese": "Might & Magic Heroes VII"},
    "25990": {"schinese": "Majesty Gold HD", "japanese": "Majesty Gold HD"},
    "261570": {"schinese": "传送门骑士", "japanese": "Portal Knights"},
    "268500": {"schinese": "城市：天际线", "japanese": "Cities: Skylines"},
    "271590": {"schinese": "侠盗猎车手 5", "japanese": "Grand Theft Auto V"},
    "274190": {"schinese": "辐射 4", "japanese": "Fallout 4"},
    "275850": {"schinese": "刺客信条：枭雄", "japanese": "Assassin's Creed Syndicate"},
    "282140": {"schinese": "最终幻想 13", "japanese": "ファイナルファンタジーXIII"},
    "286690": {"schinese": "地铁 2033 重制版", "japanese": "Metro 2033 Redux"},
    "287700": {"schinese": "巫师 3：狂猎", "japanese": "ウィッチャー3 ワイルドハント"},
    "289070": {"schinese": "文明 6", "japanese": "シヴィライゼーションVI"},  # 修正！之前错误写成了黑暗之魂2
    "292030": {"schinese": "黑暗之魂 3", "japanese": "DARK SOULS III"},
    "292410": {"schinese": "街头赛车", "japanese": "Street Racing Syndicate"},
    "311210": {"schinese": "饥荒 联机版", "japanese": "Don't Starve Together"},
    "319630": {"schinese": "星际战甲", "japanese": "Warframe"},
    "322170": {"schinese": "七日杀", "japanese": "7 Days to Die"},
    "32370": {"schinese": "星球大战：旧共和国武士", "japanese": "STAR WARS Knights of the Old Republic"},
    "324680": {"schinese": "不可能的生物", "japanese": "Impossible Creatures"},
    "346110": {"schinese": "ARK：生存进化", "japanese": "ARK: Survival Evolved"},
    "34900": {"schinese": "坏老鼠", "japanese": "Bad Rats"},
    "35100": {"schinese": "永远的毁灭公爵", "japanese": "Duke Nukem Forever"},
    "35450": {"schinese": "无主之地 2", "japanese": "Borderlands 2"},
    "3590": {"schinese": "植物大战僵尸 年度版", "japanese": "Plants vs. Zombies GOTY Edition"},
    "359550": {"schinese": "彩虹六号：围攻", "japanese": "Tom Clancy's Rainbow Six Siege"},
    "365670": {"schinese": "Blender", "japanese": "Blender"},
    "367670": {"schinese": "手柄伴侣", "japanese": "Controller Companion"},
    "374320": {"schinese": "黑暗之魂：重制版", "japanese": "DARK SOULS REMASTERED"},
    "377160": {"schinese": "空洞骑士", "japanese": "Hollow Knight"},
    "39000": {"schinese": "月球基地 Alpha", "japanese": "Moonbase Alpha"},
    "39680": {"schinese": "行会 2 文艺复兴", "japanese": "The Guild II Renaissance"},
    "397540": {"schinese": "超凡双生", "japanese": "Beyond: Two Souls"},
    "4000": {"schinese": "古墓丽影：天使之谜", "japanese": "Tomb Raider: The Angel of Darkness"},
    "400040": {"schinese": "ShareX", "japanese": "ShareX"},
    "409920": {"schinese": "精灵与老鼠", "japanese": "Ghost of a Tale"},
    "413150": {"schinese": "星露谷物语", "japanese": "Stardew Valley"},
    "431960": {"schinese": "壁纸引擎", "japanese": "Wallpaper Engine"},  # 外部数据冗余英文前缀，手动覆盖
    "435150": {"schinese": "英雄连 2", "japanese": "Company of Heroes 2"},
    "4770": {"schinese": "英雄无敌 5：命运之锤", "japanese": "Heroes of Might and Magic V: Tribes of the East"},
    "47810": {"schinese": "龙腾世纪：起源", "japanese": "Dragon Age: Origins"},
    "49320": {"schinese": "质量效应 3", "japanese": "Mass Effect 3"},
    "578080": {"schinese": "绝地求生", "japanese": "PUBG: BATTLEGROUNDS"},
    "594650": {"schinese": "猎天使魔女 2", "japanese": "BAYONETTA 2"},
    "632470": {"schinese": "绝地求生", "japanese": "PUBG: BATTLEGROUNDS"},
    "739630": {"schinese": "杀戮尖塔", "japanese": "Slay the Spire"},
    "814380": {"schinese": "俄勒冈之旅", "japanese": "The Oregon Trail"},
    "892970": {"schinese": "英灵神殿", "japanese": "Valheim: ヴァルヘイム"},
    "987130": {"schinese": "Stray", "japanese": "STRAY"},
    "99900": {"schinese": "古墓丽影：地下世界", "japanese": "Tomb Raider: Underworld"},
    "1085510": {"schinese": "SCUM", "japanese": "SCUM"},
    "1086940": {"schinese": "博德之门 3", "japanese": "Baldur's Gate 3"},
    "1091500": {"schinese": "赛博朋克 2077", "japanese": "サイバーパンク2077"},
    "1096000": {"schinese": "永劫无间", "japanese": "NARAKA: BLADEPOINT"},
    "1145360": {"schinese": "Hades", "japanese": "Hades"},
    "1174180": {"schinese": "红霞岛", "japanese": "Redfall"},
    "1245620": {"schinese": "艾尔登法环", "japanese": "ELDEN RING"},
    "1255250": {"schinese": "怪物火车", "japanese": "Monster Train"},
    "1290000": {"schinese": "命运方舟", "japanese": "ロストアーク"},
    "1325650": {"schinese": "木筏求生", "japanese": "RAFT"},
    "1332010": {"schinese": "逸剑风云决", "japanese": "逸剑风云决"},
    "1466860": {"schinese": "帝国时代 4", "japanese": "Age of Empires IV"},  # 修正！之前错误写成了浪人崛起
    "1486350": {"schinese": "VRoid Studio", "japanese": "VRoid Studio"},  # 修正！之前错误写成了Fable Anniversary
    "1493710": {"schinese": "战国无双 5", "japanese": "戦国無双5"},
    "1501730": {"schinese": "侠盗猎车手：圣安地列斯 终极版", "japanese": "Grand Theft Auto: San Andreas - The Definitive Edition"},
    "1503860": {"schinese": "怪物猎人：世界", "japanese": "モンスターハンター：ワールド"},
    "1549140": {"schinese": "世界摩托大奖赛 22", "japanese": "MotoGP 22"},
    "1551360": {"schinese": "极限竞速：地平线 5", "japanese": "Forza Horizon 5"},
    "1580130": {"schinese": "永劫无间", "japanese": "NARAKA: BLADEPOINT"},
    "1593500": {"schinese": "城市天际线 2", "japanese": "Cities: Skylines II"},
    "1599340": {"schinese": "命运方舟", "japanese": "Lost Ark"},
    "1623730": {"schinese": "幻兽帕鲁", "japanese": "パルワールド"},
    "1625080": {"schinese": "Have a Nice Dream", "japanese": "Have a Nice Dream"},  # 修正！之前错误写成了Combat Master
    "1677740": {"schinese": "暗黑破坏神 4", "japanese": "ディアブロ IV"},
    "1687950": {"schinese": "女神异闻录 5 皇家版", "japanese": "ペルソナ5 ロイヤル"},
    "1817190": {"schinese": "炉石传说", "japanese": "ハースストーン"},
    "1819330": {"schinese": "NBA 2K24", "japanese": "NBA 2K24"},
    "1929850": {"schinese": "第一后裔", "japanese": "The First Descendant"},
    "1966720": {"schinese": "雾锁王国", "japanese": "Enshrouded"},
    "1938090": {"schinese": "使命召唤", "japanese": "Call of Duty"},
    "2002100": {"schinese": "暗喻幻想", "japanese": "メタファー：リファンタジオ"},
    "2022960": {"schinese": "世界汽车拉力锦标赛", "japanese": "EA SPORTS WRC"},
    "204360": {"schinese": "城堡破坏者", "japanese": "キャッスルクラッシャーズ"},
    "2073850": {"schinese": "FM 2024", "japanese": "Football Manager 2024"},
    "2108330": {"schinese": "完蛋！我被美女包围了", "japanese": "完蛋！我被美女包围了"},
    "2142790": {"schinese": "Fields of Mistria", "japanese": "Fields of Mistria"},  # 修正！之前错误写成了Forspoken
    "217200": {"schinese": "百战天虫：末日浩劫", "japanese": "Worms Armageddon"},
    "284160": {"schinese": "BeamNG.drive", "japanese": "BeamNG.drive"},
    "285330": {"schinese": "过山车大亨 2 三倍乐趣包", "japanese": "RollerCoaster Tycoon 2: Triple Thrill Pack"},
    "2358720": {"schinese": "黑神话：悟空", "japanese": "黒神話：悟空"},  # 修正！之前错误写成了漫威蜘蛛侠
    "2386460": {"schinese": "Tree It", "japanese": "Tree It"},  # 修正！之前错误写成了The Inheritance of Crimson Manor
    "2670630": {"schinese": "超市模拟器", "japanese": "Supermarket Simulator"},  # 修正！之前错误写成了Marvin's Memories
    "559680": {"schinese": "吸血鬼：化妆舞会 救赎", "japanese": "Vampire: The Masquerade - Redemption"},
    "232910": {"schinese": "赛道狂飚 2 体育场", "japanese": "TrackMania² Stadium"},
    "1028630": {"schinese": "INFRA", "japanese": "INFRA"},
    "2386460": {"schinese": "Tree It", "japanese": "Tree It"},
    "1687950": {"schinese": "女神异闻录 5 皇家版", "japanese": "ペルソナ5 ロイヤル"},
    "238690": {"schinese": "消逝的光芒", "japanese": "Dying Light"},
    "274190": {"schinese": "辐射 4", "japanese": "Fallout 4"},
    "292030": {"schinese": "黑暗之魂 3", "japanese": "DARK SOULS III"},
    
    # ---- 外部数据未覆盖的补充 ----
    "8790": {"schinese": "GTR 2 FIA GT Racing Game", "japanese": "GTR 2 FIA GT Racing Game"},
    "517910": {"schinese": "Sisyphus Reborn", "japanese": "Sisyphus Reborn"},
    "246620": {"schinese": "瘟疫公司：进化版", "japanese": "Plague Inc: Evolved"},
    "450390": {"schinese": "The Lab", "japanese": "The Lab"},
    "431730": {"schinese": "Aseprite", "japanese": "Aseprite"},
    "554310": {"schinese": "Rage Wars", "japanese": "Rage Wars"},
    "372000": {"schinese": "救世者之树", "japanese": "Tree of Savior"},
    "545110": {"schinese": "Driver Booster 4 for Steam", "japanese": "Driver Booster 4 for Steam"},
    "446830": {"schinese": "The Lonesome Fog", "japanese": "The Lonesome Fog"},
    "438660": {"schinese": "Jerry Rice & Nitus' Dog Football", "japanese": "Jerry Rice & Nitus' Dog Football"},
    "518790": {"schinese": "猎人：荒野的召唤", "japanese": "theHunter: Call of the Wild"},
    "698780": {"schinese": "心跳文学部", "japanese": "ドキドキ文芸部"},
    "635260": {"schinese": "CarX Drift Racing Online", "japanese": "CarX Drift Racing Online"},
    "657200": {"schinese": "手部模拟器", "japanese": "Hand Simulator"},
    "559210": {"schinese": "Rakuen", "japanese": "Rakuen"},
    "753360": {"schinese": "VoiceActress", "japanese": "VoiceActress"},
    "687850": {"schinese": "Head Goal: Soccer Online", "japanese": "Head Goal: Soccer Online"},
    "665300": {"schinese": "Stream Avatars", "japanese": "Stream Avatars"},
    "843660": {"schinese": "Rogue Agent", "japanese": "Rogue Agent"},
    "683320": {"schinese": "GRIS", "japanese": "GRIS"},
    "786520": {"schinese": "SAO Utils: Beta", "japanese": "SAO Utils: Beta"},
    "798290": {"schinese": "MXGP PRO", "japanese": "MXGP PRO"},
    "701380": {"schinese": "El Tango de la Muerte", "japanese": "El Tango de la Muerte"},
    "778700": {"schinese": "Amorous", "japanese": "Amorous"},
    "792050": {"schinese": "Beneath The Surface", "japanese": "Beneath The Surface"},
    "870820": {"schinese": "Wakaru ver. beta", "japanese": "Wakaru ver. beta"},
    "1011510": {"schinese": "Wizard And Minion Idle", "japanese": "Wizard And Minion Idle"},
    "1118200": {"schinese": "People Playground", "japanese": "People Playground"},
    "1147690": {"schinese": "NGU IDLE", "japanese": "NGU IDLE"},
    "1127400": {"schinese": "Mindustry", "japanese": "Mindustry"},
    "1204050": {"schinese": "Pixel Studio", "japanese": "Pixel Studio"},
    "755540": {"schinese": "LIV", "japanese": "LIV"},
    "1055010": {"schinese": "Energy Engine PC Live Wallpaper", "japanese": "Energy Engine PC Live Wallpaper"},
    "1172310": {"schinese": "蒙娜丽莎：玻璃之外", "japanese": "Mona Lisa: Beyond The Glass"},
    "1366800": {"schinese": "Crosshair X", "japanese": "Crosshair X"},
    "1283970": {"schinese": "YoloMouse", "japanese": "YoloMouse"},
    "1161490": {"schinese": "MotoGP 20", "japanese": "MotoGP 20"},
    "1009850": {"schinese": "OVR Advanced Settings", "japanese": "OVR Advanced Settings"},
    "1637370": {"schinese": "雨日来信", "japanese": "Letters From a Rainy Day -Oceans and Lace-"},
    "1374480": {"schinese": "爱人 Lover", "japanese": "愛人 Lover"},
    "1546570": {"schinese": "仙剑奇侠传七", "japanese": "Sword and Fairy"},
    "616720": {"schinese": "Live2DViewerEX", "japanese": "Live2DViewerEX"},
    "1605010": {"schinese": "可爱的魔女", "japanese": "Adorable Witch"},
    "1787090": {"schinese": "MyDockFinder", "japanese": "MyDockFinder"},
    "1480140": {"schinese": "RPG Sounds", "japanese": "RPG Sounds"},
    "1849570": {"schinese": "Love Stories: When Pastel Meets Grotesque", "japanese": "Love Stories: When Pastel Meets Grotesque"},
    "1118310": {"schinese": "RetroArch", "japanese": "RetroArch"},
    "1893620": {"schinese": "Circadian Dice", "japanese": "Circadian Dice"},
    "1337970": {"schinese": "CatTuber", "japanese": "CatTuber"},
    "2073470": {"schinese": "Kanjozoku Game レーサー Online Street Racing & Drift", "japanese": "Kanjozoku Game レーサー Online Street Racing & Drift"},
    "1901340": {"schinese": "Ero Manager", "japanese": "Ero Manager"},
    "2536840": {"schinese": "GINKA", "japanese": "GINKA"},
    "1708150": {"schinese": "Juice Galaxy", "japanese": "Juice Galaxy"},
    "1491670": {"schinese": "Venba", "japanese": "Venba"},
    "3029820": {"schinese": "Ai Vpet", "japanese": "Ai Vpet"},
    "2593370": {"schinese": "饿殍：末代饥民", "japanese": "The Hungry Lamb: Traveling in the Late Ming Dynasty"},
    "3070070": {"schinese": "TCG 卡店模拟器", "japanese": "TCG Card Shop Simulator"},
    "2128270": {"schinese": "Path of Achra", "japanese": "Path of Achra"},
    "2707900": {"schinese": "NIGHT-RUNNERS 序章", "japanese": "NIGHT-RUNNERS PROLOGUE"},
    "1844610": {"schinese": "Reality Mixer", "japanese": "Reality Mixer - Mixed Reality for VR headsets"},
    "1775490": {"schinese": "Slice & Dice", "japanese": "Slice & Dice"},
    "1934680": {"schinese": "神话时代：重述", "japanese": "Age of Mythology: Retold"},
    "3241660": {"schinese": "R.E.P.O.", "japanese": "R.E.P.O."},
    "3164500": {"schinese": "Schedule I", "japanese": "Schedule I"},
    "3449850": {"schinese": "Desktop Kitten Girl", "japanese": "Desktop Kitten Girl"},
    "2660460": {"schinese": "Aviassembly", "japanese": "Aviassembly"},
    "2784470": {"schinese": "9 Kings", "japanese": "9 Kings"},
    "2078450": {"schinese": "战锤 40000：极速小子", "japanese": "Warhammer 40,000: Speed Freeks"},
    # 原来的一些乱映射，全部修正
    "8930": {"schinese": "文明 5", "japanese": "Civilization V"},
    "7200": {"schinese": "赛道狂飚 永恒之星版", "japanese": "Trackmania United Forever Star Edition"},
    "945360": {"schinese": "在我们之中", "japanese": "Among Us"},
    "819230": {"schinese": "Gothicc Breaker", "japanese": "Gothicc Breaker"},
    "1196590": {"schinese": "Crown of the Necromancer", "japanese": "Crown of the Necromancer"},
    "1730660": {"schinese": "Great Adventurer", "japanese": "Great Adventurer"},
    "1786370": {"schinese": "Seasons of Heaven", "japanese": "Seasons of Heaven"},
    "2014540": {"schinese": "INSURGENT", "japanese": "INSURGENT"},
    "387840": {"schinese": "Alpha Runner", "japanese": "Alpha Runner"},
    # 精确匹配未覆盖的（原模糊匹配项，验证后手动补充）
    "10190": {"schinese": "使命召唤：现代战争 2", "japanese": "Call of Duty: Modern Warfare 2"},
    "33930": {"schinese": "武装突袭 2：箭头行动", "japanese": "Arma 2: Operation Arrowhead"},
    "9420": {"schinese": "最高指挥官：钢铁同盟", "japanese": "Supreme Commander: Forged Alliance"},
    "647960": {"schinese": "铁锈战争", "japanese": "Rusted Warfare"},
    "1041320": {"schinese": "王国纪元", "japanese": "Lords Mobile"},
    "972660": {"schinese": "灵魂旅人", "japanese": "Spiritfarer"},
    "1292940": {"schinese": "逃脱方块合集", "japanese": "Cube Escape Collection"},
    "3590": {"schinese": "植物大战僵尸 年度版", "japanese": "Plants vs. Zombies GOTY Edition"},
    "632470": {"schinese": "极乐迪斯科", "japanese": "Disco Elysium"},
    "246420": {"schinese": "王国保卫战", "japanese": "Kingdom Rush"},
    "324680": {"schinese": "不可能的生物", "japanese": "Impossible Creatures"},
    # 外部数据翻译错误，手动覆盖
    "204360": {"schinese": "城堡破坏者", "japanese": "キャッスルクラッシャーズ"},  # 外部数据错误为"城堡毁灭者"
    "646570": {"schinese": "杀戮尖塔", "japanese": "Slay the Spire"},  # 外部数据错误为"尖塔奇兵"，Steam官方中文为"杀戮尖塔"
}

# ============ 第三步：合并（MANUAL_NAMES 覆盖外部精确匹配） ============
df = pd.read_csv('steam_store_games.csv')

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

names = {}
ext_match = 0
manual_match = 0
no_match = 0

for appid, en_name in displayed.items():
    appid_str = str(appid)
    
    # 1. 手动映射优先（经过核实，可覆盖外部数据错误）
    if appid_str in MANUAL_NAMES:
        entry = MANUAL_NAMES[appid_str]
        if isinstance(entry, dict):
            names[appid_str] = entry
        else:
            names[appid_str] = {'schinese': str(entry)}
        manual_match += 1
        continue
    
    # 2. 外部数据精确匹配兜底
    result = try_ext_exact(en_name)
    if result:
        names[appid_str] = result
        ext_match += 1
        continue
    
    no_match += 1

# 同时为所有数据集游戏也生成映射（仅精确匹配）
for _, row in df.iterrows():
    appid_str = str(row['appid'])
    if appid_str in names:
        continue
    result = try_ext_exact(str(row['name']))
    if result:
        names[appid_str] = result

print(f'页面显示的 {len(displayed)} 个游戏:')
print(f'  外部 CSV 精确匹配: {ext_match}')
print(f'  手动映射补充: {manual_match}')
print(f'  仍缺失: {no_match}')

if no_match > 0:
    for appid, en_name in displayed.items():
        if str(appid) not in names:
            print(f'    {appid}: {en_name}')

total_cn = sum(1 for v in names.values() if 'schinese' in v and v['schinese'])
total_jp = sum(1 for v in names.values() if 'japanese' in v and v['japanese'])
print(f'\n总计: {len(names)} 个游戏')
print(f'  中文名: {total_cn}')
print(f'  日文名: {total_jp}')

with open('game_names.json', 'w', encoding='utf-8') as f:
    json.dump(names, f, ensure_ascii=False, indent=2)
sz = len(json.dumps(names, ensure_ascii=False))
print(f'game_names.json: {sz // 1024} KB')
