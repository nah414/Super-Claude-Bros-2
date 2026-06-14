"""HERO IMPORT V4 — MESHY-NATIVE FBX, NO BLENDER IN THE ANIMATION PATH.

Blender's GLB->FBX action export has never produced a clip that evaluates
(V2: scale-baked rest vs unbaked curves; V3: consistent 1.0 rig still mush —
the exported curves themselves are the suspect, and no Blender-era clip was
ever seen playing). Meshy provides native FBX per animation; this imports the
whole family — mesh + 9 clips — from Meshy's own exports, scale measured and
applied uniformly in ONE process. Self-consistent by construction.
"""
import os

import unreal

DROPS = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops"
MESH_FBX = os.path.join(DROPS, "white_rig", "white_rig_rigged_character_fbx_url.fbx")
CLIPS = {
    "Idle": "white_anim_idle\\white_idle_animation_fbx_url.fbx",
    "Walk": "white_anim_walk\\white_walk_animation_fbx_url.fbx",
    "Run": "white_anim_run\\white_run_animation_fbx_url.fbx",
    "Jump": "white_anim_jump\\white_jump_animation_fbx_url.fbx",
    "Strike1": "white_anim_strike1\\white_strike1_animation_fbx_url.fbx",
    "Strike2": "white_anim_strike2\\white_strike2_animation_fbx_url.fbx",
    "Haymaker": "white_anim_haymaker\\white_haymaker_animation_fbx_url.fbx",
    "HitReact": "white_anim_hitreact\\white_hitreact_animation_fbx_url.fbx",
    "Relight": "white_anim_relight\\white_relight_animation_fbx_url.fbx",
}
PROBE = "/Game/_ProbeNative"
DEST = "/Game/Art/HeroSkelV4"
NAME = "SCB2Hero"
TARGET_HALF_EXTENT_Z = 66.0   # = the 132uu hero

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def import_skeletal(fbx, dest, name, scale, with_anim_skel=None):
    ui = unreal.FbxImportUI()
    if with_anim_skel is None:
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
        ui.skeleton = with_anim_skel
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
    if with_anim_skel is not None:
        for dup in (f"{dest}/{name}", f"{dest}/{name}_PhysicsAsset"):
            if eal.does_asset_exist(dup) and not isinstance(unreal.load_asset(dup), unreal.AnimSequence):
                eal.delete_asset(dup)
                print(f"PURGE_DUP: {dup}")


# ---- 1) probe: measure the native mesh at scale 1.0 ----
if eal.does_directory_exist(PROBE):
    eal.delete_directory(PROBE)
import_skeletal(MESH_FBX, PROBE, "ProbeMesh", 1.0)
probe = unreal.load_asset(f"{PROBE}/ProbeMesh")
if not isinstance(probe, unreal.SkeletalMesh):
    raise SystemExit("PROBE_FAILED")
z = probe.get_bounds().box_extent.z
scale = TARGET_HALF_EXTENT_Z / max(z, 0.001)
print(f"PROBE: native half-extent z={z:.1f} -> uniform scale {scale:.4f}")
eal.delete_directory(PROBE)

# ---- 2) the real import, self-consistent family at one scale ----
if eal.does_directory_exist(DEST):
    ok = eal.delete_directory(DEST)
    if not ok:
        raise SystemExit("V4_WIPE_FAILED (CDO lock?) — bump folder name")
import_skeletal(MESH_FBX, DEST, NAME, scale)
mesh = unreal.load_asset(f"{DEST}/{NAME}")
skeleton = unreal.load_asset(f"{DEST}/{NAME}_Skeleton")
if not isinstance(mesh, unreal.SkeletalMesh) or not isinstance(skeleton, unreal.Skeleton):
    raise SystemExit("V4_MESH_FAILED")
ext = mesh.get_bounds().box_extent
print(f"V4_MESH: extent z={ext.z:.1f} (target {TARGET_HALF_EXTENT_Z})")

bound = 0
for clip, rel in CLIPS.items():
    fbx = os.path.join(DROPS, rel)
    if not os.path.isfile(fbx):
        print(f"V4 {clip}: FBX_MISSING {fbx}")
        continue
    import_skeletal(fbx, DEST, f"A_Hero_{clip}", scale, with_anim_skel=skeleton)
    found = None
    for cand in (f"{DEST}/A_Hero_{clip}_Anim", f"{DEST}/A_Hero_{clip}"):
        a = unreal.load_asset(cand)
        if isinstance(a, unreal.AnimSequence):
            found = (cand, a)
            break
    if not found:
        print(f"V4 {clip}: NO_ANIMSEQUENCE")
        continue
    path, a = found
    s = a.get_editor_property("skeleton")
    is_bound = (s == skeleton)
    bound += int(is_bound)
    print(f"V4 {clip}: {path.split('/')[-1]} len={a.get_play_length():.2f}s "
          f"{'BOUND' if is_bound else 'ORPHANED'}")

eal.save_directory(DEST, recursive=True)
print(f"V4_{'SUCCESS' if bound == len(CLIPS) else 'PARTIAL'}: {bound}/{len(CLIPS)} bound, scale={scale:.4f}")
