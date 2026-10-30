"""Chapter four: physical inspection before trusting the control panel."""
CHOICES={'tape_audience':('all','archive'),'statement':('signed','deferred')}
ART={'dispatch':'environments/dispatch-v01.png','archive':'environments/archive-v01.png'}
FLAGS={'c4_main_closed','c4_service_open','c4_contact_verified'}

def install(scenes,dialogues,journal,Scene,Object):
    def room(key,title,objects):
        scenes[key]=Scene(title,(1500,1000),(220,790),
            ((80,80,1340,30),(80,80,30,840),(1390,80,30,840),(80,900,1340,30),
             (450,220,400,120)),tuple(Object(*o) for o in objects),
            ((740,420,260,(225,178,112)),))
    room('spillway','Водосброс • служебная платформа',[
        ('train','В вагон',(180,800),'train'),('gallery','Верхняя галерея',(1200,720),'door'),
        ('dispatch','Диспетчерская',(1180,400),'door'),('nina','Нина',(780,580),'nina')])
    room('gallery','Верхняя галерея • контроль опор',[
        ('exit','К поезду',(180,800),'door'),('archive','Нижний архив',(1150,740),'door'),
        ('gauge','Водомерная рейка',(1130,430),'relay'),
        ('confirm','Обратный контакт',(750,550),'relay')])
    scenes['archive']=Scene('Нижний архив • сухая полка',(1536,1024),(350,740),(),(
        Object('exit','На галерею',(200,720),'door'),Object('chart','Схема обхода',(440,550),'paper'),
        Object('orders','Журнал приказов',(900,510),'paper'),Object('inspection','Осмотр опор',(1100,560),'paper'),
        Object('application','Заявление о дубликате',(1270,690),'paper')),
        (),((250,550),(500,480),(540,400),(760,410),(790,480),(1090,480),
            (1200,550),(1280,580),(1330,790),(1390,900),(1390,980),(180,980),
            (140,760),(200,650)),actor_scale=1.7)
    scenes['dispatch']=Scene('Диспетчерская • ручной пост',(1536,1024),(260,570),(),(
        Object('exit','На платформу',(205,650),'door'),Object('handle','Фиксатор рукоятки',(430,430),'tool'),
        Object('valentina','Валентина',(920,510),'valentina'),Object('recorder','Магнитофон',(1190,580),'radio'),
        Object('main','Главный путь',(600,430),'relay'),Object('service','Служебный путь',(770,430),'relay'),
        Object('statement','Общий протокол',(1100,430),'paper'),Object('handover','Передача управления',(420,600),'paper')),
        (),((175,390),(1180,365),(1180,540),(1380,610),(1410,740),(1495,770),(1495,1000),(100,1000),(110,660),(175,650)),actor_scale=1.7)
    def d(key,lines,effect=None,choices=None):
        data={'lines':lines}
        if effect:data['effect']=effect
        if choices:data['choices']=choices
        dialogues[key]=data
    d('c4_departure',[('Нина','У водосброса сначала проверим опоры. Показания пульта про воду ничего не скажут.'),
        ('Павел','Служебный настил выше. Если замки целы, пройдём там.')],'c4_travel')
    d('c4_arrival',[('Лида','Мне нужен ровный путь. Если впереди лестницы, сначала скажите, потом несите.'),
        ('Нина','Поезд останется здесь, пока я не проверю опору.'),('Артём','На пульте участок свободен.'),
        ('Нина','Пульт знает про поезд. Про воду он не знает.'),
        ('Валентина · рация','Заходите через служебный тамбур. Я не могу отойти от рукоятки.')],'c4_arrived')
    d('c4_handle',[('','Артём вставляет штатный фиксатор. Валентина медленно разжимает пальцы.'),
        ('Валентина','Спасибо. Пружину давно надо было менять.')],'c4_fixed_handle')
    d('c4_meeting',[('Валентина','Воронцов. Я думала, ты не поедешь.'),('Артём','Я тоже.'),
        ('Валентина','Запись у тебя?'),('Артём','Оригинал. И Павел в вагоне.'),
        ('Валентина','Я приказала не останавливаться. В журнале стоит моя фамилия.'),
        ('Артём','А людей видел я.'),('Валентина','Я не стану говорить, что ты ничего не мог сделать. Я не знаю, что получилось бы. Знаю, что приказ отдала я.'),
        ('Нина','Сначала схема пути. Потом не расходиться: этот разговор нужно закончить.')],'c4_met')
    d('c4_chart',[('','На схеме главный путь пересекает низкую насыпь. Служебный идёт по отдельному настилу.'),
        ('Нина · рация','Закрыть главный. Открыть служебный. Затем подтвердить контакт с галереи. Одного положения рукояток мало.')],'c4_chart')
    d('c4_orders',[('','«Служебную проходить без остановки». Под распоряжением фамилия Валентины. Ниже следующая смена: «Поиск прекращён до спада воды».'),
        ('Артём','А мы к тому времени уже были наверху.')],'c4_orders')
    d('c4_inspection',[('','Последний осмотр: опора главного пути требует проверки после каждого подъёма воды. Служебный настил имеет отдельный фундамент.'),
        ('Нина · рация','Теперь сравним это с рейкой. Не с зелёной лампой.')],'c4_inspection')
    d('c4_application',[('','Просьба выдать дубликат трудовой книжки. Адрес временный, телефон соседей. Через месяц приписано: «Получено лично».'),
        ('Артём','Они ещё месяц за этими бумагами ходили.')],'c4_application')
    d('c4_gauge',[('Нина · рация','Вода выше основания главной опоры. Край служебного настила сухой, опора цела.'),
        ('Павел · рация','Показание не то?'),('Нина · рация','Показание верное. Мы не тот вопрос ему задали.')],'c4_level_checked')
    d('c4_play_shared',[('Валентина','Весь вагон уже слышал?'),('Артём','Да. Теперь послушайте вы.'),
        ('','Лента идёт до конца. Валентина сверяет время со своим журналом.'),
        ('Валентина','Мой приказ. И моё подтверждение. Запишите оба, без сокращений.')],'c4_tape_heard')
    d('c4_play_held',[('Артём','Я обещал сначала дать вам послушать.'),('Нина','Сначала — уже сейчас. Дальше мы тоже должны услышать.'),
        ('','Валентина слушает оба канала. На звуке ворот она кладёт ладонь на журнал.'),
        ('Валентина','Не останавливайте. До конца.')],'c4_tape_heard')
    d('c4_audience',[('Нина','Теперь запись останется только в архиве или мы включаем её всем?')],choices=[
        ('Прослушать вместе с пассажирами.','c4_all'),('Передать оригинал с документами, без общего прослушивания.','c4_archive')])
    d('c4_all',[('','В вагоне освобождают стол. Павел просит не перематывать второй канал.'),
        ('Лида','Мальчика на ленте помню. Потом приезжал ко мне уже со своей дочкой.'),
        ('Нина','Теперь у каждого есть возможность рассказать самому.')],'c4_all')
    d('c4_archive',[('Нина','Я поеду и помогу. Только больше не называй это нашим решением.'),
        ('Валентина','Оригинал с журналом передадим наверху. Коробку опечатаем при Павле.')],'c4_archive')
    d('c4_protocol',[('Валентина','Подпишите только то, что видели сами. За других я больше писать не буду.')],choices=[
        ('Подписать свою часть хронологии.','c4_signed'),('Передать документы. Заявление написать позже.','c4_deferred')])
    d('c4_signed',[('Артём','Видел людей. Запросил подтверждение. Прошёл без остановки.'),
        ('','Он ставит подпись под своей частью. Валентина подписывает распоряжение, Павел — время ухода от ворот.')],'c4_signed')
    d('c4_deferred',[('Артём','Я не готов написать всё сейчас.'),('Валентина','Тогда не подписывайте чужой пересказ. Журнал и кассету всё равно передадим.')],'c4_deferred')
    d('c4_handover',[('Артём','На старой платформе кому-то придётся выйти. Я останусь за пультом.'),
        ('Нина','Ты опять собираешься видеть всё через стекло?'),('Валентина','Я доведу на малом. Покажи тормоз.'),
        ('','Артём показывает ограничитель и аварийную остановку. Валентина повторяет порядок и проверяет рукоятку.'),
        ('Валентина','До сигнала стоим. После сигнала — малый ход. Если связь пропала, тормозим. Ты идёшь к платформенному замку.')],'c4_handover')
    d('c4_finish',[('Нина','Обход проверен. Главный путь закрыт, служебный подтверждён с галереи.'),
        ('Лида','Перед отправлением предупредите. Михаил сам сядет, ему только руку подать.'),
        ('','Артём оставляет ключ от кабины на столе рядом с Валентиной.')],'c4_complete')
    for flag,title,text in (
        ('c4_chart','Служебный обход','Закрыть главный путь, открыть служебный, подтвердить контакт с галереи.'),
        ('c4_level_checked','Выше воды','Главная опора подмыта; отдельный служебный настил цел.'),
        ('c4_orders','Личный приказ','В журнале распоряжение Валентины. Артём видел людей и принял решение по составу.'),
        ('c4_tape_heard','Без сокращений','Валентина прослушала оба канала оригинала.'),
        ('c4_contact_verified','Подтверждение','Рукоятки сверены с физическим обратным контактом на галерее.'),
        ('c4_handover','Выйти из кабины','Валентина проверила тормоз и порядок действий. Артём пойдёт к платформенному замку.')):
        journal[flag]=(title,text)
    from .chapter4_expansion import install as expand
    expand(dialogues,journal)

