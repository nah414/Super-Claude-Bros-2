"""Articulation scan (recipe 7.5) for ALL boss attack clips — the Phase-1 refinement
pass. Tracks the right-hand bone's world Z + horizontal reach so the real impact frame
can be windowed out of each clip (sets ClipStart/ClipRate so the hit lands as the active
window opens). Writes results to a FILE (UE headless print() doesn't reach stdout).
"""
import unreal

BOSSES = {
    "Kraken":  ("KrakenSkelV1",  ["Swing", "Charge", "Slam", "Grip", "TideSweep"]),
    "Reaver":  ("ReaverSkelV1",  ["Slash", "Crescent", "Flurry", "Dash"]),
    "Stalker": ("StalkerSkelV1", ["Strike", "Cut", "Spiral", "Lunge", "Combo"]),
    "Warlord": ("WarlordSkelV1", ["Swing", "Chop", "Sweep", "Vent"]),
    "Warden":  ("WardenSkelV1",  ["Slash", "Judgment", "Voidcast", "Charged"]),
    "Dragon":  ("DragonSkelV1",  ["WingShove", "WingSweep", "Sanctuary", "FirstFlame"]),
    "Bramble": ("BrambleSkelV1", ["Slam", "Quake", "Sweep", "Shove"]),
}

OUT_FILE = r"C:\Users\Atomn\mario2\_prep\boss_scan_results.txt"
_results = []

opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW


def pick_bone(names, prefer):
    for want in prefer:
        for n in names:
            if want in str(n).lower():
                return n
    return names[0] if names else None


for boss, (folder, clips) in BOSSES.items():
    dest = f"/Game/Art/{folder}"
    for clip in clips:
        a = unreal.load_asset(f"{dest}/A_{boss}_{clip}_Anim")
        if not isinstance(a, unreal.AnimSequence):
            _results.append(f"{boss}/{clip} MISSING")
            continue
        length = a.get_play_length()
        pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
        names = unreal.AnimPoseExtensions.get_bone_names(pose0)
        hand = pick_bone(names, ["righthand", "hand_r", "r_hand", "hand", "wrist"])
        hips = pick_bone(names, ["hips", "pelvis", "spine"])
        t, step = 0.0, max(length / 48.0, 0.04)
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
        _results.append(f"{boss}/{clip} len={length:.3f} handZ_frac={peak_z_frac:.3f} "
                        f"reach_frac={peak_reach_frac:.3f} (handZ={peak_z:.1f} reach={peak_reach:.1f})")

with open(OUT_FILE, "w") as f:
    f.write("\n".join(_results) + "\n")
print(f"BOSS_SCAN_DONE -> {OUT_FILE}")
