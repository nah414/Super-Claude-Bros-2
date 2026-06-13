"""Articulation scan (recipe 7.5) for the four guardians' attack clips. Tracks the
right-hand bone's world Z + horizontal reach so the real impact frame can be windowed
out of each clip (sets AGuardianFighter move ClipStart/ClipRate). Prints PEAKS lines.
"""
import unreal

GUARDIANS = {
    "SleekKnight":  ["Slash1", "Slash2", "Spin", "Dodge"],
    "HeroicTank":   ["Swing", "Push", "Charge", "Block"],
    "Powerhouse":   ["Jab", "Hook", "BothFists", "Combo"],
    "ClassicSpark": ["Jab", "Uppercut", "Counter", "Combo"],
}

# UE headless print() does not reliably reach stdout — also write to a file we can read.
OUT_FILE = r"C:\Users\Atomn\mario2\_prep\guardian_scan_results.txt"
_results = []

opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW


def pick_bone(names, prefer):
    for want in prefer:
        for n in names:
            if want in str(n).lower():
                return n
    return names[0] if names else None


for camel, clips in GUARDIANS.items():
    dest = f"/Game/Art/{camel}SkelV1"
    for clip in clips:
        a = unreal.load_asset(f"{dest}/A_{camel}_{clip}_Anim")
        if not isinstance(a, unreal.AnimSequence):
            print(f"GSCAN {camel}/{clip}: MISSING")
            continue
        length = a.get_play_length()
        pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
        names = unreal.AnimPoseExtensions.get_bone_names(pose0)
        hand = pick_bone(names, ["righthand", "hand_r", "r_hand", "hand", "wrist"])
        hips = pick_bone(names, ["hips", "pelvis", "spine"])
        t, step = 0.0, max(length / 40.0, 0.05)
        peak_z, peak_reach, peak_z_frac, peak_reach_frac = -1e9, -1e9, 0, 0
        while t <= length:
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, t, opts)
            h = unreal.AnimPoseExtensions.get_bone_pose(pose, hand, unreal.AnimPoseSpaces.WORLD)
            p = unreal.AnimPoseExtensions.get_bone_pose(pose, hips, unreal.AnimPoseSpaces.WORLD)
            reach = ((h.translation.x - p.translation.x) ** 2 + (h.translation.y - p.translation.y) ** 2) ** 0.5
            frac = t / length if length > 0 else 0
            if h.translation.z > peak_z:
                peak_z, peak_z_frac = h.translation.z, frac
            if reach > peak_reach:
                peak_reach, peak_reach_frac = reach, frac
            t += step
        line = (f"{camel}/{clip} len={length:.3f} handZ_frac={peak_z_frac:.3f} "
                f"reach_frac={peak_reach_frac:.3f} (handZ={peak_z:.1f} reach={peak_reach:.1f})")
        print("GSCAN " + line)
        _results.append(line)

with open(OUT_FILE, "w") as f:
    f.write("\n".join(_results) + "\n")
print(f"GSCAN_DONE -> {OUT_FILE}")
