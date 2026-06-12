"""Sonnet's signature combo: import 3 clips + scan each for the punch impact.

Additive import into the LIVE HeroineSkelV2 folder (no wipe — the heroine CDO
locks it; existing _Anim assets are NEVER touched). New names only:
A_Heroine_Combo1/2/3. Then an AnimPose hand-travel scan finds where the punch
actually lands in each routine so C++ can window the clip to the strike.
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

DROPS = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\heroine"
DEST = "/Game/Art/HeroineSkelV2"
SCALE = 0.8   # her locked family factor
CLIPS = {
    "Combo1": "anim_combo1\\heroine_combo1_animation_fbx_url.fbx",   # 193 Left_Hook
    "Combo2": "anim_combo2\\heroine_combo2_animation_fbx_url.fbx",   # 195 Right_Upper_Hook
    "Combo3": "anim_combo3\\heroine_combo3_animation_fbx_url.fbx",   # 214 Both_Fists
}

skeleton = unreal.load_asset(f"{DEST}/SCB2Heroine_Skeleton")
assert skeleton, "NO_SKELETON"

for clip, rel in CLIPS.items():
    fbx = os.path.join(DROPS, rel)
    assert os.path.isfile(fbx), f"FBX_MISSING {fbx}"
    if EAL.does_asset_exist(f"{DEST}/A_Heroine_{clip}_Anim"):
        print(f"COMBO {clip}: already imported, skipping")
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
    t.filename = fbx
    t.destination_path = DEST
    t.destination_name = f"A_Heroine_{clip}"
    t.automated = True
    t.save = True
    t.replace_existing = False
    t.options = ui
    tools.import_asset_tasks([t])

opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW
bound = 0
for clip in CLIPS:
    a = unreal.load_asset(f"{DEST}/A_Heroine_{clip}_Anim")
    if not isinstance(a, unreal.AnimSequence):
        print(f"COMBO {clip}: NO_ANIMSEQUENCE")
        continue
    s = a.get_editor_property("skeleton")
    ok = (s == skeleton)
    bound += int(ok)
    length = a.get_play_length()
    print(f"COMBO {clip}: len={length:.2f}s {'BOUND' if ok else 'ORPHANED'}")
    if not ok:
        continue
    # hand-travel scan: distance of each hand from the hips in the hips' XY
    # plane — the punch impact is the global max of forward extension.
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
    print(f"COMBO {clip}: bones hips={hips} l={lhand} r={rhand}")
    t = 0.0
    step = max(length / 40.0, 0.02)
    while t <= length:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, min(t, length - 0.001), opts)
        h = unreal.AnimPoseExtensions.get_bone_pose(pose, hips, unreal.AnimPoseSpaces.WORLD).translation
        ext = []
        for hand in (lhand, rhand):
            if hand is None:
                ext.append(0.0)
                continue
            p = unreal.AnimPoseExtensions.get_bone_pose(pose, hand, unreal.AnimPoseSpaces.WORLD).translation
            dx, dy = p.x - h.x, p.y - h.y
            ext.append((dx * dx + dy * dy) ** 0.5)
        print(f"COMBO {clip}: frac={t/length:.3f}  L={ext[0]:6.1f}  R={ext[1]:6.1f}")
        t += step

print(f"COMBO_{'SUCCESS' if bound == len(CLIPS) else 'PARTIAL'}: {bound}/{len(CLIPS)} bound")
EAL.save_directory(DEST, recursive=True)
print("COMBO_DONE")
