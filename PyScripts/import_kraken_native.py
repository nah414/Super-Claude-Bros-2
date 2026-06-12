"""THE IRON KRAKEN enters the engine — mesh + 10 clips + PBR + scans, one session.

V4 native pipeline into the virgin /Game/Art/KrakenSkelV1. His gen shipped
SEPARATE PBR maps, so M_KrakenPBR is forged from real textures — and the
emission map simply never gets plugged in (the Brightness War stays won).
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

DROPS = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\kraken"
MESH_FBX = os.path.join(DROPS, "rig", "kraken_rig_rigged_character_fbx_url.fbx")
CLIPS = {
    "Idle": "anim_idle\\kraken_idle_animation_fbx_url.fbx",
    "Walk": "anim_walk\\kraken_walk_animation_fbx_url.fbx",
    "Charge": "anim_charge\\kraken_charge_animation_fbx_url.fbx",
    "Swing": "anim_swing\\kraken_swing_animation_fbx_url.fbx",
    "Slam": "anim_slam\\kraken_slam_animation_fbx_url.fbx",
    "Grip": "anim_grip\\kraken_grip_animation_fbx_url.fbx",
    "Stagger": "anim_stagger\\kraken_stagger_animation_fbx_url.fbx",
    "HitReact": "anim_hitreact\\kraken_hitreact_animation_fbx_url.fbx",
    "Defeat": "anim_defeat\\kraken_defeat_animation_fbx_url.fbx",
    "Taunt": "anim_taunt\\kraken_taunt_animation_fbx_url.fbx",
}
TEXTURES = {  # name -> (file, srgb)   — emission deliberately ABSENT
    "T_Kraken_BaseColor": ("gen\\kraken_gen_tex0_base_color.png", True),
    "T_Kraken_Normal": ("gen\\kraken_gen_tex0_normal.png", False),
    "T_Kraken_Roughness": ("gen\\kraken_gen_tex0_roughness.png", False),
    "T_Kraken_Metallic": ("gen\\kraken_gen_tex0_metallic.png", False),
}
PROBE = "/Game/_ProbeKraken"
DEST = "/Game/Art/KrakenSkelV1"
NAME = "SCB2Kraken"
TARGET_HALF_EXTENT_Z = 70.0   # 1.75 m Champion x the family 0.8 = 140 uu


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


# ---- probe -> scale -> mesh + clips ----
if EAL.does_directory_exist(PROBE):
    EAL.delete_directory(PROBE)
import_skeletal(MESH_FBX, PROBE, "ProbeMesh", 1.0)
probe = unreal.load_asset(f"{PROBE}/ProbeMesh")
z = probe.get_bounds().box_extent.z
scale = TARGET_HALF_EXTENT_Z / max(z, 0.001)
print(f"KRK_PROBE: native z={z:.1f} -> scale {scale:.4f}")
EAL.delete_directory(PROBE)

if EAL.does_directory_exist(DEST):
    ok = EAL.delete_directory(DEST)
    if not ok:
        raise SystemExit("KRK_WIPE_FAILED (CDO lock?) — bump folder version")
import_skeletal(MESH_FBX, DEST, NAME, scale)
mesh = unreal.load_asset(f"{DEST}/{NAME}")
skeleton = unreal.load_asset(f"{DEST}/{NAME}_Skeleton")
print(f"KRK_MESH: extent z={mesh.get_bounds().box_extent.z:.1f} (target {TARGET_HALF_EXTENT_Z})")

bound = 0
for clip, rel in CLIPS.items():
    import_skeletal(os.path.join(DROPS, rel), DEST, f"A_Kraken_{clip}", scale, skel=skeleton)
    a = unreal.load_asset(f"{DEST}/A_Kraken_{clip}_Anim")
    if isinstance(a, unreal.AnimSequence):
        ok = a.get_editor_property("skeleton") == skeleton
        bound += int(ok)
        print(f"KRK {clip}: len={a.get_play_length():.2f}s {'BOUND' if ok else 'ORPHANED'}")
    else:
        print(f"KRK {clip}: NO_ANIMSEQUENCE")

# ---- textures + M_KrakenPBR (real maps; emission never connected) ----
for tex_name, (rel, srgb) in TEXTURES.items():
    t = unreal.AssetImportTask()
    t.filename = os.path.join(DROPS, rel)
    t.destination_path = DEST
    t.destination_name = tex_name
    t.automated = True
    t.save = True
    t.replace_existing = True
    tools.import_asset_tasks([t])
    tex = unreal.load_asset(f"{DEST}/{tex_name}")
    if tex:
        tex.set_editor_property("srgb", srgb)
        if "Normal" in tex_name:
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        EAL.save_loaded_asset(tex)
        print(f"KRK_TEX: {tex_name} ok srgb={srgb}")

mat = tools.create_asset("M_KrakenPBR", DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("used_with_skeletal_mesh", True)
wires = []
for i, (tex_name, prop, pin) in enumerate([
        ("T_Kraken_BaseColor", unreal.MaterialProperty.MP_BASE_COLOR, "RGB"),
        ("T_Kraken_Normal", unreal.MaterialProperty.MP_NORMAL, "RGB"),
        ("T_Kraken_Roughness", unreal.MaterialProperty.MP_ROUGHNESS, "R"),
        ("T_Kraken_Metallic", unreal.MaterialProperty.MP_METALLIC, "R")]):
    tex = unreal.load_asset(f"{DEST}/{tex_name}")
    if not tex:
        continue
    ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, -200 + i * 220)
    ts.texture = tex
    if "Normal" in tex_name:
        ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    elif not tex.get_editor_property("srgb"):
        ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    wires.append(f"{tex_name}={MEL.connect_material_property(ts, pin, prop)}")
MEL.recompile_material(mat)
EAL.save_loaded_asset(mat)
print(f"KRK_MAT: {' '.join(wires)}")

mats = mesh.get_editor_property("materials")
mesh.set_editor_property("materials", [
    unreal.SkeletalMaterial(material_interface=mat,
                            material_slot_name=m.get_editor_property("material_slot_name"))
    for m in mats])
EAL.save_loaded_asset(mesh)
print(f"KRK_MAT_ASSIGNED: {len(mats)} slot(s)")

# ---- impact scans: swing/grip = hand extension, slam = hips-Z arc ----
opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW
for clip in ("Swing", "Slam", "Grip"):
    a = unreal.load_asset(f"{DEST}/A_Kraken_{clip}_Anim")
    if not isinstance(a, unreal.AnimSequence):
        continue
    length = a.get_play_length()
    pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
    names = unreal.AnimPoseExtensions.get_bone_names(pose0)
    hips = lhand = rhand = None
    for n in names:
        sl = str(n).lower()
        if hips is None and ("hip" in sl or "pelvis" in sl):
            hips = n
        if "hand" in sl:
            if "l" in sl.replace("hand", "") and lhand is None:
                lhand = n
            elif rhand is None:
                rhand = n
    t = 0.0
    step = max(length / 36.0, 0.02)
    while t <= length:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, min(t, length - 0.001), opts)
        h = unreal.AnimPoseExtensions.get_bone_pose(pose, hips, unreal.AnimPoseSpaces.WORLD).translation
        row = [f"hipZ={h.z:6.1f}"]
        for hand in (lhand, rhand):
            if hand:
                p = unreal.AnimPoseExtensions.get_bone_pose(pose, hand, unreal.AnimPoseSpaces.WORLD).translation
                row.append(f"ext={((p.x - h.x) ** 2 + (p.y - h.y) ** 2) ** 0.5:5.1f}/z={p.z:5.1f}")
        print(f"KRKSCAN {clip}: frac={t/length:.3f}  {'  '.join(row)}")
        t += step

EAL.save_directory(DEST, recursive=True)
print(f"KRK_{'SUCCESS' if bound == len(CLIPS) else 'PARTIAL'}: {bound}/{len(CLIPS)} bound, scale={scale:.4f}")
