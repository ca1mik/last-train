"""Short world interactions and the changed return route of the first sortie."""
from dataclasses import dataclass
import pygame as pg


@dataclass
class Work:
    kind:str
    scene:str
    target:tuple
    duration:float
    label:str
    progress:float=0


TASKS={'relay':('waiting','relay',1.2,'Поднять жалюзи'),
       'lift':('ward','patient',1.4,'Поднять носилки'),
       'load':('platform','train',1.0,'Передать носилки в вагон')}
TASKS.update({'c2_cable':('shed','cable',.6,'Взять перемычку'),
    'c2_winch':('shed','winch',.7,'Подготовить лебёдку'),
    'c2_receive':('carriage','nina',1.1,'Проверить ввод и освободить проход'),
    'c2_pack':('refuge','supplies',.8,'Приготовить сумку с Лидой'),
    'c2_throw':('hospital','switch',.9,'Перевести привод'),
    'c2_attach':('hospital','switch',1.0,'Установить и натянуть лебёдку'),
    'c2_rhythm':('hospital','switch',1.1,'Крутить на светлой метке'),
    'c2_lock':('hospital','switch',.7,'Зафиксировать замок')})
FLAGS={'action_return_live'}
CABLE=pg.Rect(690,690,120,80)


def task_kind(s,key):
    from .hospital_action import task_kind as hospital_kind
    kind=hospital_kind(s,key)
    if kind is not None:return kind
    if 'action_mode' not in s.flags or s.chapter!=1:return None
    if s.scene=='waiting' and key=='relay' and not s.carrying and 'door_open' not in s.flags:return 'relay'
    if s.scene=='ward' and key=='patient' and 'door_open' in s.flags and not s.carrying and 'rescued' not in s.flags:return 'lift'
    if s.scene=='platform' and key=='train' and s.carrying:return 'load'
    return None


def request(s,key):
    kind=task_kind(s,key)
    if kind is not None:return 'field_'+kind
    if 'action_mode' not in s.flags or s.chapter!=1:return None
    if s.scene=='platform' and key=='lida' and 'rescued' in s.flags:
        s.start_dialogue('a_lida');return True
    return None


def create(kind):
    from .content import SCENES
    scene,key,duration,label=TASKS[kind]
    obj=next(o for o in SCENES[scene].objects if o.id==key)
    return Work(kind,scene,obj.pos,duration,label)


def complete(s,kind):
    if kind.startswith('c2_'):
        from .hospital_action import complete as hospital_complete
        return hospital_complete(s,kind)
    if kind=='relay':
        s.apply('relay_fixed' if 'stopper' in s.flags else 'relay_nina')
        s.say('Нина: Проход открыт. Я иду за носилками.' if 'stopper' in s.flags else 'Нина: Держу рубильник. В аптеку — через дверь справа.')
    elif kind=='lift':
        s.apply('carry');s.flags.add('action_return_live')
        s.say('Нина: Кабель в зале искрит. Обойдите его по нижнему проходу. Я догоню у поезда.')
    elif kind=='load':
        s.carrying=False;s.flags.add('rescued')
        s.say('Михаил в вагоне. Лида у ступеней — позовите её перед отправлением.')


def cable_phase(elapsed):
    phase=elapsed%6.4
    return 'warning' if phase<1 else 'live' if phase<1.8 else 'safe'


def cable_present(s):
    return s.scene=='waiting' and 'action_return_live' in s.flags and 'rescued' not in s.flags


def cable_touches(points):
    return any(CABLE.inflate(28,28).collidepoint(point) for point in points)


def install(dialogues,journal):
    dialogues['a_lida']={'lines':[
        ('Лида','Михаил в вагоне. Я поеду с ним.'),
        ('Лида','В прошлый раз ты тоже видел нас у поезда. Сейчас скажешь, что случилось?')],
        'choices':[('Сказать, что испугался и проехал мимо.','a_admit'),
                   ('Сослаться на приказ диспетчера.','a_order'),
                   ('Помочь ей подняться; поговорить позже.','a_hand')]}
    dialogues['a_admit']={'lines':[('Артём','Я видел людей. Испугался воды и не остановился.'),
        ('Лида','Я услышала. Сейчас довези Михаила. Остальное — потом.')],'effect':'admit'}
    dialogues['a_order']={'lines':[('Артём','Диспетчер приказала проходить. Я выполнил приказ.'),
        ('Лида','Твой голос по громкоговорителю я помню. Можем поговорить в дороге.')],'effect':'order'}
    dialogues['a_hand']={'lines':[('Артём','Возьмитесь за руку. Здесь мокрая ступень.'),
        ('Лида','Возьмусь. Разговор мы ещё не закончили.')],'effect':'hand'}
    journal['action_return_live']=('Обратный путь','В зале повреждён кабель: перед разрядом он загорается янтарным. Нижний проход позволяет обойти повреждённый участок с носилками.')