def apply(s,effect):
    if not effect.startswith('c4_'):return False
    if effect=='c4_travel':s.chapter=4
    elif effect=='c4_arrived':s.enter('spillway');s.health=100;s.flares=3
    elif effect in ('c4_all','c4_archive'):s.choices['tape_audience']='all' if effect=='c4_all' else 'archive'
    elif effect in ('c4_signed','c4_deferred'):s.choices['statement']='signed' if effect=='c4_signed' else 'deferred'
    elif effect in ('c4_account_known','c4_account_search','c4_account_after'):
        from .chapter4_expansion import ACCOUNT_FLAGS
        if set(ACCOUNT_FLAGS)<=s.flags:
            s.say('Валентина готовит отдельное примечание. Поговорите с ней ещё раз, чтобы приложить его к журналу.')
    return True

def objective(s):
    if s.chapter!=4:return None
    for flag,text in (('c4_fixed_handle','Освободить руку Валентины штатным фиксатором'),
        ('c4_met','Поговорить с Валентиной'),('c4_chart','Найти схему обхода в нижнем архиве'),
        ('c4_inspection','Сверить журнал осмотра опор'),('c4_level_checked','Проверить водомерную рейку на галерее'),
        ('c4_contact_verified','Закрыть главный путь, открыть служебный и проверить обратный контакт'),
        ('c4_tape_heard','Включить оригинал записи при Валентине')):
        if flag not in s.flags:return text
    if 'tape_audience' not in s.choices:return 'Решить, кто услышит запись'
    if 'statement' not in s.choices:return 'Обсудить общий протокол'
    if 'c4_handover' not in s.flags:return 'Передать Валентине управление поездом'
    return 'Вернуться к схеме в вагоне'

