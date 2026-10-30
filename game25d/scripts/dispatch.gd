extends "res://scripts/journey_stop.gd"
## Playable chapter 6 blockout. Canon from legacy chapter4; appearances provisional.
const HANDLE := Vector3(8,0,-10)
const VALENTINA := Vector3(11,0,-10)
const ARCHIVE := Vector3(-12,0,-12)
const GAUGE := Vector3(19,0,3)
const MAIN := Vector3(6,0,-15)
const SERVICE := Vector3(11,0,-15)
const CONTACT := Vector3(13,0,13)
const RECORDER := Vector3(16,0,-10)
const ALL := Vector3(-17,0,12)
const PRIVATE := Vector3(16,0,-6)
const SIGN := Vector3(8,0,-6)
const DEFER := Vector3(11,0,-3)
const CACHE := Vector3(-16,0,1)
var main_indicator: Node3D
var service_indicator: Node3D

func configure() -> void:
	stop_id="dispatch";title_text="ДИСПЕТЧЕРСКАЯ · ВОДОСБРОС";next_chapter=7
	start_point=Vector3(-20,0,16);bounds=Rect2(-26,-23,52,46)
	intro_text="Нина: сначала опоры и вода. Зелёная лампа знает о поезде, не о воде. Валентина жива и ждёт у ручного поста."

func build_content() -> void:
	# Two routes around the water: archive gallery in the north, dry south apron.
	kit.path_strip(start_point,Vector3(-17,0,-16),3.8,Color("7f8475"))
	kit.path_strip(Vector3(-17,0,-16),Vector3(19,0,-16),3.5,Color("7f8475"))
	kit.path_strip(Vector3(19,0,-16),Vector3(19,0,17),3.7,Color("7f8475"))
	kit.path_strip(start_point,Vector3(19,0,17),3.5,Color("7f8475"))
	block(Vector3(1,.02,2),Vector3(20,.1,14),Color("273c47"))
	# Railings are real boundaries: there is no lethal hidden water timer.
	block(Vector3(-9.3,.55,2),Vector3(.4,1.1,14),Color("737f7e"),true)
	block(Vector3(11.3,.55,2),Vector3(.4,1.1,14),Color("737f7e"),true)
	block(Vector3(1,.55,-5.2),Vector3(20,1.1,.4),Color("737f7e"),true)
	block(Vector3(-4,.55,9.2),Vector3(10,1.1,.4),Color("737f7e"),true)
	block(Vector3(8,.55,9.2),Vector3(6,1.1,.4),Color("737f7e"),true)
	add_gate("gallery",Vector3(2.5,.7,9.2),Vector3(3,1.4,.35),Color("9c8c5e"))
	block(Vector3(-12,.01,-11),Vector3(11,.1,10),Color("73776a"))
	block(Vector3(-12,1.4,-17),Vector3(11,2.8,.3),Color("5b625b"),true)
	block(Vector3(11,.01,-11),Vector3(18,.1,12),Color("747d75"))
	block(Vector3(11,1.4,-19),Vector3(18,2.8,.3),Color("657469"),true)
	label_world("ЖУРНАЛ ОСМОТРА + СХЕМА",ARCHIVE+Vector3(0,2,0),.007)
	label_world("ЖИВАЯ ДИСПЕТЧЕРСКАЯ",Vector3(11,3,-18),.009)
	label_world("ОБРАТНЫЙ КОНТАКТ",CONTACT+Vector3(0,2,0),.007)
	label_world("ГЛАВНЫЙ ПУТЬ · ОПОРА ПОД ВОДОЙ",Vector3(1,.7,2),.007)
	for point in [HANDLE,ARCHIVE,MAIN,SERVICE,RECORDER,SIGN]:
		block(point+Vector3(0,.5,-.85),Vector3(1.1,1,.65),Color("83806b"),true)
	main_indicator=block(MAIN+Vector3(0,1.4,-.85),Vector3(.5,.35,.15),Color("bc6854"))
	service_indicator=block(SERVICE+Vector3(0,1.4,-.85),Vector3(.5,.35,.15),Color("95b59b"))
	for i in 8:
		block(GAUGE+Vector3(-1.5,.25+i*.23,0),Vector3(.28,.12,.12),Color("e4d3a2") if i%2==0 else Color("ba7454"))
	label_world("РЕЙКА · СЛУЖЕБНЫЙ КРАЙ СУХОЙ",GAUGE+Vector3(0,2.5,0),.007)
	block(CONTACT+Vector3(0,.6,-.8),Vector3(.7,1.2,.7),Color("798c83"),true)
	block(CACHE+Vector3(-.8,.45,0),Vector3(.6,.9,1),Color("867b60"),true)
	label_world("ЗАПАС СМЕНЫ",CACHE+Vector3(0,1.8,0),.007)
	add_person("valentina",VALENTINA,1.68);add_person("nina",Vector3(17,0,5),1.68)
	add_person("pavel",Vector3(-18,0,14),1.76)
	for point in [HANDLE,ARCHIVE,GAUGE,CONTACT,start_point]:lamp(point+Vector3(-2,0,-2))

