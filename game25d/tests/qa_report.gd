extends RefCounted
## Keep versioned build evidence separate from historical default outputs.
static func path(fallback: String) -> String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--qa-report="):
			var result=arg.trim_prefix("--qa-report=")
			DirAccess.make_dir_recursive_absolute(result.get_base_dir())
			return result
	return fallback
