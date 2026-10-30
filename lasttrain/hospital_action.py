"""The second sortie: short working replies and a winch operated in the world."""
from .mechanics import Winch

BEAT_PERIOD=1.1
BEAT_WINDOW=(.40,.72)
WORK_KINDS={'c2_attach','c2_rhythm','c2_lock'}
ALIASES={key:'c2_a_'+key[3:] for key in ('c2_departure','c2_arrival','c2_intro','c2_refuge',
    'c2_refuge_reminder','c2_receiving','c2_receiving_done','c2_pack','c2_need_receiving',
    'c2_need_pack','c2_cable','c2_winch','c2_gate_manual','c2_gate_electric','c2_boarding','c2_boarding_named')}
MOBILE=set(ALIASES.values())-{'c2_a_departure','c2_a_arrival','c2_a_boarding','c2_a_boarding_named'}


def dialogue_key(s,key):
    return ALIASES.get(key,key) if 'action_mode' in s.flags else key


def task_kind(s,key):
    if 'action_mode' not in s.flags or s.chapter!=2:return None
    f=s.flags
    if s.scene=='shed':
        if key=='cable' and 'c2_cable' not in f:return 'c2_cable'
        if key=='winch' and 'c2_winch' not in f:return 'c2_winch'
    if s.scene=='carriage' and key=='nina' and 'c2_refuge' in f and not {'c2_receiving_ready','c2_boarded'}&f:return 'c2_receive'
    if s.scene=='refuge' and key=='supplies' and 'c2_refuge' in f and 'c2_pack_ready' not in f:return 'c2_pack'
    if s.scene=='hospital' and key=='switch' and 'c2_refuge' in f and 'c2_gate_open' not in f:
        if 'c2_power_ready' in f:return 'c2_throw'
        if 'c2_winch' in f:
            return 'c2_lock' if s.winch['stage']=='lock' else 'c2_rhythm' if s.winch['stage']=='turn' else 'c2_attach'
    return None


def request(s,key):
    kind=task_kind(s,key)
    return 'field_'+kind if kind is not None else None


def complete(s,kind):
    if kind=='c2_attach':
        if s.winch['stage']=='load':Winch.act(s.winch,'crank')
        if s.winch['stage']=='release':Winch.act(s.winch,'pawl')
        s.say('Нина: Страхую. Нажимай E на светлой метке; четыре рабочих хода, затем замок.')
        return 'c2_rhythm'
    if kind=='c2_lock':
        _,done=Winch.act(s.winch,'pawl')
        if done:s.choices['power_route']='manual';s.apply('c2_gate_open');s.start_dialogue('c2_gate_manual')
    elif kind=='c2_throw':
        s.choices['power_route']='electric';s.apply('c2_gate_open');s.start_dialogue('c2_gate_electric')
    else:
        key={'c2_receive':'c2_receiving','c2_pack':'c2_pack','c2_cable':'c2_cable','c2_winch':'c2_winch'}[kind]
        # Completed work is persistent even while its brief confirmation is playing.
        effect='c2_receiving_ready' if kind=='c2_receive' else 'c2_pack_ready' if kind=='c2_pack' else kind
        s.apply(effect);s.start_dialogue(key)
        if kind=='c2_pack':s.health=100
    return None


def beat_phase(task):return (task.progress%BEAT_PERIOD)/BEAT_PERIOD


def beat_ready(task):return BEAT_WINDOW[0]<=beat_phase(task)<=BEAT_WINDOW[1]


def pulse(s,task):
    if not beat_ready(task):
        task.progress=0;s.say('Не попали в ритм. Подождите светлую метку и нажмите E снова.');return False
    Winch.act(s.winch,'crank');task.progress=0
    s.say('Четыре хода. Теперь удерживайте E, чтобы зафиксировать замок.' if s.winch['stage']=='lock' else f'Нина: Держу. Ход {s.winch["turns"]}/4.')
    return True


