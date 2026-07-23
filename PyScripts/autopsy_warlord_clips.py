"""THE CLIP AUTOPSY (Adam, July 23: legs still dead after every code fix).
Skeleton binding checks passed — but the Animation Import Law warns clips can be
bound, sized, framed, and still never EVALUATE (the June frozen-hero disease).
Truth test: RAW AnimPose evaluation over time. A living walk moves leg bones by
tens of uu; a corpse clip holds every bone flat. Bramblehulk walk = the control.
"""
import unreal

opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW


def autopsy(path, label):
    a = unreal.load_asset(path)
    if not a:
        print(f"AUTOPSY {label}: MISSING")
        return
    length = a.get_play_length()
    pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
    names = unreal.AnimPoseExtensions.get_bone_names(pose0)
    picks = []
    for want in ("leg", "foot", "hip", "spine", "arm"):
        for n in names:
            if want in str(n).lower():
                picks.append(n)
                break
    if not picks:
        picks = list(names)[1:3]
    moved_total = 0.0
    for bone in picks:
        travel = 0.0
        prev = None
        t = 0.0
        while t <= length:
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, min(t, length - 0.001), opts)
            tr = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD)
            loc = tr.translation
            if prev is not None:
                travel += (loc - prev).length()
            prev = loc
            t += length / 6.0
        moved_total += travel
        print(f"AUTOPSY {label}: bone {bone} travel={travel:.1f}uu over {length:.2f}s")
    verdict = "ALIVE" if moved_total > 10.0 else "DEAD — never evaluates"
    print(f"AUTOPSY {label}: VERDICT {verdict} (total {moved_total:.1f}uu)")


autopsy("/Game/Art/WarlordSkelV1/A_Warlord_Walk_Anim", "Warlord.Walk")
autopsy("/Game/Art/WarlordSkelV1/A_Warlord_Swing_Anim", "Warlord.Swing")
autopsy("/Game/Art/WarlordSkelV1/A_Warlord_Idle_Anim", "Warlord.Idle")
autopsy("/Game/Art/BrambleSkelV1/A_Bramble_Walk_Anim", "CONTROL.BrambleWalk")
print("AUTOPSY_DONE")
