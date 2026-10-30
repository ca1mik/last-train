extends RefCounted
## Received dialogue is retained even when its presentation is postponed by combat.
var entries: Array=[]
var path:="user://journal-v045.json"
static var started: Dictionary={}

func _init() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--save-slot="):
			var slot=arg.trim_prefix("--save-slot=").get_file()
			if slot.begins_with("qa-"):path="user://journal-"+slot
	# A new campaign must not expose dialogue from a previous playthrough. Reset
	# once per process so checkpoint reconstruction keeps the current journal.
	if not started.has(path):
		started[path]=true
		if OS.get_cmdline_user_args().has("--fresh"):
			var fresh=FileAccess.open(path,FileAccess.WRITE)
			if fresh:fresh.store_string("[]");fresh.close()
	if FileAccess.file_exists(path):
		var value=JSON.parse_string(FileAccess.get_file_as_string(path))
		if value is Array:entries=value

func add(text: String,scope: String) -> void:
	for entry in entries:
		if entry is Dictionary and entry.get("text","")==text and entry.get("scope","")==scope:return
	entries.append({"text":text,"scope":scope})
	var file=FileAccess.open(path,FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(entries));file.close()

func latest(scope: String) -> String:
	for i in range(entries.size()-1,-1,-1):
		if entries[i] is Dictionary and entries[i].get("scope","")==scope:return entries[i].get("text","")
	return ""

func text_for(scope: String) -> String:
	var parts: Array[String]=[]
	for entry in entries:
		if entry is Dictionary and entry.get("scope","")==scope:parts.append(String(entry.get("text","")))
	return "\n\n────────────────────────\n\n".join(parts) if not parts.is_empty() else "Здесь сохраняются полученные реплики и важные сообщения."
