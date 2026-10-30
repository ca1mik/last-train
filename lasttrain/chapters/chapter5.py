"""The final stop: visible crew confirmations rather than a timed moral test."""
CHOICES={'ending':('testimony','unfinished','return')}
ART={'last_platform':'environments/last-platform-v01.png','upper_platform':'environments/upper-platform-v01.png',
     'crossing':'environments/crossing-v01.png','signal_post':'environments/signal-post-v01.png'}
FLAGS={'c5_gate_supported','c5_pin_out','c5_gate_swung'}
REQUIRED={'c5_brake','c5_nina_ready','c5_pavel_ready','c5_lida_ready','c5_coupler','c5_gate','c5_semaphore','c5_crossed'}

def install(scenes,dialogues,journal,Scene,Object):
    def room(key,title,objects,walls=()):
        scenes[key]=Scene(title,(1600,1050),(220,830),
            ((80,80,1440,30),(80,80,30,880),(1490,80,30,880),(80,940,1440,30))+walls,
            tuple(Object(*o) for o in objects),((800,450,260,(217,174,116)),))
    scenes['last_platform']=Scene('Служебная • остановка по требованию',(1536,1024),(340,790),(),(
        Object('train','В вагон',(260,790),'train'),Object('brake','Стояночный тормоз',(330,640),'relay'),
        Object('nina','Нина у настила',(1150,450),'nina'),Object('pavel','Павел у ворот',(950,400),'pavel'),
        Object('coupler','Разобщительный кран и сцепка',(390,520),'relay'),
        Object('gate','Платформенный замок',(1190,300),'relay'),Object('semaphore','Пост семафора',(1190,740),'door')),
        (),((570,170),(960,230),(1240,290),(1270,430),(1220,480),(1220,750),(1410,870),(1470,1000),(100,1000),(310,600)))
    scenes['signal_post']=Scene('Семафор • ручной привод',(1536,1024),(370,760),(),(
        Object('exit','На платформу',(235,780),'door'),Object('lever','Привод семафора',(1050,520),'relay'),
        Object('crossing','К настилу',(1330,750),'door'),Object('plate','Табличка проверки',(390,540),'paper')),
        (),((230,570),(320,500),(540,470),(600,420),(900,440),(950,500),
            (1170,500),(1230,560),(1350,630),(1370,760),(1330,820),(1340,980),
            (170,980),(180,760)),actor_scale=1.7)
    scenes['crossing']=Scene('Настил • люди выходят к верхней линии',(1536,1024),(220,480),(),(
        Object('exit','К семафору',(180,480),'door'),Object('nina','Нина',(850,450),'nina'),
        Object('walkway','Провести пассажиров',(1250,480),'door')),(),((60,390),(1460,390),(1460,520),(60,520)))
    scenes['upper_platform']=Scene('Верхняя линия • рассвет',(1536,1024),(620,560),(),(
        Object('nina','Нина',(800,420),'nina'),Object('lida','Лида',(1000,640),'lida'),
        Object('pavel','Павел',(560,500),'pavel'),Object('documents','Передача документов',(1280,420),'paper'),
        Object('raisa','Раиса',(1140,780),'raisa','c2_boarded')),
        (),((470,330),(980,330),(1100,360),(1500,360),(1500,1000),(140,1000),(300,620)))
    def d(key,lines,effect=None,choices=None):
        data={'lines':lines}
        if effect:data['effect']=effect
        if choices:data['choices']=choices
        dialogues[key]=data
    d('c5_departure',[('Валентина','Служебный обход готов. Можно идти к верхней линии. Или вернуться по проверенному пути с теми, кто уже в вагоне.'),
        ('Нина','Возвращение не решит вопрос с платформой. Но людей мы довезём в обоих случаях.'),
        ('','Это выбор маршрута. При возвращении будет отдельная короткая развязка; до решения сохраняется контрольная точка.')],choices=[
        ('Продолжить к старой платформе.','c5_go'),('Вернуться с пассажирами по проверенному пути.','c5_return')])
    d('c5_go',[('Артём','На платформе выхожу я. До моего подтверждения поезд стоит.'),
        ('Валентина','До подтверждения стоим. При потере связи тоже.')],'c5_travel')
    d('c5_return',[('','Утром Лида передаёт Михаила дежурной бригаде. Павел помогает вынести коробки. Никого не оставляют у воды.'),
        ('Нина','Кассету и журнал я заберу. Работу на линии придётся продолжить с другой бригадой.'),
        ('Артём','Позвони, когда доедешь.'),('Нина','Я передам документы. Про остальное поговорим позже.'),
        ('','Дома приёмник молчит. Артём всё равно вынимает вилку. На столе остаётся место, куда он хотел положить коробку с записью.')],'c5_complete')
    d('c5_arrival',[('','На старой платформе не объявляют посадку. В свете фонаря виден ряд мокрых скамеек.'),
        ('Валентина · рация','Полная остановка. Теперь стояночный тормоз.'),('Артём','Я выхожу.'),
        ('Нина','Я проверю настил. Павел — замок. Лиду спроси до того, как откроем выход.')],'c5_arrived')
    d('c5_brake',[('','Артём затягивает стояночный тормоз и проверяет неподвижное колесо.'),
        ('Валентина · рация','Тяга снята. Пневматика держит. Сцепку можно разобщать после перекрытия крана.')],'c5_brake')
    d('c5_nina',[('Нина','Доски целы, ограждение держится. Носилки проходят. Я пойду первой, Лида за мной.'),
        ('Артём','Я подстрахую сзади.'),('Нина','Хорошо. Не подгоняй тех, кто идёт медленнее.')],'c5_nina_ready')
    d('c5_pavel',[('Павел','Замок закис. Я разгружу петлю, ты вытащишь штырь.'),
        ('Артём','Удержишь?'),('Павел','Да. Если не удержу — скажу. Никуда не ухожу.')],'c5_pavel_ready')
    d('c5_lida',[('Лида','Михаил готов. Носилки проверила, одеяло закреплено. Мне нужна вторая пара рук.'),
        ('Михаил','Только считайте вслух, когда поднимаете.'),('Артём','До трёх. И остановимся, если попросите.')],'c5_lida_ready')
    d('c5_coupler',[('','Сначала кран. Затем проверка давления. Только после этого Артём снимает сцепной фиксатор.'),
        ('Валентина · рация','Хвостовая секция остаётся на тормозе. Рабочий вагон свободен.')],'c5_coupler')
    d('c5_gate',[('Павел','Держу. Теперь штырь.'),('','Замок выходит из петли. Павел медленно опускает створку на упор.'),
        ('Павел','Проход свободен. Я останусь, пока последний не пройдёт.')],'c5_gate')
    d('c5_plate',[('','«Проверять открытое положение по тяге и полотну. До подтверждения обхода сигнал не открывать».'),
        ('Артём','Сначала люди и настил. Потом зелёный.')],'c5_plate')
    d('c5_semaphore',[('','Рукоятка идёт туго. Артём доводит её до защёлки и проверяет поднятое полотно через окно поста.'),
        ('Валентина · рация','Сигнал вижу. Состав стоит, пока вы не закончите переход.'),
        ('Артём','Подтверждаю. Ждите людей.')],'c5_semaphore')
    d('c5_crossing_start',[('Артём','Раз. Два. Три.'),('','Михаила укладывают на носилки. Лида берётся за передние рукоятки, Артём — за задние.'),
        ('','Раиса и остальные соседи уже перешли с Ниной на другой берег. Нина вернулась к носилкам.'),
        ('Нина','Я проверю проход впереди. Павел, выходи последним.')],'c5_crossing_start')
    d('c5_crossed',[('Павел','Последний прошёл. Я здесь.'),
        ('','Из громкоговорителя слышен щелчок, но объявления нет.'),
        ('Валентина · рация','Вас вижу. Подам вагон к верхнему перрону. Дальше пешком не надо.')],'c5_crossed')
    d('c5_lida_upper',[('Лида','Дежурные идут с креслом. Адрес мастерской Михаила им передали. Теперь я могу сесть.'),('Артём','Чай принести?'),
        ('Лида','Принесите. И себе тоже.')],'c5_lida_upper')
    d('c5_pavel_upper',[('Павел','Ключи от квартиры у меня. Хорошо, что взял.'),('Артём','Вернёшься?'),
        ('Павел','Когда скажут, что можно. Сначала высплюсь.')],'c5_pavel_upper')
    d('c5_testimony',[('','Нина передаёт кассету, журнал и подписанную хронологию. Дежурная записывает фамилии свидетелей и выдаёт номер обращения.'),
        ('Валентина','Мою часть не переписывайте от имени машиниста.'),('Нина','Здесь каждый подписал свою.'),
        ('','На перроне Нина ставит рядом с отцом бумажный стакан чая.'),('Нина','Я позвоню, когда доеду.'),
        ('Артём','Хорошо.'),('','Он не спрашивает, простила ли она его. На платформе больше не звучит объявление.')],'c5_complete')
    d('c5_unfinished',[('','Нина передаёт оригинал и журнал. Дежурная принимает документы и записывает, каких пояснений пока нет.'),
        ('Нина','Обращение приняли. Дальше придётся приходить и отвечать на вопросы.'),
        ('Артём','Я приду.'),('Нина','Запиши номер. Я не буду каждый раз напоминать.'),
        ('','Люди из вагона вышли к верхней линии. Между Артёмом и Ниной остаётся разговор, который нельзя закончить одним обещанием.')],'c5_complete')
    for flag,title,text in (
        ('c5_brake','Остановка','Состав закреплён. До подтверждения команды движение запрещено.'),
        ('c5_gate','Открытые ворота','Павел удержал створку и остался у прохода.'),
        ('c5_semaphore','Сигнал','Привод и полотно проверены. Валентина ждёт завершения перехода.'),
        ('c5_crossed','Последний прошёл','Все пассажиры прошли по проверенному настилу. Павел вышел последним.')):
        journal[flag]=(title,text)

