"""Stage 28 import: Claude's kicks + three boss moves, four skeletons, one session.
Additive into LIVE folders (CDO-locked): NEW names only. Scans for windows.
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
ROOT = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops"

JOBS = [
    # (fbx, dest folder, skeleton asset, new name, scale)
    (ROOT + r"\anim_kick1\kick1_animation_fbx_url.fbx", "/Game/Art/HeroSkelV4", "SCB2Hero_Skeleton", "A_Hero_Kick1", 0.8),
    (ROOT + r"\anim_kick2\kick2_animation_fbx_url.fbx", "/Game/Art/HeroSkelV4", "SCB2Hero_Skeleton", "A_Hero_Kick2", 0.8),
    (ROOT + r"\anim_kickheavy\kickheavy_animation_fbx_url.fbx", "/Game/Art/HeroSkelV4", "SCB2Hero_Skeleton", "A_Hero_KickHeavy", 0.8),
    (ROOT + r"\kraken\anim_tidesweep\tidesweep_animation_fbx_url.fbx", "/Game/Art/KrakenSkelV1", "SCB2Kraken_Skeleton", "A_Kraken_TideSweep", 0.8),
    (ROOT + r"\reaver\anim_crescent\crescent_animation_fbx_url.fbx", "/Game/Art/ReaverSkelV1", "SCB2Reaver_Skeleton", "A_Reaver_Crescent", 0.8),
    (ROOT + r"\stalker\anim_spiral\spiral_animation_fbx_url.fbx", "/Game/Art/StalkerSkelV1", "SCB2Stalker_Skeleton", "A_Stalker_Spiral", 0.8),
]

opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW
bound = 0
for fbx, dest, skel_name, name, scale in JOBS:
    skel = unreal.load_asset(f"{dest}/{skel_name}")
    if not skel:
        print(f"S28 {name}: NO_SKELETON {dest}/{skel_name}")
        continue
    if not os.path.isfile(fbx):
        print(f"S28 {name}: FBX_MISSING {fbx}")
        continue
    if not EAL.does_asset_exist(f"{dest}/{name}_Anim"):
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
        t.replace_existing = False
        t.options = ui
        tools.import_asset_tasks([t])
    a = unreal.load_asset(f"{dest}/{name}_Anim")
    if not isinstance(a, unreal.AnimSequence):
        print(f"S28 {name}: NO_ANIMSEQUENCE")
        continue
    ok = a.get_editor_property("skeleton") == skel
    bound += int(ok)
    length = a.get_play_length()
    print(f"S28 {name}: len={length:.2f}s {'BOUND' if ok else 'ORPHANED'}")
    if not ok:
        continue
    pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
    names = unreal.AnimPoseExtensions.get_bone_names(pose0)
    hips = lfoot = rhand = None
    for n in names:
        sl = str(n).lower()
        if hips is None and ("hip" in sl or "pelvis" in sl):
            hips = n
        if lfoot is None and ("foot" in sl or "ankle" in sl):
            lfoot = n
        if rhand is None and "hand" in sl:
            rhand = n
    t = 0.0
    step = max(length / 24.0, 0.02)
    while t <= length:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, min(t, length - 0.001), opts)
        h = unreal.AnimPoseExtensions.get_bone_pose(pose, hips, unreal.AnimPoseSpaces.WORLD).translation
        row = [f"hipZ={h.z:6.1f}"]
        for b, tag in ((lfoot, "foot"), (rhand, "hand")):
            if b:
                p = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
                ext = ((p.x - h.x) ** 2 + (p.y - h.y) ** 2) ** 0.5
                row.append(f"{tag} z={p.z:6.1f} ext={ext:5.1f}")
        print(f"S28SCAN {name}: frac={t/length:.3f}  {'  '.join(row)}")
        t += step
    EAL.save_directory(dest, recursive=False)

print(f"S28_{'SUCCESS' if bound == len(JOBS) else 'PARTIAL'}: {bound}/{len(JOBS)} bound")
