"""THE RUST WARLORD enters the engine — mesh + 9 clips + material, one session.
V4 native pipeline into virgin /Game/Art/WarlordSkelV1. De-glow law applies
(the furnace's glow is VFX-driven, not a baked full-body emission).
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

DROPS = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\warlord"
MESH_FBX = os.path.join(DROPS, "rig", "warlord_rig_rigged_character_fbx_url.fbx")
CLIPS = {
    "Idle": "anim_idle\\warlord_idle_animation_fbx_url.fbx",
    "Walk": "anim_walk\\warlord_walk_animation_fbx_url.fbx",
    "Swing": "anim_swing\\warlord_swing_animation_fbx_url.fbx",
    "Chop": "anim_chop\\warlord_chop_animation_fbx_url.fbx",
    "Sweep": "anim_sweep\\warlord_sweep_animation_fbx_url.fbx",
    "Vent": "anim_vent\\warlord_vent_animation_fbx_url.fbx",
    "HitReact": "anim_hitreact\\warlord_hitreact_animation_fbx_url.fbx",
    "Stagger": "anim_stagger\\warlord_stagger_animation_fbx_url.fbx",
    "Defeat": "anim_defeat\\warlord_defeat_animation_fbx_url.fbx",
}
PROBE = "/Game/_ProbeWarlord"
DEST = "/Game/Art/WarlordSkelV1"
NAME = "SCB2Warlord"
TARGET_HALF_EXTENT_Z = 78.0   # 1.95 m rig x the family 0.8 = 1.56 m = 156 uu


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


if EAL.does_directory_exist(PROBE):
    EAL.delete_directory(PROBE)
import_skeletal(MESH_FBX, PROBE, "ProbeMesh", 1.0)
probe = unreal.load_asset(f"{PROBE}/ProbeMesh")
z = probe.get_bounds().box_extent.z
scale = TARGET_HALF_EXTENT_Z / max(z, 0.001)
print(f"WAR_PROBE: native z={z:.1f} -> scale {scale:.4f}")
EAL.delete_directory(PROBE)

if EAL.does_directory_exist(DEST):
    ok = EAL.delete_directory(DEST)
    if not ok:
        raise SystemExit("WAR_WIPE_FAILED (CDO lock?) — bump folder version")
import_skeletal(MESH_FBX, DEST, NAME, scale)
mesh = unreal.load_asset(f"{DEST}/{NAME}")
skeleton = unreal.load_asset(f"{DEST}/{NAME}_Skeleton")
print(f"WAR_MESH: extent z={mesh.get_bounds().box_extent.z:.1f} (target {TARGET_HALF_EXTENT_Z})")

bound = 0
for clip, rel in CLIPS.items():
    import_skeletal(os.path.join(DROPS, rel), DEST, f"A_Warlord_{clip}", scale, skel=skeleton)
    a = unreal.load_asset(f"{DEST}/A_Warlord_{clip}_Anim")
    if isinstance(a, unreal.AnimSequence):
        ok = a.get_editor_property("skeleton") == skeleton
        bound += int(ok)
        print(f"WAR {clip}: len={a.get_play_length():.2f}s {'BOUND' if ok else 'ORPHANED'}")
    else:
        print(f"WAR {clip}: NO_ANIMSEQUENCE")

base_tex = unreal.load_asset(f"{DEST}/texture_0")
mat = tools.create_asset("M_WarlordPBR", DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("used_with_skeletal_mesh", True)
ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, -100)
ts.texture = base_tex
ok_base = MEL.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
rough = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 150)
rough.set_editor_property("r", 0.5)
ok_rough = MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
metal = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 300)
metal.set_editor_property("r", 0.25)   # an armored sheen on the verdigris plate
ok_metal = MEL.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
MEL.recompile_material(mat)
EAL.save_loaded_asset(mat)
print(f"WAR_MAT: base={ok_base} rough={ok_rough} metal={ok_metal}")

mats = mesh.get_editor_property("materials")
mesh.set_editor_property("materials", [
    unreal.SkeletalMaterial(material_interface=mat,
                            material_slot_name=m.get_editor_property("material_slot_name"))
    for m in mats])
EAL.save_loaded_asset(mesh)
print(f"WAR_MAT_ASSIGNED: {len(mats)} slot(s)")

EAL.save_directory(DEST, recursive=True)
print(f"WAR_{'SUCCESS' if bound == len(CLIPS) else 'PARTIAL'}: {bound}/{len(CLIPS)} bound, scale={scale:.4f}")
