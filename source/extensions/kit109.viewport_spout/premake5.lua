-- Use folder name to build extension name and tag.
local ext = get_current_extension_info()

project_ext (ext)

-- Link the Python packages and bundled spout library into the build target directory.
repo_build.prebuild_link {
    { "kit109", ext.target_dir.."/kit109" },
    { "spout",  ext.target_dir.."/spout"  },
}
