"""Campaign chapters extend the shared scene and dialogue registry."""
from . import chapter2,chapter3,chapter4,chapter5

CHAPTERS=(chapter5,chapter4,chapter2,chapter3)
CHOICES={key:values for chapter in CHAPTERS for key,values in chapter.CHOICES.items()}
ART={key:value for chapter in CHAPTERS for key,value in chapter.ART.items()}
FLAGS=set().union(*(getattr(chapter,'FLAGS',set()) for chapter in CHAPTERS))
INFO={
    1:{'title':'Проверка тормозов','complete':'chapter_complete','next':'c2_departure',
       'result':'Лида и Михаил в вагоне. Следующая станция — Больничная.','next_label':'Ехать к Больничной'},
    2:{'title':'Чужой ток','complete':'c2_complete','next':'c3_departure',
       'result':'Стрелка переведена. Люди из убежища в вагоне. Следующая станция — Рабочий посёлок.',
       'next_label':'Ехать в Рабочий посёлок'},
    3:{'title':'Открытые ворота','complete':'c3_complete','next':'c4_departure',
       'result':'Павел в вагоне. Связь с диспетчером восстановлена. Впереди водосброс и диспетчерская.',
       'next_label':'Ехать к водосбросу'},
    4:{'title':'Личный приказ','complete':'c4_complete','next':'c5_departure',
       'result':'Обход проверен. Валентина принимает управление, Артём готовится выйти к платформенному замку.',
       'next_label':'Выбрать последний маршрут'},
    5:{'title':'Остановка по требованию','complete':'c5_complete','next':None,
       'result':'Рейс окончен.','next_label':None},
}
TRAVEL={'drive':'loop','c1_align':'c1_aligned','c2_travel':'c2_arrival','c3_travel':'c3_arrival','c4_travel':'c4_arrival','c5_travel':'c5_arrival'}

def install(scenes,dialogues,journal,Scene,Object):
    for chapter in CHAPTERS:
        chapter.install(scenes,dialogues,journal,Scene,Object)
    from .chapter4_expansion import install_endings
    install_endings(dialogues)

def interact(session,key):
    for chapter in CHAPTERS:
        result=chapter.interact(session,key)
        if result is not None:return result
    return None

def apply(session,effect):
    for chapter in CHAPTERS:
        if chapter.apply(session,effect):return True
    return False

def objective(session):
    for chapter in CHAPTERS:
        result=chapter.objective(session)
        if result is not None:return result
    return None