def deployed(s,task=None):
    return (s.chapter==2 and s.scene=='hospital' and 'action_mode' in s.flags and 'c2_winch' in s.flags
            and (s.winch['stage']!='load' or task is not None and task.kind=='c2_attach')
            and s.choices.get('power_route')!='electric')


def positions(s):
    from .content import SCENES
    anchor=next(o.pos for o in SCENES[s.scene].objects if o.id=='switch')
    return (anchor[0]-38,anchor[1]+59),(anchor[0]-100,anchor[1]+77)


def work_position(s):
    from .content import SCENES
    anchor=next(o.pos for o in SCENES[s.scene].objects if o.id=='switch')
    return (anchor[0],anchor[1]+60)


def install(dialogues,journal):
    lines={
      'c2_departure':[('Нина','Следующая — Больничная. Там ждут люди. Проверим путь на месте.'),('Артём','Поехали.')],
      'c2_arrival':[('Нина','Стрелка в тупик. Нужно выйти и открыть путь.'),('Лида','В окнах свет. Проверю убежище.')],
      'c2_intro':[('Нина','Генератор питает убежище и стрелку. У людей аппарат — свет не трогаем.'),
        ('Нина','В складе перемычка и лебёдка. Либо соединим оба контура, либо переведём вручную.'),('Артём','Я за инструментом.')],
      'c2_refuge':[('Лида','Четверо соседей. Трое идут сами, четвёртому нужен аппарат.'),
        ('Лида','Откройте путь. С Ниной проверьте ввод в вагоне; потом подойдите к моей сумке у двери.'),
        ('Лида','Человека и переносной источник оставьте мне. Свет здесь не выключайте.')],
      'c2_refuge_reminder':[('Лида','Нужны путь, проверенный ввод в вагоне и моя сумка у шкафа. Я остаюсь с людьми.')],
      'c2_receiving':[('Нина','Ввод проверен. Кабель закреплён, проход свободен.'),('Михаил','Мою сумку убрали под сиденье. Я помню.')],
      'c2_receiving_done':[('Нина','Здесь готово. Ждём Лиду и открытый путь.')],
      'c2_pack':[('Лида','Сумка проверена. Поставь у выхода — понесёшь по моему сигналу.'),('Раиса','Я тоже готова. Очки нашла.')],
      'c2_need_receiving':[('Лида','Путь готов. Теперь проверьте с Ниной ввод и проход в вагоне.')],
      'c2_need_pack':[('Лида','Осталась моя сумка у шкафа. Подойди, я покажу.')],
      'c2_cable':[('Нина · рация','Целая перемычка. Соедини обе ветви на отключённой схеме; убежище остаётся на резерве.')],
      'c2_winch':[('Нина · рация','Лебёдку к стрелке. Я застрахую трос; крути на светлой метке.')],
      'c2_gate_manual':[('Нина','Замок держит. Можно отпустить.'),('Артём','Свет в убежище горит. Зови Лиду.')],
      'c2_gate_electric':[('Нина','Есть контроль. Обе ветви держатся.'),('Артём','Путь открыт, свет оставили. За людьми.')],
      'c2_boarding':[('Лида','Трое идут с Ниной. Я остаюсь с четвёртым, аппарат проверен.'),
        ('','Люди переходят в вагон. Лида проверяет человека на новом месте.'),
        ('Лида','В прошлый раз ваш поезд был так близко — я различала занавеску.'),
        ('','Артём смотрит на окно кабины. Занавески не было. Только полотенце.')],
      'c2_boarding_named':[('Лида','Раиса Ильинична, карточка у вас?'),('Раиса','Во внутреннем кармане. Адрес объясню сама.')],
    }
    lines['c2_boarding_named']+=lines['c2_boarding']
    for source,target in ALIASES.items():
        dialogues[target]={**dialogues[source],'lines':lines[source]}

