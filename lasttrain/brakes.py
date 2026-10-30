"""A readable, reduced pneumatic test for the game's fictional service train."""
import math

class BrakeTest:
    stages=('charge','apply','release','done')
    valves=('hold','charge','apply','release')

    @staticmethod
    def initial(completed=False):
        return {'stage':'done' if completed else 'charge','valve':'release' if completed else 'hold',
                'compressor':completed,'line':5.0 if completed else 0.0,'cylinder':0.0}

    @classmethod
    def validate(cls,b):
        return (isinstance(b,dict) and set(b)=={'stage','valve','compressor','line','cylinder'}
                and b['stage'] in cls.stages and b['valve'] in cls.valves
                and type(b['compressor']) is bool
                and all(type(b[k]) in (int,float) and math.isfinite(b[k]) and 0<=b[k]<=limit
                        for k,limit in (('line',5),('cylinder',3))))

    @staticmethod
    def approach(value,target,speed,dt):
        return value+max(-speed*dt,min(speed*dt,target-value))

    @classmethod
    def step(cls,b,dt):
        if b['stage']=='done':return
        valve=b['valve'];dt=max(0,dt)
        if valve in ('charge','release'):
            if b['compressor']:b['line']=cls.approach(b['line'],5,1.2,dt)
            b['cylinder']=cls.approach(b['cylinder'],0,1.5,dt)
        elif valve=='apply':
            # Air already in the line permits a brake application without pump power.
            target=min(3,b['line'])
            b['cylinder']=cls.approach(b['cylinder'],target,1.0,dt)
            if b['line']>3.5:b['line']=cls.approach(b['line'],3.5,.5,dt)

    @classmethod
    def act(cls,b,action):
        if b['stage']=='done':return 'Проверка уже завершена.',False
        if action=='compressor':
            b['compressor']=not b['compressor']
            return ('Компрессор включён.' if b['compressor'] else 'Компрессор выключен.'),False
        if action in cls.valves:
            b['valve']=action
            return {'hold':'Рукоятка перекрыта. Показания удерживаются.',
                    'charge':'Зарядка магистрали. Дождитесь 5 бар.',
                    'apply':'Торможение. Проверьте рост давления в цилиндре.',
                    'release':'Отпуск. Проверьте цилиндр и восстановление магистрали.'}[action],False
        if action!='observe':return 'Неизвестное действие.',False
        stage=b['stage']
        if stage=='charge':
            if b['line']<4.8 or b['cylinder']>.15:return 'Нужна заряженная магистраль: около 5 бар, цилиндр — около нуля.',False
            b['stage']='apply';return 'Магистраль заряжена. Теперь выполните пробное торможение.',False
        if stage=='apply':
            if b['valve']!='apply' or b['cylinder']<2.8 or b['line']>4:return 'Торможение не подтверждено: цилиндр должен подняться к 3 бар, магистраль — снизиться.',False
            b['stage']='release';return 'Цилиндр набрал давление. Отпустите тормоз и проверьте оба прибора.',False
        if b['valve']!='release' or b['cylinder']>.15 or b['line']<4.8:
            return 'Отпуск не подтверждён: цилиндр должен вернуться к нулю, магистраль — к 5 бар.',False
        b['stage']='done';return 'Зарядка, торможение и отпуск подтверждены. Нина проверит хвост состава.',True

def operate(s,action):
    if s.chapter!=1 or s.scene!='cabin' or s.puzzle!='brake':return False
    message,done=BrakeTest.act(s.brake,action);s.say(message)
    if done:
        s.flags.add('c1_brake_ready');s.puzzle=None;s.start_dialogue('c1_brake_ready')
    return done