def interact(s,key):
    if s.chapter==3 and 'c3_complete' in s.flags and key in ('map','cabin'):
        s.start_dialogue('c4_departure');return True
    if s.chapter!=4:return None
    f=s.flags
    def talk(name):s.start_dialogue(name);return True
    def enter(scene):s.enter(scene);return True
    if s.scene=='carriage':
        if 'c4_arrived' not in f:return talk('c4_departure')
        if key=='cabin':return enter('spillway')
        if key=='map':
            if 'c4_handover' in f:return talk('c4_finish')
            s.say(s.objective());return True
        s.say('Команда ждёт проверки обхода. '+s.objective());return True
    if s.scene=='spillway':
        if key=='train':return enter('carriage')
        if key in ('gallery','dispatch'):return enter(key)
        s.say(s.objective());return True
    if s.scene=='gallery':
        if key=='exit':return enter('spillway')
        if key=='archive':return enter('archive')
        if key=='gauge':
            if 'c4_inspection' in f:return talk('c4_gauge')
            s.say('Сначала найдите журнал осмотра: нужно знать, с какой отметкой сравнивать воду.');return True
        if key=='confirm':
            if {'c4_main_closed','c4_service_open','c4_chart','c4_level_checked'}<=f:
                f.add('c4_contact_verified');s.say('Контакт подтверждает служебный путь. Главный закрыт.')
            else:s.say('Обратный контакт не подтверждён. Проверьте схему, опоры и обе рукоятки.')
            return True
    if s.scene=='archive':
        if key=='exit':return enter('gallery')
        return talk('c4_'+key)
    if s.scene=='dispatch':
        if key=='exit':return enter('spillway')
        if key=='handle':return talk('c4_handle')
        if 'c4_fixed_handle' not in f:s.say('Валентина держит подпружиненную рукоятку. Рядом штатный фиксатор.');return True
        if key=='valentina':
            from .chapter4_expansion import ACCOUNT_FLAGS
            if 'c4_met' not in f:return talk('c4_meeting')
            if 'c4_addendum' in f:return talk('c4_account_done')
            if set(ACCOUNT_FLAGS)<=f:return talk('c4_addendum')
            return talk('c4_questions')
        if 'c4_met' not in f:s.say('Сначала поговорите с Валентиной.');return True
        if key in ('main','service'):
            if 'c4_handover' in f:s.say('Управление передано. Проверенный маршрут зафиксирован.');return True
            if not {'c4_chart','c4_level_checked'}<=f:s.say('Сначала схема и осмотр опоры.');return True
            flag='c4_main_closed' if key=='main' else 'c4_service_open'
            if flag in f:f.remove(flag)
            else:f.add(flag)
            f.discard('c4_contact_verified')
            s.say(('Главный закрыт' if 'c4_main_closed' in f else 'Главный открыт')+'; '+('служебный открыт.' if 'c4_service_open' in f else 'служебный закрыт.'))
            return True
        if key=='recorder':
            if 'tape_audience' in s.choices:s.say('Решение о записи принято. Оригинал сохранён для передачи наверху.');return True
            if 'c4_tape_heard' not in f:return talk('c4_play_shared' if s.choices.get('recording_policy')=='share' else 'c4_play_held')
            if s.choices.get('recording_policy')=='share':return talk('c4_all')
            return talk('c4_audience')
        if key=='statement':
            if 'tape_audience' not in s.choices:s.say('Сначала закончите разговор о записи.');return True
            return talk('c4_protocol')
        if key=='handover':
            if 'c4_contact_verified' in f and 'statement' in s.choices:return talk('c4_handover')
            s.say(s.objective());return True
    return True
