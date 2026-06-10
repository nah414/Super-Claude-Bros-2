"""Import the Meshy hero FBX as a SkeletalMesh + animations — legacy FBX path only.

Interchange's glb/fbx unit conversion proved non-deterministic (the invisible-hero
saga), so we disable it for FBX and use the classic FbxImporter. Blender baked real
centimeters in. Gotcha learned the hard way: replace_existing turns the task into a
REIMPORT, and skeletal reimports silently skip animations — so we wipe the folder
and import fresh: mesh first, then each clip as an animation-only task.

Run:
  UnrealEditor-Cmd.exe <proj> -ExecutePythonScript=PyScripts/import_hero_skeletal.py
  -RenderOffscreen -unattended
"""
import os

import unreal

SRC_DIR = r"C:\Users\Atomn\mario2\_prep\meshy_drops\ue_ready"
MESH_FBX = os.path.join(SRC_DIR, "automaton_walking.fbx")
ANIM_FBXES = {
    "A_Hero_Walk": os.path.join(SRC_DIR, "automaton_walking.fbx"),
    "A_Hero_Run": os.path.join(SRC_DIR, "automaton_running.fbx"),
    "A_Hero_SpinJump": os.path.join(SRC_DIR, "automaton_spinjump.fbx"),
}
DEST = "/Game/Art/HeroSkel"
NAME = "SCB2Hero"

if not os.path.isfile(MESH_FBX):
    raise SystemExit(f"FBX_MISSING: {MESH_FBX}")

# Kill the Interchange roulette for FBX: fall back to the deterministic legacy importer.
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")

# Clean slate so every run is a fresh import, never a reimport.
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


# ---- 1) Skeletal mesh (+skeleton +physics asset) ----
ui = unreal.FbxImportUI()
ui.import_mesh = True
ui.import_as_skeletal = True
ui.import_animations = False
ui.import_materials = True
ui.import_textures = True
ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
sk = ui.skeletal_mesh_import_data
sk.set_editor_property("import_uniform_scale", 1.0)
sk.set_editor_property("convert_scene", True)

mesh_paths = run_task(MESH_FBX, NAME, ui)
for p in mesh_paths:
    print(f"IMPORTED_MESH: {p}")
if not mesh_paths:
    raise SystemExit("IMPORT_FAILED: mesh")

skeleton = unreal.load_asset(f"{DEST}/{NAME}_Skeleton")
if not skeleton:
    raise SystemExit("IMPORT_FAILED: no skeleton asset")

mesh = unreal.load_asset(f"{DEST}/{NAME}")
if isinstance(mesh, unreal.SkeletalMesh):
    ext = mesh.get_bounds().box_extent
    print(f"SKELMESH extent: x={ext.x:.1f} y={ext.y:.1f} z={ext.z:.1f} uu")

# ---- 2) Each clip as an animation-only import bound to that skeleton ----
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
    ad = aui.anim_sequence_import_data
    ad.set_editor_property("import_uniform_scale", 1.0)
    ad.set_editor_property("snap_to_closest_frame_boundary", True)
    for p in run_task(fbx, anim_name, aui):
        print(f"IMPORTED_ANIM: {p}")

unreal.EditorAssetLibrary.save_directory(DEST, recursive=True)
print("HERO_SKEL_IMPORT_DONE")
