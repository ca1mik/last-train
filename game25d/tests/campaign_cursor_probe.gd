extends SceneTree
func _initialize() -> void:
	var data=JSON.parse_string('{"version":2,"chapter":2,"mikhail_boarded":true}')
	print("QA_USER_DIR=",OS.get_user_data_dir())
	print("JSON_NUMERIC_PROBE version=",data.version," int_membership=",data.version in [1,2]," equality=",data.version==2)
	quit()
