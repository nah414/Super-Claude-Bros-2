"""Import the Spark Heroine as SkeletalMesh + 4 clips — same battle-tested recipe
as the hero: legacy FBX only, wipe-then-fresh (reimport drops animations).
She banks at /Game/Art/HeroineSkel until a playable-character system arrives.
"""
import os

import unreal

SRC_DIR = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\ue_ready_heroine"
MESH_FBX = os.path.join(SRC_DIR, "heroine_rigged.fbx")
ANIM_FBXES = {
    "A_Heroine_Idle": os.path.join(SRC_DIR, "heroine_idle.fbx"),
    "A_Heroine_Walk": os.path.join(SRC_DIR, "heroine_walk.fbx"),
    "A_Heroine_Run": os.path.join(SRC_DIR, "heroine_run.fbx"),
    "A_Heroine_Jump": os.path.join(SRC_DIR, "heroine_jump.fbx"),
}
DEST = "/Game/Art/HeroineSkel"
NAME = "SCB2Heroine"

if not os.path.isfile(MESH_FBX):
    raise SystemExit(f"FBX_MISSING: {MESH_FBX}")

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")

if unreal.EditorAssetLibrary.does_directory_exist(DEST):
    unreal.EditorAssetLibrary.delete_directory(DEST)
    print(f"WIPED: {DEST}")

tools = unreal.AssetToolsHelpers.get_asset_tools()


def run_task(filename, dest_name, ui):
    task = unreal.AssetImportTask()
    task.filename = filename
    task.destination_path = DEST
    task.destination_name = dest_name
    task.automated = True
    task.save = True
    task.replace_existing = False
    task.options = ui
    tools.import_asset_tasks([task])
    return list(task.get_editor_property("imported_object_paths") or [])


ui = unreal.FbxImportUI()
ui.import_mesh = True
ui.import_as_skeletal = True
ui.import_animations = False
ui.import_materials = True
ui.import_textures = True
ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
ui.skeletal_mesh_import_data.set_editor_property("import_uniform_scale", 1.0)
ui.skeletal_mesh_import_data.set_editor_property("convert_scene", True)

for p in run_task(MESH_FBX, NAME, ui):
    print(f"IMPORTED_MESH: {p}")

skeleton = unreal.load_asset(f"{DEST}/{NAME}_Skeleton")
if not skeleton:
    raise SystemExit("IMPORT_FAILED: no skeleton")

for anim_name, fbx in ANIM_FBXES.items():
    if not os.path.isfile(fbx):
        print(f"ANIM_MISSING: {fbx}")
        continue
    aui = unreal.FbxImportUI()
    aui.import_mesh = False
    aui.import_as_skeletal = False
    aui.import_animations = True
    aui.import_materials = False
    aui.import_textures = False
    aui.skeleton = skeleton
    aui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    aui.anim_sequence_import_data.set_editor_property("import_uniform_scale", 1.0)
    aui.anim_sequence_import_data.set_editor_property("snap_to_closest_frame_boundary", True)
    for p in run_task(fbx, anim_name, aui):
        print(f"IMPORTED_ANIM: {p}")

unreal.EditorAssetLibrary.save_directory(DEST, recursive=True)
print("HEROINE_SKEL_IMPORT_DONE")