def apply(s,effect):
    if not effect.startswith('c5_'):return False
    if effect=='c5_travel':s.chapter=5
    elif effect=='c5_arrived':s.enter('last_platform');s.health=100;s.flares=3
    elif effect=='c5_crossed':s.enter('upper_platform')
    elif effect=='c5_complete':
        s.chapter=5
        s.choices['ending']='return' if 'c5_arrived' not in s.flags else ('testimony' if s.choices.get('tape_audience')=='all' and s.choices.get('statement')=='signed' else 'unfinished')
    return True

def objective(s):
    if s.chapter!=5:return None
    if 'c5_complete' in s.flags:return 'Рейс окончен • документы переданы'
    for flag,text in (('c5_brake','Закрепить состав стояночным тормозом'),('c5_nina_ready','Проверить настил с Ниной'),
        ('c5_pavel_ready','Договориться с Павлом у ворот'),('c5_lida_ready','Спросить Лиду о готовности пассажиров в вагоне'),
        ('c5_coupler','Перекрыть кран и освободить сцепку'),('c5_gate','Вместе с Павлом открыть платформенный замок'),
        ('c5_semaphore','Открыть и проверить семафор'),('c5_crossed','Провести пассажиров по настилу')):
        if flag not in s.flags:return text
    return 'Передать документы на верхнем перроне'

