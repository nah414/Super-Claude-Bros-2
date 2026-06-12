"""Sonnet's kick combo: import 3 clips + scan each for the kick impact.

Additive import into the LIVE HeroineSkelV2 (no wipe, new names only:
A_Heroine_Kick1/2/3). Impact scan tracks FOOT height + extension — a kick's
money frame is the foot at peak height/reach.
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

DROPS = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\heroine"
DEST = "/Game/Art/HeroineSkelV2"
SCALE = 0.8
CLIPS = {
    "Kick1": "anim_kick1\\heroine_kick1_animation_fbx_url.fbx",   # 215 High_Kick
    "Kick2": "anim_kick2\\heroine_kick2_animation_fbx_url.fbx",   # 207 Roundhouse_Kick
    "Kick3": "anim_kick3\\heroine_kick3_animation_fbx_url.fbx",   # 216 Lunge_Spin_Kick
}

skeleton = unreal.load_asset(f"{DEST}/SCB2Heroine_Skeleton")
assert skeleton, "NO_SKELETON"

for clip, rel in CLIPS.items():
    fbx = os.path.join(DROPS, rel)
    assert os.path.isfile(fbx), f"FBX_MISSING {fbx}"
    if EAL.does_asset_exist(f"{DEST}/A_Heroine_{clip}_Anim"):
        print(f"KICK {clip}: already imported, skipping")
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
        print(f"KICK {clip}: NO_ANIMSEQUENCE")
        continue
    s = a.get_editor_property("skeleton")
    ok = (s == skeleton)
    bound += int(ok)
    length = a.get_play_length()
    print(f"KICK {clip}: len={length:.2f}s {'BOUND' if ok else 'ORPHANED'}")
    if not ok:
        continue
    pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
    names = unreal.AnimPoseExtensions.get_bone_names(pose0)
    hips, lfoot, rfoot = None, None, None
    for n in names:
        sl = str(n).lower()
        if hips is None and ("hip" in sl or "pelvis" in sl):
            hips = n
        if "foot" in sl or "ankle" in sl:
            if "l" in sl.replace("foot", "").replace("ankle", "") and lfoot is None:
                lfoot = n
            elif rfoot is None:
                rfoot = n
    print(f"KICK {clip}: bones hips={hips} l={lfoot} r={rfoot}")
    t = 0.0
    step = max(length / 40.0, 0.02)
    while t <= length:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, min(t, length - 0.001), opts)
        h = unreal.AnimPoseExtensions.get_bone_pose(pose, hips, unreal.AnimPoseSpaces.WORLD).translation
        out = []
        for foot in (lfoot, rfoot):
            if foot is None:
                out.append("z=  n/a ext=  n/a")
                continue
            p = unreal.AnimPoseExtensions.get_bone_pose(pose, foot, unreal.AnimPoseSpaces.WORLD).translation
            dx, dy = p.x - h.x, p.y - h.y
            out.append(f"z={p.z:6.1f} ext={(dx * dx + dy * dy) ** 0.5:5.1f}")
        print(f"KICK {clip}: frac={t/length:.3f}  L[{out[0]}]  R[{out[1]}]")
        t += step

print(f"KICK_{'SUCCESS' if bound == len(CLIPS) else 'PARTIAL'}: {bound}/{len(CLIPS)} bound")
EAL.save_directory(DEST, recursive=True)
print("KICK_DONE")
