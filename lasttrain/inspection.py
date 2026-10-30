"""Observe the exit geometry before stepping from the stopped train."""
VIEW=(95,210,660,440)
POINTS=(
    ('step','Ступень',(270,760),'Стальная ступень мокрая, но цела. Видна противоскользящая насечка.'),
    ('gap','Межрельсовое пространство',(660,820),'От ступени до края слишком далеко. Под ногами будут балласт и рельсы, а не площадка.'),
    ('landing','Платформа и поручень',(1130,540),'Плиты и поручень целы. Но для выхода нужно подать вагон ближе к площадке.'),
)

def operate(s,action):
    if s.chapter!=1 or s.scene!='cabin' or s.puzzle!='inspection' or 'c1_parked' not in s.flags:return False
    for key,label,pos,description in POINTS:
        if action==key:
            s.flags.add('c1_inspected_'+key);s.say(description);return False
    if action=='rails':
        s.say('На балласт не выходим: перепад высоты и рельсы под ногами. Нужен выход на уровень платформы.');return False
    if action=='platform':
        if not all('c1_inspected_'+p[0] in s.flags for p in POINTS):
            s.say('Сначала осмотрите ступень, пространство под ней и площадку с поручнем.');return False
        s.puzzle=None;s.start_dialogue('c1_disembark');return True
    return False
