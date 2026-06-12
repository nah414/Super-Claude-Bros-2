"""Bramblehulk round 2: additive import of sweep + shove + impact scans.
LIVE folder (CDO-locked): NEW names only, never touch existing _Anim assets.
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DROPS = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\bramble"
DEST = "/Game/Art/BrambleSkelV1"
SCALE = 0.8
CLIPS = {"Sweep": "anim_sweep\\bramble_sweep_animation_fbx_url.fbx",
         "Shove": "anim_shove\\bramble_shove_animation_fbx_url.fbx"}

skeleton = unreal.load_asset(f"{DEST}/SCB2Bramble_Skeleton")
assert skeleton, "NO_SKELETON"
for clip, rel in CLIPS.items():
    if EAL.does_asset_exist(f"{DEST}/A_Bramble_{clip}_Anim"):
        print(f"BR2 {clip}: exists, skipping")
        continue
    ui = unreal.FbxImportUI()
    ui.import_mesh = False
    ui.import_as_skeletal = False
    ui.import_animations = True
    ui.import_materials = False
    ui.import_textures = False
    ui.skeleton = skeleton
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    ui.anim_sequence_import_data.set_editor_property("import_uniform_scale", SCALE)
    ui.anim_sequence_import_data.set_editor_property("snap_to_closest_frame_boundary", True)
    ui.anim_sequence_import_data.set_editor_property("convert_scene", True)
    t = unreal.AssetImportTask()
    t.filename = os.path.join(DROPS, rel)
    t.destination_path = DEST
    t.destination_name = f"A_Bramble_{clip}"
    t.automated = True
    t.save = True
    t.replace_existing = False
    t.options = ui
    tools.import_asset_tasks([t])

opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW
bound = 0
for clip in CLIPS:
    a = unreal.load_asset(f"{DEST}/A_Bramble_{clip}_Anim")
    if not isinstance(a, unreal.AnimSequence):
        print(f"BR2 {clip}: NO_ANIMSEQUENCE")
        continue
    ok = a.get_editor_property("skeleton") == skeleton
    bound += int(ok)
    length = a.get_play_length()
    print(f"BR2 {clip}: len={length:.2f}s {'BOUND' if ok else 'ORPHANED'}")
    pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
    names = unreal.AnimPoseExtensions.get_bone_names(pose0)
    hips = lhand = lfoot = None
    for n in names:
        sl = str(n).lower()
        if hips is None and ("hip" in sl or "pelvis" in sl):
            hips = n
        if lhand is None and "hand" in sl:
            lhand = n
        if lfoot is None and ("foot" in sl or "ankle" in sl):
            lfoot = n
    t = 0.0
    step = max(length / 28.0, 0.02)
    while t <= length:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, min(t, length - 0.001), opts)
        h = unreal.AnimPoseExtensions.get_bone_pose(pose, hips, unreal.AnimPoseSpaces.WORLD).translation
        row = [f"hipZ={h.z:6.1f}"]
        for b, tag in ((lhand, "hand"), (lfoot, "foot")):
            if b:
                p = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
                ext = ((p.x - h.x) ** 2 + (p.y - h.y) ** 2) ** 0.5
                row.append(f"{tag} ext={ext:5.1f} z={p.z:6.1f}")
        print(f"BR2SCAN {clip}: frac={t/length:.3f}  {'  '.join(row)}")
        t += step

EAL.save_directory(DEST, recursive=True)
print(f"BR2_{'SUCCESS' if bound == len(CLIPS) else 'PARTIAL'}: {bound}/{len(CLIPS)} bound")
