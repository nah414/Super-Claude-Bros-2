"""HERO IMPORT, ALL-IN-ONE, RACE-FREE: wipe -> mesh -> 9 anims -> verify, all in
one process with asserts at every step and a final in-process state dump.
(The multi-process chains were lying to us through log rotation.)

The clip FBXes are MESH-FUL on purpose: the legacy importer only builds proper
track-to-skeleton maps when the FBX carries the skin (heroine-proven). The junk
meshes it spawns are tolerated — they are the price of bound, playable clips.
NEVER delete or rename the _Anim assets (that orphans them — June 11 lesson).

Run: UnrealEditor-Cmd.exe <proj> -ExecutePythonScript=PyScripts/import_hero_all_in_one.py -RenderOffscreen -unattended
"""
import os

import unreal

SRC_DIR = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\ue_ready"
# Virgin folder per import generation: whichever folder the compiled C++ CDO
# references is memory-locked at editor boot (delete_directory returns False and
# reimports silently collide). V3 = the anim-scale fix generation.
DEST = "/Game/Art/HeroSkelV3"
NAME = "SCB2Hero"
# THE ANIM-SCALE FIX: clips are converted at factor 1.0 (no Blender scale bake —
# baking scales the REST pose but not the action curves, which collapsed the
# body). UE applies the 0.8 here instead, scaling rig AND translation tracks
# together. The mesh stays a 0.800-baked conversion; 1.0-clips x 0.8 = match.
CLIP_IMPORT_SCALE = 0.8
CLIPS = ["Idle", "Walk", "Run", "Jump", "Strike1", "Strike2", "Haymaker", "HitReact", "Relight"]

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

# ---- 1) wipe, and PROVE it ----
if eal.does_directory_exist(DEST):
    ok = eal.delete_directory(DEST)
    print(f"STEP1_WIPE: {ok}")
    if not ok:
        raise SystemExit("WIPE_FAILED — directory locked?")
reg = unreal.AssetRegistryHelpers.get_asset_registry()
left = reg.get_assets_by_path(DEST, recursive=True)
print(f"STEP1_REMAINING: {len(left)}")
if len(left) > 0:
    raise SystemExit("WIPE_INCOMPLETE")

# ---- 2) mesh ----
ui = unreal.FbxImportUI()
ui.import_mesh = True
ui.import_as_skeletal = True
ui.import_animations = False
ui.import_materials = True
ui.import_textures = True
ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
ui.skeletal_mesh_import_data.set_editor_property("import_uniform_scale", 1.0)
ui.skeletal_mesh_import_data.set_editor_property("convert_scene", True)
task = unreal.AssetImportTask()
task.filename = os.path.join(SRC_DIR, "hero_rigged.fbx")
task.destination_path = DEST
task.destination_name = NAME
task.automated = True
task.save = True
task.replace_existing = False
task.options = ui
tools.import_asset_tasks([task])

mesh = unreal.load_asset(f"{DEST}/{NAME}")
skeleton = unreal.load_asset(f"{DEST}/{NAME}_Skeleton")
if not isinstance(mesh, unreal.SkeletalMesh) or not isinstance(skeleton, unreal.Skeleton):
    raise SystemExit("STEP2_MESH_FAILED")
ext = mesh.get_bounds().box_extent
print(f"STEP2_MESH: extent z={ext.z:.1f} (66 = correct 132uu hero)")

# ---- 3) anims, with per-clip verification ----
bound = 0
for clip in CLIPS:
    fbx = os.path.join(SRC_DIR, f"hero_{clip.lower()}.fbx")
    if not os.path.isfile(fbx):
        print(f"STEP3 {clip}: FBX_MISSING {fbx}")
        continue
    aui = unreal.FbxImportUI()
    aui.import_mesh = False
    aui.import_as_skeletal = False
    aui.import_animations = True
    aui.import_materials = False
    aui.import_textures = False
    aui.skeleton = skeleton
    aui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    aui.anim_sequence_import_data.set_editor_property("import_uniform_scale", CLIP_IMPORT_SCALE)
    aui.anim_sequence_import_data.set_editor_property("snap_to_closest_frame_boundary", True)
    t = unreal.AssetImportTask()
    t.filename = fbx
    t.destination_path = DEST
    t.destination_name = f"A_Hero_{clip}"
    t.automated = True
    t.save = True
    t.replace_existing = False
    t.options = aui
    tools.import_asset_tasks([t])

    # accept either layout: _Anim (mesh-ful FBX) or canonical (anim-only FBX)
    found = None
    for cand in (f"{DEST}/A_Hero_{clip}_Anim", f"{DEST}/A_Hero_{clip}"):
        a = unreal.load_asset(cand)
        if isinstance(a, unreal.AnimSequence):
            found = (cand, a)
            break
    if not found:
        print(f"STEP3 {clip}: NO_ANIMSEQUENCE_CREATED")
        continue
    path, a = found
    s = a.get_editor_property("skeleton")
    is_bound = (s == skeleton)
    bound += int(is_bound)
    print(f"STEP3 {clip}: {path.split('/')[-1]} len={a.get_play_length():.2f}s "
          f"skeleton={s.get_name() if s else 'NONE'} {'BOUND' if is_bound else 'ORPHANED'}")

eal.save_directory(DEST, recursive=True)
print(f"ALL_IN_ONE_{'SUCCESS' if bound == len(CLIPS) else 'PARTIAL'}: {bound}/{len(CLIPS)} bound")
