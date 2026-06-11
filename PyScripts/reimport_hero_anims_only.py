"""THE FROZEN-HERO FIX, part 2: delete the orphaned AnimSequences and reimport
each clip from its ANIM-ONLY FBX, bound to SCB2Hero_Skeleton at import time
(the Skeleton property is read-only after import — binding must happen here).
The mesh, skeleton, and material are untouched."""
import os

import unreal

SRC_DIR = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\ue_ready"
DEST = "/Game/Art/HeroSkel"
CLIPS = {
    "A_Hero_Idle": "hero_idle.fbx",
    "A_Hero_Walk": "hero_walk.fbx",
    "A_Hero_Run": "hero_run.fbx",
    "A_Hero_Jump": "hero_jump.fbx",
    "A_Hero_Strike1": "hero_strike1.fbx",
    "A_Hero_Strike2": "hero_strike2.fbx",
    "A_Hero_Haymaker": "hero_haymaker.fbx",
    "A_Hero_HitReact": "hero_hitreact.fbx",
    "A_Hero_Relight": "hero_relight.fbx",
}

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")

skel = unreal.load_asset(f"{DEST}/SCB2Hero_Skeleton")
if not isinstance(skel, unreal.Skeleton):
    raise SystemExit("NO_SKELETON")

tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary

ok_count = 0
for name, fbx in CLIPS.items():
    src = os.path.join(SRC_DIR, fbx)
    if not os.path.isfile(src):
        print(f"FBX_MISSING: {src}")
        continue
    path = f"{DEST}/{name}"
    if eal.does_asset_exist(path):
        eal.delete_asset(path)

    ui = unreal.FbxImportUI()
    ui.import_mesh = False
    ui.import_as_skeletal = False
    ui.import_animations = True
    ui.import_materials = False
    ui.import_textures = False
    ui.skeleton = skel
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    # THE MISSING KEY: without original_import_type=SKELETAL_MESH the automated
    # anim-only path silently drops the target-skeleton binding (skeleton=NONE,
    # frozen hero). Known legacy-FBX automation quirk.
    ui.set_editor_property("original_import_type", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ad = ui.anim_sequence_import_data
    ad.set_editor_property("import_uniform_scale", 1.0)
    ad.set_editor_property("snap_to_closest_frame_boundary", True)

    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = DEST
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = False
    task.options = ui
    tools.import_asset_tasks([task])

    a = unreal.load_asset(path)
    if isinstance(a, unreal.AnimSequence):
        s = a.get_editor_property("skeleton")
        bound = (s == skel)
        ok_count += int(bound)
        print(f"REIMPORT {name}: len={a.get_play_length():.3f}s skeleton="
              f"{s.get_name() if s else 'NONE'} {'OK' if bound else 'ORPHANED'}")
    else:
        print(f"REIMPORT {name}: FAILED ({type(a).__name__ if a else 'missing'})")

eal.save_directory(DEST, recursive=True)
print(f"ANIM_REIMPORT_{'DONE' if ok_count == len(CLIPS) else 'INCOMPLETE'}: {ok_count}/{len(CLIPS)} bound")
