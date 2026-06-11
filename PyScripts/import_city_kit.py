"""Import the Neon District kit as static meshes -> /Game/Art/CityKit/<name>/SM_<name>.
Legacy FBX path (Interchange banned); textures arrive embedded via Blender bind."""
import os

import unreal

SRC_DIR = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\ue_ready_city"
DEST_ROOT = "/Game/Art/CityKit"

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
tools = unreal.AssetToolsHelpers.get_asset_tools()

fbxes = sorted(f for f in os.listdir(SRC_DIR) if f.lower().endswith(".fbx"))
if not fbxes:
    raise SystemExit("NO_FBXES")

for fbx in fbxes:
    stem = os.path.splitext(fbx)[0]
    dest = f"{DEST_ROOT}/{stem}"
    if unreal.EditorAssetLibrary.does_directory_exist(dest):
        unreal.EditorAssetLibrary.delete_directory(dest)

    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_animations = False
    ui.import_materials = True
    ui.import_textures = True
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    sd = ui.static_mesh_import_data
    sd.set_editor_property("import_uniform_scale", 1.0)
    sd.set_editor_property("combine_meshes", True)

    task = unreal.AssetImportTask()
    task.filename = os.path.join(SRC_DIR, fbx)
    task.destination_path = dest
    task.destination_name = f"SM_{stem}"
    task.automated = True
    task.save = True
    task.replace_existing = False
    task.options = ui
    tools.import_asset_tasks([task])

    paths = list(task.get_editor_property("imported_object_paths") or [])
    if paths:
        asset = unreal.load_asset(paths[0])
        if isinstance(asset, unreal.StaticMesh):
            b = asset.get_bounding_box()
            print(f"CITY_OK: {stem} ({b.max.z - b.min.z:.0f}uu tall)")
        else:
            print(f"CITY_OK: {stem}")
    else:
        print(f"CITY_FAIL: {stem}")

unreal.EditorAssetLibrary.save_directory(DEST_ROOT, recursive=True)
print("CITY_KIT_IMPORT_DONE")