func spawn_encounters() -> void:
	spawn_actor("walker",Vector3(22,0,-6));spawn_actor("runner",Vector3(-4,0,-20))

func has(flag: String) -> bool:return bool(state.get(flag,false))

func get_options() -> Array:
	var result: Array=[]
	if not has("handle"):result.append(["handle",HANDLE,"Вставить штатный фиксатор рукояти"])
	elif not has("met"):result.append(["meet",VALENTINA,"Поговорить с Валентиной"])
	if not has("inspection"):result.append(["archive",ARCHIVE,"Сверить схему и журнал опор"])
	if has("inspection") and not has("water"):result.append(["water",GAUGE,"Сравнить рейку с отметкой опоры"])
	if has("met") and has("water"):
		result.append(["main",MAIN,"Открыть главный путь" if has("main_closed") else "Закрыть главный путь"])
		result.append(["service",SERVICE,"Закрыть служебный путь" if has("service_open") else "Открыть служебный путь"])
		if not has("contact"):result.append(["contact",CONTACT,"Проверить физический обратный контакт"])
	if has("met") and not has("heard"):result.append(["play",RECORDER,"Включить оба канала при Валентине"])
	if has("heard") and str(state.get("audience",""))=="":
		result.append(["all",ALL,"Прослушать запись вместе в вагоне"])
		if str(campaign_data.get("recording_policy","hold"))!="share":result.append(["archive_only",PRIVATE,"Опечатать оригинал без общего прослушивания"])
	if str(state.get("audience",""))!="" and str(state.get("statement",""))=="":
		result.append(["sign",SIGN,"Подписать только свою часть хронологии"])
		result.append(["defer",DEFER,"Передать документы, написать заявление позже"])
	if not has("cache"):result.append(["cache",CACHE,"Взять разовый запас смены"])
	if has("contact") and str(state.get("statement",""))!="":result.append(["depart",start_point,"К служебному переходу с Валентиной"])
	return result