def interact(s,key):
    if s.chapter==4 and 'c4_complete' in s.flags and key in ('map','cabin'):
        s.start_dialogue('c5_departure');return True
    if s.chapter!=5:return None
    f=s.flags
    def talk(name):s.start_dialogue(name);return True
    def enter(scene):s.enter(scene);return True
    if 'c5_complete' in f:s.say('Рейс окончен. Итог сохранён; можно начать новую игру из меню.');return True
    if s.scene=='carriage':
        if key=='lida':return talk('c5_lida')
        if key=='cabin':return enter('last_platform')
        s.say(s.objective());return True
    if s.scene=='last_platform':
        if key=='train':return enter('carriage')
        if key=='brake':return talk('c5_brake')
        if key=='nina':return talk('c5_nina')
        if key=='pavel':return talk('c5_pavel')
        if key=='semaphore':return enter('signal_post')
        if key=='coupler' and 'c5_brake' in f:return talk('c5_coupler')
        if key=='gate' and {'c5_brake','c5_pavel_ready','c5_coupler'}<=f:
            if 'c5_gate' in f:s.say('Створка на упоре. Павел держит проход свободным.');return True
            s.puzzle='gate';return 'gate'
        s.say(s.objective());return True
    if s.scene=='signal_post':
        if key=='exit':return enter('last_platform')
        if key=='plate':return talk('c5_plate')
        if key=='lever' and {'c5_gate','c5_nina_ready','c5_lida_ready'}<=f:return talk('c5_semaphore')
        if key=='crossing' and 'c5_semaphore' in f:return enter('crossing')
        s.say(s.objective());return True
    if s.scene=='crossing':
        if key=='exit':return enter('signal_post')
        if key=='walkway' and REQUIRED-{'c5_crossed'}<=f:return talk('c5_crossing_start')
        s.say('Нина держит начало настила. Лида ждёт вашей помощи на пороге.');return True
    if s.scene=='upper_platform':
        if key=='pavel' and 'pavel_statement' in s.choices:return talk('c5_pavel_statement')
        if key in ('lida','pavel'):return talk('c5_'+key+'_upper')
        if key in ('documents','nina'):
            name='c5_testimony' if s.choices.get('tape_audience')=='all' and s.choices.get('statement')=='signed' else 'c5_unfinished'
            if 'pavel_statement' in s.choices:name+='_pavel'
            if 'c4_addendum' in f:name+='_addendum'
            return talk(name)
    return True

