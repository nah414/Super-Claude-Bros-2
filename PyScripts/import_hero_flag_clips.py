"""Additive import of the FLAG-CAPTURE clips for BOTH heroes — surgical, no family wipe.

Adds two clips per hero against their EXISTING skeleton at the family scale:
  A_Hero_FlagGrab_Anim     A_Hero_FlagVictory_Anim      (/Game/Art/HeroSkelV4)
  A_Heroine_FlagGrab_Anim  A_Heroine_FlagVictory_Anim   (/Game/Art/HeroineSkelV2)

Scale is re-probed from each native mesh FBX (the proven 0.8 family rule, measured not
guessed) so the new clip matches the mesh exactly. The mesh + existing clips are left
untouched. Legacy FBX importer (Interchange off), per the Animation Import Law.

Run (NOT -nullrhi — skeletal import needs the GPU path):
  powershell -File Scripts/run_pyscript.ps1 -Script ..\PyScripts\import_hero_flag_clips.py
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

DROPS = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops"
PROBE = "/Game/_ProbeFlag"

FAMILIES = [
    {
        "who": "Hero",
        "mesh_fbx": os.path.join(DROPS, "white_rig", "white_rig_rigged_character_fbx_url.fbx"),
        "dest": "/Game/Art/HeroSkelV4",
        "skel": "/Game/Art/HeroSkelV4/SCB2Hero_Skeleton",
        "target_z": 66.0,
        "clips": {
            "FlagGrab":    os.path.join(DROPS, "anim_flaggrab", "hero_flaggrab_animation_fbx_url.fbx"),
            "FlagVictory": os.path.join(DROPS, "anim_flagvictory", "hero_flagvictory_animation_fbx_url.fbx"),
        },
    },
    {
        "who": "Heroine",
        "mesh_fbx": os.path.join(DROPS, "heroine", "rig", "heroine_rig_rigged_character_fbx_url.fbx"),
        "dest": "/Game/Art/HeroineSkelV2",
        "skel": "/Game/Art/HeroineSkelV2/SCB2Heroine_Skeleton",
        "target_z": 64.0,
        "clips": {
            "FlagGrab":    os.path.join(DROPS, "heroine", "anim_flaggrab", "heroine_flaggrab_animation_fbx_url.fbx"),
            "FlagVictory": os.path.join(DROPS, "heroine", "anim_flagvictory", "heroine_flagvictory_animation_fbx_url.fbx"),
        },
    },
]


def probe_scale(mesh_fbx, target_z):
    """Measure the native mesh half-extent at scale 1.0 -> the family uniform scale."""
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
    # FBXIT_ANIMATION also spawns a junk SkeletalMesh + PhysicsAsset; purge so only *_Anim survives.
    for dup in (f"{dest}/{name}", f"{dest}/{name}_PhysicsAsset"):
        if eal.does_asset_exist(dup) and not isinstance(unreal.load_asset(dup), unreal.AnimSequence):
            eal.delete_asset(dup)
            print(f"PURGE_DUP: {dup}")


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
        if not os.path.isfile(fbx):
            print(f"{who} {clip}: FBX_MISSING {fbx}")
            continue
        name = f"A_{who}_{clip}"
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
    eal.save_directory(fam["dest"], recursive=True)

print(f"FLAGCLIPS_{'SUCCESS' if total_bound == total_clips else 'PARTIAL'}: {total_bound}/{total_clips} bound")
