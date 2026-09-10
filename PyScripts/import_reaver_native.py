"""THE EMBER REAVER enters the engine — mesh + 9 clips + material + scans.

V4 native pipeline into virgin /Game/Art/ReaverSkelV1. The remesh re-bakes
UVs, so the material forges from the rig's own embedded texture_0 (the
recolor PNGs on disk belong to the OLD topology). Emission never connects.
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

DROPS = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\reaver"
MESH_FBX = os.path.join(DROPS, "rig", "reaver_rig_rigged_character_fbx_url.fbx")
CLIPS = {
    "Idle": "anim_idle\\reaver_idle_animation_fbx_url.fbx",
    "Run": "anim_run\\reaver_run_animation_fbx_url.fbx",
    "Slash": "anim_slash\\reaver_slash_animation_fbx_url.fbx",
    "Dash": "anim_dash\\reaver_dash_animation_fbx_url.fbx",
    "Flurry": "anim_flurry\\reaver_flurry_animation_fbx_url.fbx",
    "Stagger": "anim_stagger\\reaver_stagger_animation_fbx_url.fbx",
    "HitReact": "anim_hitreact\\reaver_hitreact_animation_fbx_url.fbx",
    "Defeat": "anim_defeat\\reaver_defeat_animation_fbx_url.fbx",
    "Taunt": "anim_taunt\\reaver_taunt_animation_fbx_url.fbx",
}
PROBE = "/Game/_ProbeReaver"
DEST = "/Game/Art/ReaverSkelV1"
NAME = "SCB2Reaver"
TARGET_HALF_EXTENT_Z = 68.0   # 1.70 m duelist x the family 0.8 = 136 uu


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
            if EAL.does_asset_exist(dup) and not isinstance(unreal.load_asset(dup), unreal.AnimSequence):
                EAL.delete_asset(dup)
                print(f"PURGE_DUP: {dup}")


if EAL.does_directory_exist(PROBE):
    EAL.delete_directory(PROBE)
import_skeletal(MESH_FBX, PROBE, "ProbeMesh", 1.0)
probe = unreal.load_asset(f"{PROBE}/ProbeMesh")
z = probe.get_bounds().box_extent.z
scale = TARGET_HALF_EXTENT_Z / max(z, 0.001)
print(f"RVR_PROBE: native z={z:.1f} -> scale {scale:.4f}")
EAL.delete_directory(PROBE)

if EAL.does_directory_exist(DEST):
    ok = EAL.delete_directory(DEST)
    if not ok:
        raise SystemExit("RVR_WIPE_FAILED (CDO lock?) — bump folder version")
import_skeletal(MESH_FBX, DEST, NAME, scale)
mesh = unreal.load_asset(f"{DEST}/{NAME}")
skeleton = unreal.load_asset(f"{DEST}/{NAME}_Skeleton")
print(f"RVR_MESH: extent z={mesh.get_bounds().box_extent.z:.1f} (target {TARGET_HALF_EXTENT_Z})")

bound = 0
for clip, rel in CLIPS.items():
    import_skeletal(os.path.join(DROPS, rel), DEST, f"A_Reaver_{clip}", scale, skel=skeleton)
    a = unreal.load_asset(f"{DEST}/A_Reaver_{clip}_Anim")
    if isinstance(a, unreal.AnimSequence):
        ok = a.get_editor_property("skeleton") == skeleton
        bound += int(ok)
        print(f"RVR {clip}: len={a.get_play_length():.2f}s {'BOUND' if ok else 'ORPHANED'}")
    else:
        print(f"RVR {clip}: NO_ANIMSEQUENCE")

# ---- M_ReaverPBR from the rig's OWN base color (de-glow law: no emissive) ----
base_tex = unreal.load_asset(f"{DEST}/texture_0")
mat = tools.create_asset("M_ReaverPBR", DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("used_with_skeletal_mesh", True)
ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, -100)
ts.texture = base_tex
ok_base = MEL.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
rough = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 150)
rough.set_editor_property("r", 0.5)
ok_rough = MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
spec = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 300)
spec.set_editor_property("r", 0.4)
ok_spec = MEL.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
MEL.recompile_material(mat)
EAL.save_loaded_asset(mat)
print(f"RVR_MAT: base={ok_base} rough={ok_rough} spec={ok_spec}")

mats = mesh.get_editor_property("materials")
mesh.set_editor_property("materials", [
    unreal.SkeletalMaterial(material_interface=mat,
                            material_slot_name=m.get_editor_property("material_slot_name"))
    for m in mats])
EAL.save_loaded_asset(mesh)
print(f"RVR_MAT_ASSIGNED: {len(mats)} slot(s)")

# ---- impact scans for the three attack clips ----
opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW
for clip in ("Slash", "Dash", "Flurry"):
    a = unreal.load_asset(f"{DEST}/A_Reaver_{clip}_Anim")
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
    step = max(length / 32.0, 0.02)
    while t <= length:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, min(t, length - 0.001), opts)
        h = unreal.AnimPoseExtensions.get_bone_pose(pose, hips, unreal.AnimPoseSpaces.WORLD).translation
        row = [f"hipZ={h.z:6.1f}"]
        for hand in (lhand, rhand):
            if hand:
                p = unreal.AnimPoseExtensions.get_bone_pose(pose, hand, unreal.AnimPoseSpaces.WORLD).translation
                row.append(f"ext={((p.x - h.x) ** 2 + (p.y - h.y) ** 2) ** 0.5:5.1f}")
        print(f"RVRSCAN {clip}: frac={t/length:.3f}  {'  '.join(row)}")
        t += step

EAL.save_directory(DEST, recursive=True)
print(f"RVR_{'SUCCESS' if bound == len(CLIPS) else 'PARTIAL'}: {bound}/{len(CLIPS)} bound, scale={scale:.4f}")
