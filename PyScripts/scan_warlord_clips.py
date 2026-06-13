"""Articulation scan (recipe 7.5) for the Rust Warlord's timed attacks.
Tracks the weapon-hand bone's world Z (height) and its horizontal reach from
the hips, so the real impact frame can be windowed out of the long routines.
"""
import unreal

DEST = "/Game/Art/WarlordSkelV1"
CLIPS = ["Swing", "Chop", "Sweep", "Vent"]

opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW


def pick_bone(names, prefer):
    # prefer a right-hand bone; fall back to any hand, then hips/spine
    for want in prefer:
        for n in names:
            if want in str(n).lower():
                return n
    return names[0] if names else None


for clip in CLIPS:
    a = unreal.load_asset(f"{DEST}/A_Warlord_{clip}_Anim")
    if not isinstance(a, unreal.AnimSequence):
        print(f"WSCAN {clip}: MISSING")
        continue
    length = a.get_play_length()
    pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
    names = unreal.AnimPoseExtensions.get_bone_names(pose0)
    hand = pick_bone(names, ["righthand", "hand_r", "r_hand", "hand", "wrist"])
    hips = pick_bone(names, ["hips", "pelvis", "spine"])
    print(f"WSCAN {clip}: len={length:.2f}s hand={hand} hips={hips}")
    t = 0.0
    step = max(length / 40.0, 0.05)   # ~40 samples across the clip
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
        print(f"WSCAN {clip}: frac={frac:.3f} t={t:5.2f} handZ={hz:7.2f} reach={reach:6.1f}")
        t += step
    print(f"WSCAN {clip}_PEAKS: handZ peak={peak_z:.1f} @frac {peak_z_frac:.3f} | "
          f"reach peak={peak_reach:.1f} @frac {peak_reach_frac:.3f}")
print("WSCAN_DONE")
