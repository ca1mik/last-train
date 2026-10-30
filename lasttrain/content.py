"""Authored chapter data. Coordinates are in world pixels, not screen pixels."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Object:
    id: str
    label: str
    pos: tuple
    kind: str = 'prop'
    requires: str = ''

@dataclass(frozen=True)
class Scene:
    title: str
    size: tuple
    start: tuple
    walls: tuple
    objects: tuple
    lights: tuple = ()
    walk_polygon: tuple = ()
    obstacles: tuple = ()
    actor_scale: float = 1.0
    art_crop: tuple = ()

def inside_polygon(point, polygon):
    if not polygon:return True
    x,y=point;inside=False
    j=len(polygon)-1
    for i,(xi,yi) in enumerate(polygon):
        xj,yj=polygon[j]
        if (yi>y)!=(yj>y) and x < (xj-xi)*(y-yi)/(yj-yi)+xi:inside=not inside
        j=i
    return inside

def segments_intersect(a,b,c,d):
    def cross(p,q,r):return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    if max(a[0],b[0])<min(c[0],d[0]) or max(c[0],d[0])<min(a[0],b[0]):return False
    if max(a[1],b[1])<min(c[1],d[1]) or max(c[1],d[1])<min(a[1],b[1]):return False
    return cross(a,b,c)*cross(a,b,d)<=0 and cross(c,d,a)*cross(c,d,b)<=0

def polygon_blocks_box(polygon,corners):
    if any(inside_polygon(p,polygon) for p in corners):return True
    left,top=corners[0];right,bottom=corners[2]
    if any(left<=x<=right and top<=y<=bottom for x,y in polygon):return True
    return any(segments_intersect(corners[i],corners[(i+1)%4],polygon[j],polygon[(j+1)%len(polygon)])
               for i in range(4) for j in range(len(polygon)))

def walkable(scene,pos,radius=14):
    x,y=pos;w,h=scene.size
    if not(radius<=x<=w-radius and radius<=y<=h-radius):return False
    corners=((x-radius,y-radius),(x+radius,y-radius),(x+radius,y+radius),(x-radius,y+radius))
    if any(not inside_polygon(p,scene.walk_polygon) for p in corners):return False
    if any(wx<x+radius and wx+ww>x-radius and wy<y+radius and wy+wh>y-radius for wx,wy,ww,wh in scene.walls):return False
    return not any(polygon_blocks_box(p,corners) for p in scene.obstacles)

def clear_sight(scene,a,b):
    polygons=list(scene.obstacles)+[((x,y),(x+w,y),(x+w,y+h),(x,y+h)) for x,y,w,h in scene.walls]
    return not any(inside_polygon(a,p) or inside_polygon(b,p) or
                   any(segments_intersect(a,b,p[i],p[(i+1)%len(p)]) for i in range(len(p))) for p in polygons)

SCENE_ART={'platform':'concepts/station-v01.png','cabin':'environments/cabin-v01.png','carriage':'environments/carriage-v01.png',
           'waiting':'environments/waiting-v01.png','ward':'environments/ward-v01.png',
           'workshop':'environments/workshop-v01.png'}

SCENES = {
    'cabin': Scene('Кабина • Белореченск', (1672, 941), (850, 700),
        ((450,350,180,180),(960,350,180,180)),
        (Object('window', 'Лобовое стекло', (1140, 500), 'window'),
         Object('controls', 'Пульт машиниста', (790, 535), 'console'),
         Object('radio', 'Радиостанция', (1260, 510), 'radio'),
         Object('tea', 'Два стакана', (395, 520), 'tea'),
         Object('cabin_door', 'Дверь кабины', (1270, 740), 'door')),
        ((790,535,230,(236,181,104)),),
        ((380,490),(1280,490),(1310,820),(1080,850),(1080,895),(500,895),(500,850),(270,840)),actor_scale=1.7),
    'platform': Scene('Служебная платформа', (1672, 941), (650, 580),
        ((0, 0, 575, 610), (890, 0, 782, 315), (1210, 315, 462, 190),
         (1530, 505, 142, 150), (835, 400, 145, 70)),
        (Object('train', 'Подняться в поезд', (600, 545), 'train'),
         Object('lida', 'Женщина с фонарём', (760, 590), 'lida'),
         Object('station_door', 'Зал ожидания', (1430, 620), 'door'),
         Object('sign', 'Расписание', (800, 330), 'sign'),
         Object('signal', 'Красный сигнал', (700, 230), 'signal'),
         Object('bench', 'Скамья', (1000, 500), 'bench')),
        ((540, 520, 230, (231, 171, 92)), (1430, 570, 200, (231, 171, 92))),
        ((0,0),(1672,0),(1672,941),(1280,941),(0,288))),
    'waiting': Scene('Зал ожидания', (1672, 941), (180, 800),(),
        (Object('exit', 'На платформу', (115, 750), 'door'),
         Object('bell', 'Ручной звонок', (230, 630), 'bell'),
         Object('boot', 'Детский сапог', (515, 325), 'boot'),
         Object('relay', 'Щит жалюзи', (1330, 320), 'relay'),
         Object('workshop_door', 'Мастерская', (1540, 750), 'door'),
         Object('ward_door', 'Дверь аптеки', (1440, 470), 'door')),
        ((180,750,130,(221,167,100)),(1330,300,160,(105,156,139))),
        ((420,245),(1360,260),(1640,900),(70,900),(90,690)),
        (((805,303),(865,306),(865,385),(1030,520),(1030,638),(980,639),(800,466)),),actor_scale=1.7),
    'workshop': Scene('Мастерская дежурного', (1536,1024), (350,700),(),
        (Object('exit', 'В зал ожидания', (250,620), 'door'),
         Object('stopper', 'Ящик со стальным стопором', (970,600), 'tool'),
         Object('note', 'Записка дежурного', (1180,640), 'paper')),
        (),((130,600),(310,520),(640,470),(1110,580),(1340,630),(1370,680),
            (1290,870),(1270,980),(530,980),(350,880),(270,840),(140,710)),actor_scale=1.7),
    'ward': Scene('Аптека • служебное помещение', (1536,1024), (300,730),(),
        (Object('exit', 'В зал ожидания', (170,670), 'door'),
         Object('patient', 'Михаил', (1030,680), 'patient'),
         Object('nina', 'Нина', (620,570), 'nina'),
         Object('cabinet', 'Аптечный шкаф', (440,500), 'cabinet')),
        (),((240,530),(310,480),(540,480),(600,450),(1180,450),(1220,530),
            (1340,580),(1430,820),(1480,980),(60,980),(60,680),(210,620)),actor_scale=1.7),
    'carriage': Scene('Пассажирский вагон', (1536,720), (320,600),(),
        (Object('nina', 'Нина', (520,520), 'nina'),
         Object('lida', 'Лида', (900,640), 'lida'),
         Object('patient', 'Михаил', (1140,615), 'patient'),
         Object('map', 'Схема линии', (1280,550), 'map'),
         Object('cabin', 'В кабину', (175,600), 'door')),
        (),((245,455),(1180,480),(1340,520),(1360,600),(1460,650),(1470,700),
            (80,700),(90,650),(170,490)),actor_scale=2.1,art_crop=(0,0,1536,720)),
}

# A line is (speaker, text). A choice is (text, following dialogue id).
DIALOGUES = {
 'opening': {'lines': [('Нина', 'Откроешь?'), ('Артём', 'С другой стороны ручка.'),
    ('Нина', 'Я знаю, как работают двери.')], 'effect': 'opening'},
 'meet_nina': {'lines': [('Нина', 'До служебной платформы. Снимем опоры, проверим проход. И назад.'),
    ('Артём', 'Там восемнадцать лет никто не ездил.'), ('Нина', 'Поэтому я и позвала машиниста.'),
    ('', 'Она кладёт папку на пульт. Артём отодвигает её от горячей трубы.')], 'effect': 'nina_boarded'},
 'tea': {'lines': [('', 'Два стакана в подстаканниках. Один чай почти чёрный. Другой — совсем светлый.'),
    ('Артём', 'Не забыл.')], 'effect': 'tea'},
 'departure': {'lines': [('Нина', 'Давление держится. Впереди зелёный.'),
    ('Артём', 'Проверка тормозов. Держись за поручень.')], 'effect': 'drive'},
 'loop': {'lines': [('Валентина · радио', 'Сорок седьмой, проверка связи.'),
    ('Артём', 'Маневровый двенадцать. Мы по заявке управления.'),
    ('Валентина · радио', 'Сорок седьмой. Подтвердите число людей.'),
    ('Нина', 'Ты её включал?'), ('', 'За стеклом снова проходит столб с красной тряпкой.'),
    ('Нина', 'Останови. Мы уже здесь были.')], 'effect': 'arrive'},
 'radio': {'lines': [('', 'Тумблер в положении «Выкл». В динамике слышен чей-то вдох.')], 'effect': 'radio'},
 'window': {'lines': [('', 'На изоляторе висит красная тряпка. Она не двигается, хотя дождь идёт наискосок.')], 'effect': 'window'},
 'lida_intro': {'lines': [('Лида', 'Двигатель не глушите. Здесь звук дальше света ходит.'),
    ('', 'Женщина смотрит на табличку тепловоза, затем на Артёма.'),
    ('Лида', 'Другого не было?'), ('Артём', 'Поезда?'), ('Лида', 'Машиниста.'),
    ('Лида', 'В аптеке человек. Нога сломана, один не выйдет. Боковую дверь перекосило.'),
    ('Нина', 'Я возьму носилки.'), ('Лида', 'Там ступени, ты не знаешь…'),
    ('Нина', 'Покажете.')], 'effect': 'met_lida'},
 'lida_reminder': {'lines': [('Лида', 'Щит в дальнем конце зала. Только сперва послушайте. Если там кто-то есть — уведите звуком.') ]},
 'sign': {'lines': [('', '23:47. Служебный №47. В графе «Остановка» прочерк. Бумага сухая под разбитым стеклом.')], 'effect': 'sign'},
 'signal': {'lines': [('Артём', 'Красный. Пока не разберёмся, состав стоит.') ]},
 'bench': {'lines': [('', 'На скамье остался прямоугольник сухого дерева, будто кто-то только что встал.') ]},
 'boot': {'lines': [('', 'Один детский сапог. Внутри вода. Вокруг него — сухой пол.'),
    ('', 'Артём ставит сапог ближе к батарее. Она холодная.')], 'effect': 'boot'},
 'relay_choice': {'lines': [('Артём', 'Пружина не держит. Отпущу рубильник — дверь снова упадёт.'),
    ('Нина · рация', 'Могу подержать. Ты проведёшь Лиду.')],
    'choices': [('Попросить Нину удерживать рубильник.', 'relay_nina'),
                ('Поискать стопор в мастерской.', 'relay_tool')]},
 'relay_nina': {'lines': [('Артём', 'Держи. Я обойду через коридор.'),
    ('Нина', 'Поняла. Пока не выведешь человека, не отпускаю.')], 'effect': 'relay_nina'},
 'relay_tool': {'lines': [('Артём', 'Здесь должна быть мастерская. Если найду стопор, руки будут свободны.'),
    ('Нина', 'Я у пациента. Позови, если понадобится.')], 'effect': 'seek_stopper'},
 'stopper': {'lines': [('', 'В ящике под верстаком — тяжёлый стальной стопор. На рукоятке свежий след от ладони.')], 'effect': 'stopper'},
 'relay_fixed': {'lines': [('', 'Стопор встаёт в паз. За стеной медленно поднимаются жалюзи.'),
    ('Нина · рация', 'Проход открыт. Мы в аптеке.')], 'effect': 'relay_fixed'},
 'note': {'lines': [('', '«Ворота открыл вручную. Ждите у служебной. Паша». Ниже чужой рукой: «Поезд не остановился».'),
    ('Артём', 'Ворота были открыты…')], 'effect': 'note'},
 'patient': {'lines': [('Михаил', 'Вы за мной?'), ('Артём', 'За вами.'),
    ('Михаил', 'Тогда не слушайте, если буду ругаться. Это я от боли.'),
    ('Лида', 'С этой стороны порог выше. Я первая.'), ('Артём', 'Давайте я.'),
    ('Лида', 'Только не отпускайте.'), ('Артём', 'Скажите, когда.')], 'effect': 'carry'},
 'nina_ward': {'lines': [('Нина', 'Не торопись у поворота. Носилки шире, чем кажутся.') ]},
 'cabinet': {'lines': [('', 'Лида оставила бинт и чистую воду. Можно перевязать руку.')], 'effect': 'heal'},
 'lida_refusal': {'lines': [('Артём', 'Садитесь.'),
    ('Лида', 'Вы тогда тоже это сказали. Через громкоговоритель.'),
    ('', 'Она не берётся за поручень. За станцией звенит оставленный вами звонок.')],
    'choices': [('«Я видел вас на платформе».', 'admit'),
                ('«Мне приказали ехать».', 'order'),
                ('Отойти от ступеней и молча протянуть руку.', 'hand')]},
 'admit': {'lines': [('Лида', 'Нет. Вы видели людей. Меня вы сейчас видите.'),
    ('Артём', 'До следующей станции довезу.'), ('Лида', 'До следующей — довезите.')], 'effect': 'admit'},
 'order': {'lines': [('Лида', 'Я не спрашивала, чей был приказ.'),
    ('', 'Артём убирает руку с поручня и отходит, освобождая проход.'),
    ('Артём', 'До следующей станции довезу.'), ('Лида', 'До следующей — довезите.')], 'effect': 'order'},
 'hand': {'lines': [('', 'Лида смотрит на его ладонь. Артём не отводит взгляда.'),
    ('Артём', 'До следующей станции довезу.'), ('Лида', 'До следующей — довезите.')], 'effect': 'hand'},
 'nina_after': {'lines': [('', 'Нина ставит рядом второй стакан.'), ('Нина', 'Ты её помнишь?'),
    ('Артём', 'Лицо — нет.'), ('Нина', 'А платформу?'), ('', 'Чай дрожит. Артём придерживает стакан.'),
    ('Артём', 'Платформу помню.')], 'effect': 'nina_after'},
 'lida_after': {'lines': [('Лида', 'Сумка та же. Всё собиралась поменять. У новой карманы не там.'),
    ('Артём', 'Ручку бы перешить.'), ('Лида', 'Перешиваю. Каждый год.')], 'effect': 'lida_after'},
 'patient_after': {'lines': [('Михаил', 'Не знаю, что у вас произошло. Но вы пришли. Спасибо.')], 'effect': 'patient_after'},
 'map': {'lines': [('', 'Следующая станция — Больничная. На старой схеме линия обрывается у водосброса.'),
    ('Валентина · радио', 'Сорок седьмой, впереди свободно. Служебную проходите без остановки.'),
    ('', 'Артём выключает радиостанцию. Голос заканчивает фразу из громкоговорителя за окном.')], 'effect': 'chapter_complete'},
}

JOURNAL = {
 'met_lida': ('Лида', 'В аптеке раненый. Щит жалюзи находится в дальнем конце зала ожидания.'),
 'boot': ('Сапог', 'Мокрый сапог на сухом полу. Кто-то оставил его у выхода.'),
 'note': ('Открытые ворота', 'Паша открыл ворота вручную. Артём думал, что проход был закрыт.'),
 'relay_nina': ('Общее дело', 'Нина удерживает рубильник. Нужно забрать Михаила из аптеки.'),
 'relay_fixed': ('Стопор', 'Жалюзи зафиксированы. Можно переносить Михаила.'),
 'rescued': ('Михаил в вагоне', 'Он жив. Лида всё ещё стоит на платформе.'),
 'lida_boarded': ('До следующей', 'Лида согласилась ехать. Она помнит тот состав.'),
 'nina_after': ('Разговор', 'Нина спросила о платформе. Я ответил.'),
}

from .chapters.chapter1_expansion import install as expand_opening
expand_opening(DIALOGUES,JOURNAL)
from .combat import install as install_action
install_action(DIALOGUES,JOURNAL)
from .fieldwork import install as install_fieldwork
install_fieldwork(DIALOGUES,JOURNAL)
from .chapters import install as install_chapters
install_chapters(SCENES,DIALOGUES,JOURNAL,Scene,Object)
from .chapters import ART as CHAPTER_ART
SCENE_ART.update(CHAPTER_ART)
from .hospital_action import install as install_hospital_action
install_hospital_action(DIALOGUES,JOURNAL)
