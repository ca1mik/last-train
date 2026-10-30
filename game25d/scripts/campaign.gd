extends RefCounted
## The cursor never owns a level checkpoint. New runs and replays select new
## namespaces; legacy checkpoints and the previous profile are never deleted.
const FIRST="res://expedition.tscn"
const HOSPITAL="res://hospital.tscn"
const FOREST="res://forest.tscn"
const SETTLEMENT="res://settlement.tscn"
const FREIGHT="res://freight.tscn"
const DISPATCH="res://dispatch.tscn"
const CROSSING="res://crossing.tscn"
const FINALE="res://finale.tscn"
const EPILOGUE="res://epilogue.tscn"
const SCENES={1:FIRST,2:HOSPITAL,3:FOREST,4:SETTLEMENT,5:FREIGHT,6:DISPATCH,7:CROSSING,8:FINALE,9:EPILOGUE}
static var _profile_loaded:=false
static var _namespace:=""
static var _replay:=false
static var _main_namespace:=""

static func qa_slot() -> String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--save-slot="):
			var slot=arg.trim_prefix("--save-slot=").get_file()
			if slot.begins_with("qa-"):return slot
	return ""

static func profile_path() -> String:
	return "user://campaign-profile-"+qa_slot() if qa_slot()!="" else "user://campaign-profile-v049.json"

static func _ensure_profile() -> void:
	if _profile_loaded:return
	_profile_loaded=true
	if not FileAccess.file_exists(profile_path()):return
	var data=JSON.parse_string(FileAccess.get_file_as_string(profile_path()))
	if data is Dictionary and data.get("active_run",null) is String:
		var candidate: String=data.active_run
		if candidate.begins_with("run-") and candidate==candidate.get_file():_namespace=candidate

static func path() -> String:
	_ensure_profile()
	if _namespace!="":return "user://profiles/"+_namespace+"/campaign.json"
	return "user://campaign-"+qa_slot() if qa_slot()!="" else "user://campaign-v048.json"

static func checkpoint_path(stem: String,legacy_basename: String) -> String:
	_ensure_profile()
	if _namespace=="":return legacy_basename if legacy_basename.begins_with("user://") else "user://"+legacy_basename
	var directory="user://profiles/"+_namespace
	DirAccess.make_dir_recursive_absolute(directory)
	return directory+"/"+stem.get_file()+".json"

static func read() -> Dictionary:
	var source=path()
	# 0.45 continues owning its old cursor; this migration only reads it.
	if not FileAccess.file_exists(source) and source=="user://campaign-v048.json":source="user://campaign-v037.json"
	if not FileAccess.file_exists(source):return {}
	var data=JSON.parse_string(FileAccess.get_file_as_string(source))
	if not data is Dictionary:return {}
	var version=data.get("version",0)
	var chapter=data.get("chapter",1)
	# JSON numbers are floats. Array membership is type-strict in Godot even
	# though numeric == is not. Validate exact integers before casting.
	if not (version is int or version is float) or not (chapter is int or chapter is float):return {}
	if not is_finite(float(version)) or not is_finite(float(chapter)):return {}
	if float(version)!=floor(float(version)) or float(chapter)!=floor(float(chapter)):return {}
	if int(version) not in [1,2,3] or not SCENES.has(int(chapter)):return {}
	if int(version)<3 and int(chapter)>3:return {}
	data.version=int(version);data.chapter=int(chapter)
	return data

static func saved_scene() -> String:
	return SCENES.get(read().get("chapter",1),FIRST)

static func has_launch_override() -> bool:
	for arg in OS.get_cmdline_user_args():
		if arg in ["--hospital-evacuation-preview","--map-lab","--forest-stop","--freight-yard","--hospital-branch","--first-expedition","--continue-campaign"]:return true
	return false