func act(action: String) -> bool:
	match action:
		"handle":
			if has("handle"):return false
			state["handle"]=true;say("Валентина разжимает пальцы. «Спасибо. Пружину давно надо было менять». Артём проверяет штатный фиксатор.",6)
		"meet":
			if not has("handle") or has("met"):return false
			state["met"]=true;say("Валентина: я приказала не останавливаться. В журнале моя фамилия. Артём: а людей видел я. Нина: каждый расскажет за себя.",9)
		"archive":
			if has("inspection"):return false
			state["inspection"]=true;say("Главная насыпь низкая; служебный настил стоит на отдельном фундаменте. На схеме: закрыть главный, открыть служебный, проверить контакт с галереи.",8)
		"water":
			if not has("inspection") or has("water"):return false
			state["water"]=true;say("Нина: вода выше основания главной опоры. Служебный край сухой, опора цела. Теперь можно выбирать путь — по осмотру, не по зелёной лампе.",8)
		"main","service":
			if not has("met") or not has("water"):return false
			var flag="main_closed" if action=="main" else "service_open"
			state[flag]=not has(flag);state["contact"]=false
			say(("Главный закрыт. " if has("main_closed") else "Главный открыт. ")+("Служебный открыт. " if has("service_open") else "Служебный закрыт. ")+"После изменения рукояток обратный контакт нужно проверить снова.",6)
		"contact":
			if not has("main_closed") or not has("service_open") or not has("water") or has("contact"):
				say("Контакт не подтверждает безопасный маршрут. Главный должен быть закрыт, служебный открыт после проверки воды.",5);return false
			state["contact"]=true;say("Контакт на галерее совпал с рукоятками. Служебный путь подтверждён. Калитка нижней галереи открылась: к вагону теперь ближе.",6)
		"play":
			if not has("met") or has("heard"):return false
			state["heard"]=true
			if str(campaign_data.get("recording_policy","hold"))=="share":state["audience"]="all"
			say("Валентина слушает оригинал до конца и сверяет время с журналом. «Мой приказ. И моё подтверждение. Запишите оба, без сокращений».",9)
		"all","archive_only":
			if not has("heard") or str(state.get("audience",""))!="":return false
			if action=="archive_only" and str(campaign_data.get("recording_policy","hold"))=="share":return false
			state["audience"]="all" if action=="all" else "archive"
			say("В вагоне слушают оба канала. Павел просит не перематывать второй. Теперь каждый может рассказать сам." if action=="all" else "При Павле опечатывают оригинал. Нина: я помогу. Только больше не называй это нашим решением.",8)
		"sign","defer":
			if str(state.get("audience",""))=="" or str(state.get("statement",""))!="":return false
			state["statement"]="signed" if action=="sign" else "deferred"
			say("Артём: видел людей. Запросил подтверждение. Прошёл без остановки. Каждый подписывает свою часть, не чужое признание." if action=="sign" else "Артём: я не готов написать всё сейчас. Валентина: тогда не подписывайте чужой пересказ. Журнал и кассету всё равно передадим.",8)
		"cache":
			if has("cache"):return false
			state["cache"]=true;flares=mini(5,flares+1);hero.health=minf(100,hero.health+25);say("Разовый запас смены: перевязка и сигнальная ракета.",4)
		"depart":
			if not has("contact") or str(state.get("statement",""))=="":return false
			depart({"dispatch_verified":true,"recording_audience":state["audience"],"statement":state["statement"],"valentina_boarded":true,"valentina_heard":true});return true
		_:return false
	return true

func apply_state() -> void:
	set_gate_open("gallery",has("contact"))
	if is_instance_valid(main_indicator):main_indicator.rotation.z=.55 if has("main_closed") else 0.0
	if is_instance_valid(service_indicator):service_indicator.rotation.z=-.55 if has("service_open") else 0.0

func task_text() -> String:
	if not has("handle"):return "Освободить руку Валентины штатным фиксатором в диспетчерской"
	if not has("met"):return "Поговорить с живой Валентиной у ручного поста"
	if not has("inspection"):return "В архиве найти схему и отметку осмотра опоры"
	if not has("water"):return "С Ниной сверить рейку на восточной галерее"
	if not has("contact"):return "Закрыть главный, открыть служебный; подтвердить контакт на южной галерее"
	if not has("heard"):return "Включить оригинал записи при Валентине"
	if str(state.get("audience",""))=="":return "Выбрать аудиторию: общий стол в вагоне или опечатать оригинал у магнитофона"
	if str(state.get("statement",""))=="":return "У стола подписать свою часть; у выхода — отложить заявление"
	return "Вернуться к составу · служебный путь подтверждён"
