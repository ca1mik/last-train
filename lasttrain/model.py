"""Story state and persistence, independent from renderer and input devices."""
import json
import math
import os
import copy
from pathlib import Path
from .content import SCENES, DIALOGUES, JOURNAL, walkable
from . import chapters
from .mechanics import PowerBoard, Winch, RadioTune
from .brakes import BrakeTest

SCHEMA = 14
DEFAULT_SAVE = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'LastTrain' / 'chapter-save.json'

class Session:
    def __init__(self):
        self.scene = 'cabin'
        self.pos = list(SCENES[self.scene].start)
        self.flags = set()
        self.choices = {}
        self.dialogue = None
        self.line = 0
        self.health = 100
        self.flares = 3
        self.elapsed = 0.0
        self.carrying = False
        self.carry_rear = None
        self.notice = ''
        self.notice_time = 0.0
        self.checkpoint = None
        self.chapter = 1
        self.power = list(PowerBoard.initial)
        self.winch = Winch.initial()
        self.puzzle = None
        self.radio = [0,0,0]
        self.signal_pattern = 0
        self.line_power = True
        self.brake=BrakeTest.initial()

    def say(self, text):
        self.notice, self.notice_time = text, 5.0

    def start_dialogue(self, key):
        from .hospital_action import dialogue_key
        key=dialogue_key(self,key)
        if key not in DIALOGUES:
            raise ValueError('Unknown dialogue: ' + key)
        self.dialogue, self.line = key, 0

    def advance(self):
        if not self.dialogue:
            return None
        data = DIALOGUES[self.dialogue]
        if self.line < len(data['lines']) - 1:
            self.line += 1
            return None
        if data.get('choices'):
            self.line = len(data['lines'])
            return None
        effect = data.get('effect')
        self.dialogue = None
        if effect:
            self.apply(effect)
        return effect

    def choose(self, index):
        if not self.dialogue:
            return
        data = DIALOGUES[self.dialogue]
        if self.line < len(data['lines']):
            return
        options = data.get('choices', [])
        if 0 <= index < len(options):
            self.start_dialogue(options[index][1])

    def enter(self, scene, pos=None):
        self.carry_rear=None
        self.scene = scene
        self.pos = list(pos or SCENES[scene].start)

    def apply(self, effect):
        if effect=='drive' and self.brake['stage']!='done':
            raise ValueError('Сначала завершите проверку тормозов')
        self.flags.add(effect)
        if chapters.apply(self,effect):return
        if effect=='c1_brake_started':self.puzzle='brake'
        if effect=='c1_stop':self.enter('cabin')
        if effect == 'arrive':
            self.enter('platform')
        elif effect == 'relay_nina':
            self.flags.add('door_open')
        elif effect == 'relay_fixed':
            self.flags.add('door_open')
        elif effect == 'carry':
            self.carrying = True
            self.say('Михаил на носилках. Вернитесь через зал к поезду. Идите осторожно.')
        elif effect in ('admit', 'order', 'hand'):
            self.choices['lida'] = effect
            self.flags.add('lida_boarded')
            self.enter('carriage')
        elif effect == 'heal':
            self.health = 100

    def objective(self):
        campaign=chapters.objective(self)
        if campaign is not None:return campaign
        f = self.flags
        if 'chapter_complete' in f:
            return 'Глава пройдена • путь к Больничной открыт'
        if 'lida_boarded' in f:
            return 'Поговорить с Ниной, затем проверить схему линии'
        if 'rescued' in f:
            return 'Выйти на платформу и поговорить с Лидой'
        if self.carrying:
            return 'Перенести Михаила к поезду'
        if 'door_open' in f:
            return 'Забрать раненого из аптеки'
        if 'stopper' in f:
            return 'Установить стопор в щит жалюзи'
        if 'seek_stopper' in f:
            return 'Найти стопор в мастерской'
        if 'met_lida' in f:
            return 'Пройти зал ожидания и осмотреть щит'
        if 'arrive' in f:
            return 'Поговорить с женщиной на платформе'
        if 'c1_stop' in f:
            return 'Осмотреть выход у двери кабины' if 'c1_parked' in f else 'Закрепить состав у пульта перед выходом'
        if 'c1_brake_ready' in f:
            return 'Тормоза проверены • подтвердить отправление у пульта'
        if 'nina_boarded' in f:
            return 'Проверить тормоза у пульта'
        if 'opening' in f:
            return 'Открыть дверь Нине'
        return 'Прислушаться к стуку в дверь'

    def journal(self):
        return [entry for flag, entry in JOURNAL.items() if flag in self.flags]

    def interact(self, key):
        if self.dialogue:
            return
        if key=='raisa' and 'c2_boarded' in self.flags and self.scene in ('carriage','upper_platform'):
            if self.scene=='upper_platform':dialogue='c5_raisa_upper'
            elif self.chapter==2:dialogue='c2_raisa_card' if 'c2_card_written' in self.flags else 'c2_raisa_no_card'
            else:dialogue=f'c{self.chapter}_raisa_train'
            self.start_dialogue(dialogue);return True
        from .hospital_action import request as hospital_request
        hospital_event=hospital_request(self,key)
        if hospital_event is not None:return hospital_event
        campaign=chapters.interact(self,key)
        if campaign is not None:return campaign
        from .fieldwork import request as field_request
        field_event=field_request(self,key)
        if field_event is not None:return field_event
        f, scene = self.flags, self.scene
        if scene == 'cabin':
            if key == 'cabin_door':
                if 'arrive' in f:
                    self.enter('platform')
                elif 'c1_stop' in f:
                    if 'c1_parked' in f:self.puzzle='inspection';return 'inspection'
                    self.say('Перед выходом закрепите состав у пульта.')
                else:
                    self.start_dialogue('meet_nina')
            elif key == 'controls':
                if 'nina_boarded' not in f:
                    self.say('Сначала откройте дверь Нине.')
                elif 'arrive' in f:
                    self.say('Сначала нужно помочь людям на станции.')
                elif 'c1_stop' in f:
                    if 'c1_parked' not in f:self.start_dialogue('c1_parked')
                    else:self.say('Состав закреплён. Осмотрите выход у двери.')
                elif 'c1_brake_started' in f and 'c1_brake_ready' not in f:
                    self.puzzle='brake';return 'brake'
                else:
                    self.start_dialogue('c1_brake_ready' if 'c1_brake_ready' in f else 'departure')
            elif key in ('tea', 'radio', 'window'):
                self.start_dialogue(key)
        elif scene == 'platform':
            if key == 'lida':
                self.start_dialogue('lida_refusal' if 'rescued' in f else 'lida_reminder' if 'met_lida' in f else 'lida_intro')
            elif key == 'station_door':
                if 'met_lida' in f:
                    self.enter('waiting')
                else:
                    self.say('Женщина у поезда зовёт вас. Сначала поговорите с ней.')
            elif key == 'train':
                if self.carrying:
                    self.carrying = False
                    self.flags.add('rescued')
                    self.say('Михаил в вагоне. Лида осталась у ступеней. Поговорите с ней.')
                elif 'rescued' in f:
                    self.say('Лида ещё на платформе. Подойдите к ней.')
                else:
                    self.enter('cabin')
            elif key in ('sign', 'signal', 'bench'):
                self.start_dialogue(key)
        elif scene == 'waiting':
            if key == 'exit':
                self.enter('platform', (1390, 650))
            elif key == 'workshop_door':
                self.enter('workshop')
            elif key == 'ward_door':
                if 'door_open' in f:
                    self.enter('ward')
                else:
                    self.say('Жалюзи опущены. Щит в дальнем конце зала.')
            elif key == 'relay':
                if self.carrying:
                    self.say('Нина держит рубильник. Сейчас нужно вынести Михаила.')
                elif 'door_open' in f:
                    self.say('Проход открыт.')
                elif 'stopper' in f:
                    self.start_dialogue('relay_fixed')
                else:
                    self.start_dialogue('relay_choice')
            elif key == 'boot':
                self.start_dialogue('boot')
            elif key == 'bell':
                self.flags.add('rang_bell')
                self.say('Звонок отвлекает Путевого. Пройдите через другой коридор.')
                return 'bell'
        elif scene == 'workshop':
            if key == 'exit':
                self.enter('waiting', (1490, 760))
            elif key == 'stopper':
                if 'stopper' not in f:
                    self.start_dialogue('stopper')
                else:
                    self.say('Стопор уже у вас. Вернитесь к щиту.')
            elif key == 'note':
                self.start_dialogue('note')
        elif scene == 'ward':
            if key == 'exit':
                self.enter('waiting', (1390, 510))
            elif key == 'patient':
                if not self.carrying and 'rescued' not in f:
                    self.start_dialogue('patient')
            elif key == 'nina':
                self.start_dialogue('nina_ward')
            elif key == 'cabinet':
                self.start_dialogue('cabinet')
        elif scene == 'carriage':
            if key in ('nina', 'lida', 'patient'):
                self.start_dialogue(key + '_after')
            elif key == 'map':
                if 'chapter_complete' in f:
                    self.start_dialogue('c2_departure')
                elif 'nina_after' in f:
                    self.start_dialogue('map')
                else:
                    self.say('Нина хочет поговорить, прежде чем вы продолжите путь.')
            elif key == 'cabin':
                self.say('Сначала проверьте схему в конце вагона.')
        return None

    def snapshot(self):
        return {'schema': SCHEMA, 'scene': self.scene, 'pos': list(self.pos),
                'flags': sorted(self.flags), 'choices': dict(self.choices),
                'health': self.health, 'flares': self.flares,
                'elapsed': self.elapsed, 'carrying': self.carrying,
                'carry_rear':list(self.carry_rear) if self.carrying and self.carry_rear is not None else None,
                'chapter':self.chapter, 'power':list(self.power), 'winch':dict(self.winch),
                'radio':list(self.radio),'signal_pattern':self.signal_pattern,'line_power':self.line_power,
                'brake':dict(self.brake)}

    @classmethod
    def restore(cls, data):
        migrated=False
        old_schema=data.get('schema') if isinstance(data,dict) else None
        legacy_brake=isinstance(data,dict) and data.get('schema') in (2,3,4,5,6,7)
        if isinstance(data,dict) and data.get('schema')==2:
            migrated=True
            data=copy.deepcopy(data)
            data.update(schema=SCHEMA,chapter=1,power=list(PowerBoard.initial),winch=Winch.initial(),
                        radio=[0,0,0],signal_pattern=0,line_power=True)
        elif isinstance(data,dict) and data.get('schema')==3:
            data=copy.deepcopy(data)
            data.update(schema=SCHEMA,radio=[0,0,0],signal_pattern=0,line_power=True)
        elif isinstance(data,dict) and data.get('schema')==4:
            data=copy.deepcopy(data);data['schema']=SCHEMA
            if data.get('scene') in ('dispatch','last_platform','upper_platform','crossing'):
                migrated=True
        elif isinstance(data,dict) and data.get('schema')==5:
            data=copy.deepcopy(data);data['schema']=SCHEMA
            if data.get('scene') in ('last_platform','upper_platform','crossing'):migrated=True
        elif isinstance(data,dict) and data.get('schema')==6:
            data=copy.deepcopy(data);data['schema']=SCHEMA
            if data.get('scene')=='crossing':migrated=True
        elif isinstance(data,dict) and data.get('schema')==7:
            data=copy.deepcopy(data);data['schema']=SCHEMA
        elif isinstance(data,dict) and data.get('schema')==8:
            data=copy.deepcopy(data);data['schema']=SCHEMA
        elif isinstance(data,dict) and data.get('schema')==9:
            data=copy.deepcopy(data);data['schema']=SCHEMA
        elif isinstance(data,dict) and data.get('schema')==10:
            data=copy.deepcopy(data);data['schema']=SCHEMA
        elif isinstance(data,dict) and data.get('schema')==11:
            data=copy.deepcopy(data);data['schema']=SCHEMA
        elif isinstance(data,dict) and data.get('schema')==12:
            data=copy.deepcopy(data);data['schema']=SCHEMA
        elif isinstance(data,dict) and data.get('schema')==13:
            data=copy.deepcopy(data);data['schema']=SCHEMA
        if old_schema in range(2,14) and data.get('scene') in ('power','yard','shed'):migrated=True
        if old_schema in range(2,13) and isinstance(data.get('flags'),list) and 'c2_boarded' in data['flags']:
            data['flags']=data['flags']+[flag for flag in ('c2_receiving_ready','c2_pack_ready') if flag not in data['flags']]
        if old_schema in range(2,12) and data.get('scene') in ('archive','workshop','signal_post'):migrated=True
        if old_schema in range(2,11) and data.get('scene') in ('flat','ward'):migrated=True
        if old_schema in (2,3,4,5,6,7,8,9) and data.get('scene')=='carriage':migrated=True
        if old_schema in (2,3,4,5,6,7,8) and data.get('scene')=='refuge':migrated=True
        if legacy_brake and isinstance(data.get('flags'),list) and all(isinstance(f,str) for f in data['flags']):
            completed=bool(set(data['flags'])&{'drive','arrive','chapter_complete','c1_brake_ready'})
            data['brake']=BrakeTest.initial(completed)
            if completed:data['flags']=list(set(data['flags'])|{'c1_brake_ready'})
        if not isinstance(data, dict) or data.get('schema') != SCHEMA:
            raise ValueError('Неподдерживаемая версия сохранения')
        scene = data.get('scene')
        pos = data.get('pos')
        flags = data.get('flags')
        choices = data.get('choices')
        if scene not in SCENES or not isinstance(pos, list) or len(pos) != 2:
            raise ValueError('Повреждены координаты')
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in pos):
            raise ValueError('Повреждены координаты')
        width, height = SCENES[scene].size
        if not (20 <= pos[0] <= width-20 and 20 <= pos[1] <= height-20):
            raise ValueError('Координаты вне станции')
        if not walkable(SCENES[scene],pos):
            # v0.2 maps used different coordinates; preserve progress on migration.
            if migrated:
                pos=list(SCENES[scene].start);data['pos']=pos
            else:raise ValueError('Координаты вне прохода')
        from .combat import FLAGS as COMBAT_FLAGS
        allowed = set(JOURNAL) | {v.get('effect') for v in DIALOGUES.values()} | {'door_open', 'rang_bell'} | chapters.FLAGS | COMBAT_FLAGS
        if not isinstance(flags, list) or any(not isinstance(x,str) or x not in allowed for x in flags):
            raise ValueError('Повреждены события')
        allowed_choices={'lida':('admit','order','hand'),**chapters.CHOICES}
        if not isinstance(choices, dict) or any(k not in allowed_choices or v not in allowed_choices[k] for k,v in choices.items()):
            raise ValueError('Повреждены решения')
        for field, lo, hi in [('health',1,100),('flares',0,3),('elapsed',0,1e8)]:
            value = data.get(field)
            if type(value) not in (int,float) or not math.isfinite(value) or not lo <= value <= hi:
                raise ValueError('Повреждено поле ' + field)
        if type(data.get('carrying')) is not bool:
            raise ValueError('Повреждено состояние носилок')
        if type(data['flares']) is not int:
            raise ValueError('Повреждено число ракет')
        if not BrakeTest.validate(data.get('brake')):
            raise ValueError('Повреждено состояние тормозной проверки')
        if ('c1_brake_ready' in flags)!=(data['brake']['stage']=='done'):
            raise ValueError('Тормозная проверка не соответствует результату')
        if 'drive' in flags and 'c1_brake_ready' not in flags:
            raise ValueError('Состав отправлен без проверки тормозов')
        if 'c1_parked' in flags and 'c1_stop' not in flags:
            raise ValueError('Состав ещё не остановлен на станции')
        if any(f.startswith('c1_inspected_') for f in flags) and 'c1_parked' not in flags:
            raise ValueError('Осмотр начат до закрепления состава')
        if data['carrying'] and ('carry' not in flags or 'rescued' in flags):
            raise ValueError('Неверное состояние носилок')
        if 'action_return_live' in flags and not {'action_mode','carry','door_open'}<=set(flags):
            raise ValueError('Обратная вылазка ещё не началась')
        if data['carrying'] and scene not in ('ward','waiting','platform'):
            raise ValueError('Носилки вне маршрута')
        carry_rear=data.get('carry_rear')
        if carry_rear is not None:
            from .carrying import CARRIER_SPACING,team_walkable
            valid=(data['carrying'] and isinstance(carry_rear,list) and len(carry_rear)==2 and
                   all(type(n) in (int,float) and math.isfinite(n) for n in carry_rear))
            if not valid:raise ValueError('Повреждено положение носильщиков')
            distance=math.dist(pos,carry_rear)
            if abs(distance-CARRIER_SPACING*SCENES[scene].actor_scale)>1 or not team_walkable(SCENES[scene],pos,carry_rear):
                raise ValueError('Носилки не помещаются в проходе')
        if 'lida_boarded' in flags and 'rescued' not in flags:
            raise ValueError('Нарушен порядок событий')
        if 'chapter_complete' in flags and ('nina_after' not in flags or 'lida_boarded' not in flags):
            raise ValueError('Незавершённая глава')
        if type(data.get('chapter')) is not int or data['chapter'] not in chapters.INFO:
            raise ValueError('Повреждён номер главы')
        if data['chapter']>=2 and 'chapter_complete' not in flags:
            raise ValueError('Предыдущая глава не завершена')
        if scene in ('hospital','refuge','power','yard','shed') and data['chapter']!=2:
            raise ValueError('Сцена не соответствует главе')
        if not PowerBoard.validate(data.get('power')) or not Winch.validate(data.get('winch')):
            raise ValueError('Повреждено состояние оборудования')
        if 'c2_power_ready' in flags and not PowerBoard.result(data['power'],'c2_cable' in flags)[0]:
            raise ValueError('Питание не соответствует схеме')
        if 'c2_complete' in flags and not {'c2_truth','c2_boarded','c2_gate_open'}<=set(flags):
            raise ValueError('Вторая глава не завершена')
        if {'c2_receiving_ready','c2_pack_ready'}&set(flags) and (data['chapter']<2 or 'c2_refuge' not in flags):
            raise ValueError('Подготовка эвакуации ещё не согласована с Лидой')
        if 'c2_boarded' in flags and not {'c2_receiving_ready','c2_pack_ready','c2_gate_open'}<=set(flags):
            raise ValueError('Пассажиров ещё не готовы принять')
        if data['chapter']>=3 and 'c2_complete' not in flags:
            raise ValueError('Предыдущая глава не завершена')
        if scene in ('settlement','relay_house','flat','switchyard','gantry') and data['chapter']!=3:
            raise ValueError('Сцена не соответствует главе')
        if not RadioTune.validate(data.get('radio')) or type(data.get('line_power')) is not bool:
            raise ValueError('Повреждено состояние связи')
        if type(data.get('signal_pattern')) is not int or data['signal_pattern'] not in (0,2,3):
            raise ValueError('Повреждён проверочный сигнал')
        if 'c3_contact' in flags and ('c3_repair' not in flags or data['signal_pattern']==0 or not RadioTune.locked(data['radio'])):
            raise ValueError('Связь не была восстановлена')
        if 'c3_boarded' in flags and not {'c3_met','c3_contact','c3_original'}<=set(flags):
            raise ValueError('Павел не готов к отправлению')
        if 'c3_complete' in flags and not {'c3_boarded','c3_tape_decided','c3_nina_after'}<=set(flags):
            raise ValueError('Третья глава не завершена')
        if 'c3_letters_discussed' in flags and not {'c3_letter_early','c3_letter_middle','c3_letter_late'}<=set(flags):
            raise ValueError('Черновики Павла ещё не прочитаны')
        if ('pavel_statement' in choices)!=('c3_letters_discussed' in flags):
            raise ValueError('Решение о письме Павла не подтверждено')
        for flag,value in (('c3_statement_taken','take'),('c3_statement_left','leave')):
            if flag in flags and choices.get('pavel_statement')!=value:
                raise ValueError('Письмо Павла не соответствует решению')
            if choices.get('pavel_statement')==value and flag not in flags:
                raise ValueError('Передача письма Павла ещё не завершена')
        if data['chapter']>=4 and 'c3_complete' not in flags:
            raise ValueError('Третья глава не завершена')
        if scene in ('spillway','gallery','archive','dispatch') and data['chapter']!=4:
            raise ValueError('Сцена не соответствует главе')
        from .chapters.chapter4_expansion import ACCOUNT_FLAGS
        if set(ACCOUNT_FLAGS)&set(flags) and (data['chapter']<4 or 'c4_met' not in flags):
            raise ValueError('Разговор с Валентиной ещё не состоялся')
        if 'c4_addendum' in flags and not set(ACCOUNT_FLAGS)<=set(flags):
            raise ValueError('Содержание примечания Валентины ещё не обсуждено')
        if 'c4_contact_verified' in flags and not {'c4_chart','c4_level_checked','c4_main_closed','c4_service_open'}<=set(flags):
            raise ValueError('Обход не подтверждён')
        if 'c4_handover' in flags and ('c4_contact_verified' not in flags or 'statement' not in choices):
            raise ValueError('Передача управления не подготовлена')
        if 'c4_complete' in flags and 'c4_handover' not in flags:
            raise ValueError('Четвёртая глава не завершена')
        if data['chapter']>=5 and 'c4_complete' not in flags:
            raise ValueError('Четвёртая глава не завершена')
        if scene in ('last_platform','signal_post','crossing','upper_platform') and data['chapter']!=5:
            raise ValueError('Сцена не соответствует главе')
        if 'c5_crossed' in flags and not chapters.chapter5.REQUIRED<=set(flags):
            raise ValueError('Переход пассажиров не подготовлен')
        if 'c5_pin_out' in flags and 'c5_gate_supported' not in flags:
            raise ValueError('Штырь не освобождён от нагрузки')
        if 'c5_gate_swung' in flags and 'c5_pin_out' not in flags:
            raise ValueError('Створка заперта')
        if 'c5_complete' in flags:
            ending=choices.get('ending')
            if ending not in ('testimony','unfinished','return'):
                raise ValueError('Отсутствует итог рейса')
            if ending!='return' and 'c5_crossed' not in flags:
                raise ValueError('Рейс не завершён')
            if ending=='return' and 'c5_arrived' in flags:
                raise ValueError('Возвращение не соответствует маршруту')
            if ending=='testimony' and (choices.get('tape_audience')!='all' or choices.get('statement')!='signed'):
                raise ValueError('Итог не соответствует свидетельствам')
        s = cls()
        for key in ('scene','pos','choices','health','flares','elapsed','carrying','chapter','power','winch','radio','signal_pattern','line_power','brake'):
            setattr(s, key, copy.deepcopy(data[key]))
        s.flags = set(flags)
        s.carry_rear=copy.deepcopy(carry_rear)
        return s

    def save(self, path=DEFAULT_SAVE):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.snapshot()
        # Checkpoints never serialize a half-finished conversation.
        self.restore(payload)
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(path)

    @classmethod
    def load(cls, path=DEFAULT_SAVE):
        return cls.restore(json.loads(Path(path).read_text(encoding='utf-8')))