static func current_scene() -> String:
	var args=OS.get_cmdline_user_args()
	# Explicit previews choose their opening scene, never the saved progress.
	if args.has("--hospital-evacuation-preview"):return HOSPITAL
	if args.has("--map-lab"):return "res://locations.tscn"
	if args.has("--forest-stop"):return FOREST
	if args.has("--freight-yard"):return "res://wasteland.tscn"
	if args.has("--hospital-branch"):return HOSPITAL
	if args.has("--first-expedition"):return FIRST
	return saved_scene()

static func _write_json(destination: String,data: Dictionary) -> Error:
	var directory_result=DirAccess.make_dir_recursive_absolute(destination.get_base_dir())
	if directory_result!=OK:return directory_result
	var temporary=destination+".tmp"
	var file=FileAccess.open(temporary,FileAccess.WRITE)
	if not file:return FileAccess.get_open_error()
	file.store_string(JSON.stringify(data));file.flush()
	var result=file.get_error();file.close()
	if result!=OK:return result
	return DirAccess.rename_absolute(temporary,destination)

static func write_cursor(data: Dictionary) -> Error:
	return _write_json(path(),data)

static func mark_departure(chapter: int,outcomes: Dictionary={}) -> Error:
	if not SCENES.has(chapter):return ERR_INVALID_PARAMETER
	var data=read().duplicate(true)
	for key in outcomes:
		if key not in ["version","chapter","finale_snapshot"]:data[key]=outcomes[key]
	data.version=3;data.chapter=chapter
	if chapter==7 and not _replay:
		var snapshot=data.duplicate(true);snapshot.erase("finale_snapshot")
		data.finale_snapshot=snapshot
	return write_cursor(data)

static func mark_hospital_departure(truth: String) -> Error:
	if truth not in ["admit","defend"]:return ERR_INVALID_PARAMETER
	return mark_departure(3,{"mikhail_boarded":true,"hospital_residents":4,"hospital_truth":truth})

static func depart(tree: SceneTree) -> Error:
	var result=mark_departure(2,{"mikhail_boarded":true})
	if result!=OK:return result
	tree.root.set_meta("campaign_playing",true)
	return tree.change_scene_to_file(HOSPITAL)

static func _fresh_namespace(prefix: String) -> String:
	return prefix+"-"+str(int(Time.get_unix_time_from_system()))+"-"+str(Time.get_ticks_usec())

static func new_run(tree: SceneTree=null) -> Error:
	_ensure_profile()
	var previous=_namespace
	_namespace=_fresh_namespace("run")
	var result=write_cursor({"version":3,"chapter":1})
	if result==OK:result=_write_json(profile_path(),{"version":1,"active_run":_namespace})
	if result!=OK:_namespace=previous;return result
	_replay=false;_main_namespace=""
	if tree:
		tree.root.set_meta("campaign_playing",true)
		return tree.change_scene_to_file(FIRST)
	return OK

static func is_replay() -> bool:return _replay

static func begin_replay(tree: SceneTree=null) -> Error:
	if _replay:return ERR_ALREADY_IN_USE
	var main=read()
	var snapshot=main.get("finale_snapshot",{})
	if not snapshot is Dictionary or int(snapshot.get("chapter",0))!=7:return ERR_UNAVAILABLE
	_main_namespace=_namespace;_namespace=_fresh_namespace("replay")
	var result=write_cursor(snapshot.duplicate(true))
	if result!=OK:_namespace=_main_namespace;_main_namespace="";return result
	_replay=true
	if tree:
		tree.root.set_meta("campaign_playing",true)
		return tree.change_scene_to_file(CROSSING)
	return OK

static func finish(outcome: String,outcomes: Dictionary={}) -> Error:
	if outcome.strip_edges().is_empty():return ERR_INVALID_PARAMETER
	var final_outcomes=outcomes.duplicate(true)
	final_outcomes.ending=outcome;final_outcomes.completed=true
	return mark_departure(9,final_outcomes)

static func finish_replay(tree: SceneTree=null) -> Error:
	if not _replay:return ERR_UNAVAILABLE
	_namespace=_main_namespace;_main_namespace="";_replay=false
	if tree:
		tree.root.set_meta("campaign_playing",true)
		return tree.change_scene_to_file(saved_scene())
	return OK
