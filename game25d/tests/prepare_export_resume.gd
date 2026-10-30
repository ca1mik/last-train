extends SceneTree
## Select an existing ordinary-input QA checkpoint for exported-EXE boot.
## Only the QA campaign cursor is copied; checkpoint health/position are untouched.
func _initialize() -> void:
	var slot="qa-native-hospital-winch-v038.json"
	var checkpoint="user://hospital-"+slot
	var before=FileAccess.get_sha256(checkpoint)
	var data=JSON.parse_string(FileAccess.get_file_as_string(checkpoint))
	if not data is Dictionary or data.get("mission",0)!=1:push_error("Expected completed ordinary-input hospital QA checkpoint");quit(1);return
	var cursor=FileAccess.get_file_as_string("user://campaign-qa-build-transition.json")
	var parsed=JSON.parse_string(cursor)
	if not parsed is Dictionary or parsed.get("chapter",0)!=2:push_error("Missing actual transition-test campaign cursor");quit(1);return
	var file=FileAccess.open("user://campaign-"+slot,FileAccess.WRITE);file.store_string(cursor);file.close()
	var unchanged=before==FileAccess.get_sha256(checkpoint)
	file=FileAccess.open("H:/game/release/motion-v038/export-prep.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"scope":"QA cursor fixture copied from actual E transition test; ordinary-input hospital checkpoint untouched","checkpoint_sha256":before,"checkpoint_unchanged":unchanged,"mission":data.mission,"method":data.route_method},"  "));file.close()
	print("EXPORT_RESUME_PREP checkpoint_unchanged=",unchanged);quit(0 if unchanged else 1)
