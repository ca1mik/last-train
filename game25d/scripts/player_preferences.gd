extends RefCounted
## Audio preferences are independent of campaign checkpoints and QA isolated.
const DEFAULTS={"Master":1.0,"SFX":1.0,"Ambience":.7,"Voice":1.0}
var values: Dictionary=DEFAULTS.duplicate()
var path:="user://preferences-v045.cfg"

func _init() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--save-slot="):
			var slot=arg.trim_prefix("--save-slot=").get_file()
			if slot.begins_with("qa-"):path="user://preferences-"+slot+".cfg"

func load_all() -> void:
	var config=ConfigFile.new()
	if config.load(path)==OK:
		for bus in DEFAULTS:values[bus]=clampf(float(config.get_value("audio",bus,DEFAULTS[bus])),0,1)
	for bus in DEFAULTS:
		if AudioServer.get_bus_index(bus)<0:
			AudioServer.add_bus();var index=AudioServer.bus_count-1;AudioServer.set_bus_name(index,bus);AudioServer.set_bus_send(index,"Master")
		apply(bus)

func apply(bus: String) -> void:
	var index=AudioServer.get_bus_index(bus)
	if index<0:return
	AudioServer.set_bus_mute(index,float(values[bus])<=.001)
	AudioServer.set_bus_volume_db(index,linear_to_db(maxf(float(values[bus]),.0001)))

func set_volume(bus: String,value: float) -> void:
	if not DEFAULTS.has(bus):return
	values[bus]=clampf(value,0,1);apply(bus)
	var config=ConfigFile.new();config.load(path)
	for name in DEFAULTS:config.set_value("audio",name,values[name])
	config.save(path)
