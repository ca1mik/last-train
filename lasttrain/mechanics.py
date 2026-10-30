"""Deterministic puzzle rules shared by gameplay, saves and tests."""
from collections import deque

N,E,S,W=0,1,2,3
DELTAS=((0,-1),(1,0),(0,1),(-1,0))

class PowerBoard:
    width=5
    height=4
    source=5
    hospital=4
    gate=19
    # Connections before rotation. Empty tiles cannot be operated.
    sockets={2:(N,E),3:(N,S),4:(W,),5:(E,),6:(N,S),7:(N,E,S),
             8:(N,E),12:(N,S),13:(N,E),17:(N,E),18:(N,S),19:(W,)}
    fixed={4,5,19}
    initial=(0,0,3,0,0,0,2,0,1,0,0,0,1,3,0,0,0,2,0,0)
    solution=(0,0,1,1,0,0,1,2,1,0,0,0,0,3,0,0,0,0,1,0)

    @classmethod
    def validate(cls,rotation):
        return (isinstance(rotation,list) and len(rotation)==20 and
                all(type(n) is int and 0<=n<=3 for n in rotation) and
                all(rotation[i]==0 for i in cls.fixed))

    @classmethod
    def ports(cls,index,rotation):
        return {(direction+rotation[index])%4 for direction in cls.sockets.get(index,())}

    @classmethod
    def rotate(cls,rotation,index,steps=1):
        if index in cls.sockets and index not in cls.fixed:
            rotation[index]=(rotation[index]+steps)%4

    @classmethod
    def powered(cls,rotation,bridge=True):
        fed={cls.source};queue=deque([cls.source])
        while queue:
            i=queue.popleft();x,y=i%cls.width,i//cls.width
            for port in cls.ports(i,rotation):
                dx,dy=DELTAS[port];nx,ny=x+dx,y+dy
                if not(0<=nx<cls.width and 0<=ny<cls.height):continue
                j=ny*cls.width+nx
                if not bridge and {i,j}=={12,17}:continue
                if (port+2)%4 in cls.ports(j,rotation) and j not in fed:
                    fed.add(j);queue.append(j)
        return fed

    @classmethod
    def result(cls,rotation,bridge):
        powered=cls.powered(rotation,bridge)
        if cls.hospital not in powered:
            return False,'Убежище не подключено. Нагрузка осталась на резерве.'
        if cls.gate not in powered:
            if not bridge:
                return False,'Нужна кабельная перемычка в нижней ветви. Ищите катушку во дворе.'
            return False,'Убежище подключено, но привод стрелки пока без питания.'
        return True,'Обе ветви подключены. Теперь можно перевести стрелку.'


class Winch:
    """A pawl must be unloaded before release; a locked turnout cannot be forced."""
    stages=('load','release','turn','lock')
    required_turns=4

    @staticmethod
    def initial():
        return {'stage':'load','turns':0}

    @staticmethod
    def validate(state):
        return (isinstance(state,dict) and set(state)=={'stage','turns'} and
                state['stage'] in Winch.stages and type(state['turns']) is int and
                0<=state['turns']<=Winch.required_turns)

    @staticmethod
    def act(state,action):
        stage=state['stage']
        if stage=='load' and action=='crank':
            state['stage']='release'
            return 'Трос натянут. Теперь освободите собачку.',False
        if stage=='release' and action=='pawl':
            state['stage']='turn'
            return 'Нина держит трос. Вращайте рукоятку.',False
        if stage=='turn' and action=='crank':
            state['turns']+=1
            if state['turns']>=Winch.required_turns:
                state['stage']='lock'
                return 'Стрелка встала. Зафиксируйте замок.',False
            return f'Перевод стрелки: {state["turns"]}/{Winch.required_turns}.',False
        if stage=='lock' and action=='pawl':
            return 'Стрелка зафиксирована. Можно провести состав.',True
        return {'load':'Сначала натяните трос рукояткой.',
                'release':'Нагрузка на тросе. Освободите собачку.',
                'turn':'Замок пока не защёлкнется. Продолжайте вращать рукоятку.',
                'lock':'Не тяните дальше. Зафиксируйте замок.'}[stage],False


class RadioTune:
    ranges=(12,10,4)
    target=(8,4,2)

    @classmethod
    def validate(cls,settings):
        return (isinstance(settings,list) and len(settings)==3 and
                all(type(v) is int and 0<=v<r for v,r in zip(settings,cls.ranges)))

    @classmethod
    def adjust(cls,settings,control,steps=1):
        if type(control) is int and 0<=control<3:
            settings[control]=(settings[control]+steps)%cls.ranges[control]

    @classmethod
    def quality(cls,settings):
        coarse=abs(settings[0]-cls.target[0]);coarse=min(coarse,12-coarse)
        fine=abs(settings[1]-cls.target[1])
        return max(0,min(1,(1-coarse/6)*.65+(1-fine/9)*.25+(.1 if settings[2]==cls.target[2] else 0)))

    @classmethod
    def locked(cls,settings):
        return tuple(settings)==cls.target
