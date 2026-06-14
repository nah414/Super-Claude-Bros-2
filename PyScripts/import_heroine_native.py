import os
import unreal

DROPS = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\heroine"
MESH_FBX = os.path.join(DROPS, "rig", "heroine_rig_rigged_character_fbx_url.fbx")
CLIPS = {
    "Idle": "anim_idle\\heroine_idle_animation_fbx_url.fbx",
    "Walk": "anim_walk\\heroine_walk_animation_fbx_url.fbx",
    "Run": "anim_run\\heroine_run_animation_fbx_url.fbx",
    "Jump": "anim_jump\\heroine_jump_animation_fbx_url.fbx",
    "Strike1": "anim_strike1\\heroine_strike1_animation_fbx_url.fbx",
    "Strike2": "anim_strike2\\heroine_strike2_animation_fbx_url.fbx",
    "Haymaker": "anim_haymaker\\heroine_haymaker_animation_fbx_url.fbx",
    "HitReact": "anim_hitreact\\heroine_hitreact_animation_fbx_url.fbx",
    "Relight": "anim_relight\\heroine_relight_animation_fbx_url.fbx",
    "CrouchWalk": "anim_crouchwalk\\heroine_crouchwalk_animation_fbx_url.fbx",
}
PROBE = "/Game/_ProbeHeroine"
DEST = "/Game/Art/HeroineSkelV2"
NAME = "SCB2Heroine"
TARGET_HALF_EXTENT_Z = 64.0   # 160 cm roster -> 128 uu in-game (the 0.8 family rule)

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def import_skeletal(fbx, dest, name, scale, skel=None):
    ui = unreal.FbxImportUI()
    if skel is None:
        ui.import_mesh = True
        ui.import_as_skeletal = True
        ui.import_animations = False
        ui.import_materials = True
        ui.import_textures = True
        ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
        ui.skeletal_mesh_import_data.set_editor_property("import_uniform_scale", scale)
        ui.skeletal_mesh_import_data.set_editor_property("convert_scene", True)
    else:
        ui.import_mesh = False
        ui.import_as_skeletal = False
        ui.import_animations = True
        ui.import_materials = False
        ui.import_textures = False
        ui.skeleton = skel
        ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
        ui.anim_sequence_import_data.set_editor_property("import_uniform_scale", scale)
        ui.anim_sequence_import_data.set_editor_property("snap_to_closest_frame_boundary", True)
        ui.anim_sequence_import_data.set_editor_property("convert_scene", True)
    t = unreal.AssetImportTask()
    t.filename = fbx
    t.destination_path = dest
    t.destination_name = name
    t.automated = True
    t.save = True
    t.replace_existing = False
    t.options = ui
    tools.import_asset_tasks([t])
    # FBXIT_ANIMATION also materializes a redundant full SkeletalMesh + PhysicsAsset next to
    # the AnimSequence; purge them so the repo never re-bloats (game loads only SCB2<Char> + *_Anim).
    if skel is not None:
        for dup in (f"{dest}/{name}", f"{dest}/{name}_PhysicsAsset"):
            if eal.does_asset_exist(dup) and not isinstance(unreal.load_asset(dup), unreal.AnimSequence):
                eal.delete_asset(dup)
                print(f"PURGE_DUP: {dup}")


if eal.does_directory_exist(PROBE):
    eal.delete_directory(PROBE)
import_skeletal(MESH_FBX, PROBE, "ProbeMesh", 1.0)
probe = unreal.load_asset(f"{PROBE}/ProbeMesh")
z = probe.get_bounds().box_extent.z
scale = TARGET_HALF_EXTENT_Z / max(z, 0.001)
print(f"HEROINE_PROBE: native z={z:.1f} -> scale {scale:.4f}")
eal.delete_directory(PROBE)

if eal.does_directory_exist(DEST):
    ok = eal.delete_directory(DEST)
    if not ok:
        raise SystemExit("V2_WIPE_FAILED (CDO lock?) — bump folder name")
import_skeletal(MESH_FBX, DEST, NAME, scale)
mesh = unreal.load_asset(f"{DEST}/{NAME}")
skeleton = unreal.load_asset(f"{DEST}/{NAME}_Skeleton")
ext = mesh.get_bounds().box_extent
print(f"HEROINE_MESH: extent z={ext.z:.1f} (target {TARGET_HALF_EXTENT_Z})")

bound = 0
for clip, rel in CLIPS.items():
    fbx = os.path.join(DROPS, rel)
    if not os.path.isfile(fbx):
        print(f"HEROINE {clip}: FBX_MISSING {fbx}")
        continue
    import_skeletal(fbx, DEST, f"A_Heroine_{clip}", scale, skel=skeleton)
    found = None
    for cand in (f"{DEST}/A_Heroine_{clip}_Anim", f"{DEST}/A_Heroine_{clip}"):
        a = unreal.load_asset(cand)
        if isinstance(a, unreal.AnimSequence):
            found = (cand, a)
            break
    if not found:
        print(f"HEROINE {clip}: NO_ANIMSEQUENCE")
        continue
    path, a = found
    s = a.get_editor_property("skeleton")
    is_bound = (s == skeleton)
    bound += int(is_bound)
    print(f"HEROINE {clip}: {path.split('/')[-1]} len={a.get_play_length():.2f}s {'BOUND' if is_bound else 'ORPHANED'}")

eal.save_directory(DEST, recursive=True)
print(f"HEROINE_{'SUCCESS' if bound == len(CLIPS) else 'PARTIAL'}: {bound}/{len(CLIPS)} bound, scale={scale:.4f}")
