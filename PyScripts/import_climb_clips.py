"""Additive import of the CLIMB rig clips for BOTH heroes — surgical, no family wipe.

Adds four clips per hero against their EXISTING skeleton at the probed family scale:
  A_Hero_ClimbGrab/ClimbUp/ClimbDown/ClimbHang_Anim      (/Game/Art/HeroSkelV4)
  A_Heroine_ClimbGrab/ClimbUp/ClimbDown/ClimbHang_Anim   (/Game/Art/HeroineSkelV2)

THE 449 REUSE: ClimbUp's source is the ON-DISK flaggrab FBX (stage 36 ordered
449 Climb_Up_Rope for the flagpole) — same rig, byte-identical motion, imported
a second time under its honest name. Zero credits.

CLIMB SCAN (checklist 7.5-1): per clip prints hands-Z-relative-to-hips (the reach
cycle -> ClimbCycleReach), hips WORLD-Z drift (a rising root would drift-and-snap
under single-node playback), and for ClimbGrab the grip frac (-> window numbers).

Run (NOT -nullrhi — skeletal import needs the GPU path):
  powershell -File Scripts/run_pyscript.ps1 -Script ..\PyScripts\import_climb_clips.py
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

DROPS = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops"
PROBE = "/Game/_ProbeClimb"

FAMILIES = [
    {
        "who": "Hero",
        "mesh_fbx": os.path.join(DROPS, "white_rig", "white_rig_rigged_character_fbx_url.fbx"),
        "dest": "/Game/Art/HeroSkelV4",
        "skel": "/Game/Art/HeroSkelV4/SCB2Hero_Skeleton",
        "target_z": 66.0,
        "clips": {
            "ClimbGrab": os.path.join(DROPS, "anim_climbgrab", "hero_climbgrab_animation_fbx_url.fbx"),
            "ClimbUp":   os.path.join(DROPS, "anim_flaggrab", "hero_flaggrab_animation_fbx_url.fbx"),
            "ClimbDown": os.path.join(DROPS, "anim_climbdown", "hero_climbdown_animation_fbx_url.fbx"),
            "ClimbHang": os.path.join(DROPS, "anim_climbhang", "hero_climbhang_animation_fbx_url.fbx"),
        },
    },
    {
        "who": "Heroine",
        "mesh_fbx": os.path.join(DROPS, "heroine", "rig", "heroine_rig_rigged_character_fbx_url.fbx"),
        "dest": "/Game/Art/HeroineSkelV2",
        "skel": "/Game/Art/HeroineSkelV2/SCB2Heroine_Skeleton",
        "target_z": 64.0,
        "clips": {
            "ClimbGrab": os.path.join(DROPS, "heroine", "anim_climbgrab", "heroine_climbgrab_animation_fbx_url.fbx"),
            "ClimbUp":   os.path.join(DROPS, "heroine", "anim_flaggrab", "heroine_flaggrab_animation_fbx_url.fbx"),
            "ClimbDown": os.path.join(DROPS, "heroine", "anim_climbdown", "heroine_climbdown_animation_fbx_url.fbx"),
            "ClimbHang": os.path.join(DROPS, "heroine", "anim_climbhang", "heroine_climbhang_animation_fbx_url.fbx"),
        },
    },
]


def probe_scale(mesh_fbx, target_z):
    if eal.does_directory_exist(PROBE):
        eal.delete_directory(PROBE)
    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = True
    ui.import_animations = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    ui.skeletal_mesh_import_data.set_editor_property("import_uniform_scale", 1.0)
    ui.skeletal_mesh_import_data.set_editor_property("convert_scene", True)
    t = unreal.AssetImportTask()
    t.filename = mesh_fbx
    t.destination_path = PROBE
    t.destination_name = "ProbeMesh"
    t.automated = True
    t.save = False
    t.replace_existing = True
    t.options = ui
    tools.import_asset_tasks([t])
    probe = unreal.load_asset(f"{PROBE}/ProbeMesh")
    z = probe.get_bounds().box_extent.z
    eal.delete_directory(PROBE)
    return target_z / max(z, 0.001), z


def import_anim(fbx, dest, name, scale, skel):
    ui = unreal.FbxImportUI()
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
    t.replace_existing = True
    t.options = ui
    tools.import_asset_tasks([t])
    for dup in (f"{dest}/{name}", f"{dest}/{name}_PhysicsAsset"):
        if eal.does_asset_exist(dup) and not isinstance(unreal.load_asset(dup), unreal.AnimSequence):
            eal.delete_asset(dup)
            print(f"PURGE_DUP: {dup}")


opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW


def climb_scan(a, who, clip):
    """Hands-Z-vs-hips reach cycle + hips world-Z drift + first-grip frac."""
    length = a.get_play_length()
    pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
    names = unreal.AnimPoseExtensions.get_bone_names(pose0)
    hips, lhand, rhand = None, None, None
    for n in names:
        sl = str(n).lower()
        if hips is None and ("hip" in sl or "pelvis" in sl):
            hips = n
        if "hand" in sl:
            if "l" in sl.replace("hand", "") and lhand is None:
                lhand = n
            elif rhand is None:
                rhand = n
    if hips is None:
        print(f"CLIMB {who} {clip}: no hips bone — scan skipped")
        return
    reach_lo, reach_hi = 1e9, -1e9
    hipz_lo, hipz_hi = 1e9, -1e9
    grip_frac, grip_best = 0.0, -1e9
    t = 0.0
    step = max(length / 40.0, 0.02)
    while t <= length:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, min(t, length - 0.001), opts)
        h = unreal.AnimPoseExtensions.get_bone_pose(pose, hips, unreal.AnimPoseSpaces.WORLD).translation
        hipz_lo, hipz_hi = min(hipz_lo, h.z), max(hipz_hi, h.z)
        hz = -1e9
        for hand in (lhand, rhand):
            if hand is None:
                continue
            p = unreal.AnimPoseExtensions.get_bone_pose(pose, hand, unreal.AnimPoseSpaces.WORLD).translation
            hz = max(hz, p.z - h.z)
        if hz > -1e8:
            reach_lo, reach_hi = min(reach_lo, hz), max(reach_hi, hz)
            if hz > grip_best and t / length < 0.6:
                grip_best, grip_frac = hz, t / length
        t += step
    print(f"CLIMB {who} {clip}: len={length:.2f}s reach_span={reach_hi - reach_lo:.1f}uu "
          f"hipZ_drift={hipz_hi - hipz_lo:.1f}uu first_grip_frac={grip_frac:.3f}")
    if hipz_hi - hipz_lo > 40.0:
        print(f"CLIMB {who} {clip}: WARN root rises {hipz_hi - hipz_lo:.0f}uu — "
              f"drift-and-snap risk under single-node playback")


total_bound = 0
total_clips = 0
for fam in FAMILIES:
    who = fam["who"]
    skel = unreal.load_asset(fam["skel"])
    if not isinstance(skel, unreal.Skeleton):
        print(f"{who}: NO_SKELETON at {fam['skel']}")
        continue
    scale, native_z = probe_scale(fam["mesh_fbx"], fam["target_z"])
    print(f"{who}_PROBE: native z={native_z:.1f} -> scale {scale:.4f}")
    for clip, fbx in fam["clips"].items():
        total_clips += 1
        name = f"A_{who}_{clip}"
        if eal.does_asset_exist(f"{fam['dest']}/{name}_Anim"):
            print(f"{who} {clip}: exists — NEW-names law, skipped")
            total_bound += 1
            continue
        if not os.path.isfile(fbx):
            print(f"{who} {clip}: FBX_MISSING {fbx}")
            continue
        import_anim(fbx, fam["dest"], name, scale, skel)
        found = None
        for cand in (f"{fam['dest']}/{name}_Anim", f"{fam['dest']}/{name}"):
            a = unreal.load_asset(cand)
            if isinstance(a, unreal.AnimSequence):
                found = (cand, a)
                break
        if not found:
            print(f"{who} {clip}: NO_ANIMSEQUENCE")
            continue
        path, a = found
        is_bound = (a.get_editor_property("skeleton") == skel)
        total_bound += int(is_bound)
        print(f"{who} {clip}: {path.split('/')[-1]} len={a.get_play_length():.2f}s "
              f"{'BOUND' if is_bound else 'ORPHANED'}")
        if is_bound:
            climb_scan(a, who, clip)
    eal.save_directory(fam["dest"], recursive=True)

print(f"CLIMBCLIPS_{'SUCCESS' if total_bound == total_clips else 'PARTIAL'}: "
      f"{total_bound}/{total_clips} bound")
