extends SceneTree
func _initialize() -> void:
	var source="user://qa-chapter1-stopper-v039.json"
	var target="user://qa-export-exit-v039.json"
	var before=FileAccess.get_sha256(source)
	var contents=FileAccess.get_file_as_string(source)
	var data=JSON.parse_string(contents)
	assert(data is Dictionary and data.get("mission")==3 and data.get("exit_stage")==6)
	FileAccess.open(target,FileAccess.WRITE).store_string(contents)
	# Only a QA cursor selects chapter 1; the real ordinary-input checkpoint is
	# copied byte-for-byte. This is not a new playthrough or a player save change.
	FileAccess.open("user://campaign-qa-export-exit-v039.json",FileAccess.WRITE).store_string(JSON.stringify({"version":1,"chapter":1,"mikhail_boarded":true}))
	var report={"scope":"QA cursor reset to chapter1; byte-identical copy of actual ordinary-input checkpoint", "source":source,"target":target,"source_unchanged":before==FileAccess.get_sha256(source),"copy_identical":before==FileAccess.get_sha256(target),"sha256":before,"mission":3,"exit_stage":6}
	DirAccess.make_dir_recursive_absolute("H:/game/release/chapter1-v039")
	FileAccess.open("H:/game/release/chapter1-v039/export-prep.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("EXPORT_EXIT_PREP ",report.source_unchanged," ",report.copy_identical);quit()
