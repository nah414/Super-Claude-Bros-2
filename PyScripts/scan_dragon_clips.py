"""Articulation scan (recipe 7.5) for the Lumen Dragonlord's action clips."""
import unreal

DEST = "/Game/Art/DragonSkelV1"
CLIPS = ["WingShove", "WingSweep", "Sanctuary", "FirstFlame"]

opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW


def pick_bone(names, prefer):
    for want in prefer:
        for n in names:
            if want in str(n).lower():
                return n
    return names[0] if names else None


for clip in CLIPS:
    a = unreal.load_asset(f"{DEST}/A_Dragon_{clip}_Anim")
    if not isinstance(a, unreal.AnimSequence):
        print(f"DRSCAN {clip}: MISSING")
        continue
    length = a.get_play_length()
    pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
    names = unreal.AnimPoseExtensions.get_bone_names(pose0)
    hand = pick_bone(names, ["righthand", "hand_r", "r_hand", "hand", "wrist"])
    hips = pick_bone(names, ["hips", "pelvis", "spine"])
    print(f"DRSCAN {clip}: len={length:.2f}s hand={hand} hips={hips}")
    t = 0.0
    step = max(length / 40.0, 0.05)
    peak_z, peak_reach, peak_z_frac, peak_reach_frac = -1e9, -1e9, 0, 0
    while t <= length:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, t, opts)
        h = unreal.AnimPoseExtensions.get_bone_pose(pose, hand, unreal.AnimPoseSpaces.WORLD)
        p = unreal.AnimPoseExtensions.get_bone_pose(pose, hips, unreal.AnimPoseSpaces.WORLD)
        hz = h.translation.z
        reach = ((h.translation.x - p.translation.x) ** 2 + (h.translation.y - p.translation.y) ** 2) ** 0.5
        frac = t / length if length > 0 else 0
        if hz > peak_z:
            peak_z, peak_z_frac = hz, frac
        if reach > peak_reach:
            peak_reach, peak_reach_frac = reach, frac
        t += step
    print(f"DRSCAN {clip}_PEAKS: handZ peak={peak_z:.1f} @frac {peak_z_frac:.3f} | "
          f"reach peak={peak_reach:.1f} @frac {peak_reach_frac:.3f}")
print("DRSCAN_DONE")