def result(s):
    text={'testimony':'Все пассажиры на верхней линии. Запись и подписанная хронология переданы. Каждый отвечает за свою часть.',
        'unfinished':'Все пассажиры на верхней линии. Документы переданы; часть разговоров и свидетельств ещё предстоит закончить.',
        'return':'Пассажиры благополучно вернулись. Нина передала документы; работа на старой платформе осталась другой бригаде.'}.get(s.choices.get('ending'),'Рейс окончен.')
    if 'pavel_statement' in s.choices:
        text+=(' Подписанное письмо Павла сохранено для личной передачи.' if s.choices.get('ending')=='return' else
               ' Павел лично передал подписанное письмо вместе с записью.')
    if 'c4_addendum' in s.flags:text+=' Подписанное примечание Валентины передано вместе с журналом.'
    return text

def operate_gate(s,action):
    if s.chapter!=5 or s.scene!='last_platform' or s.puzzle!='gate':return False
    f=s.flags
    if not {'c5_brake','c5_pavel_ready','c5_coupler'}<=f:return False
    if action=='support':
        if 'c5_gate_supported' not in f:f.add('c5_gate_supported');s.say('Павел приподнял створку. Нагрузка со штыря снята.')
        else:s.say('Павел держит. Можно вынуть штырь.')
    elif action=='pin':
        if 'c5_gate_supported' not in f:s.say('Штырь закушен весом створки. Сначала попросите Павла разгрузить петлю.')
        elif 'c5_pin_out' not in f:f.add('c5_pin_out');s.say('Штырь вынут. Створку можно медленно открыть.')
    elif action=='swing':
        if 'c5_pin_out' not in f:s.say('Створка заперта. Сначала освободите штырь.')
        elif 'c5_gate_swung' not in f:f.add('c5_gate_swung');s.say('Створка открыта. Проверьте, что она легла на упор.')
    elif action=='confirm':
        if 'c5_gate_swung' not in f:s.say('Пока нельзя подтвердить свободный проход.')
        else:s.puzzle=None;s.start_dialogue('c5_gate');return True
    return False
