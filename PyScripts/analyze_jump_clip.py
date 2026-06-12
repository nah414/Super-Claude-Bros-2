import unreal
ANIM = "/Game/Art/HeroSkelV4/A_Hero_Jump2_Anim"
a = unreal.load_asset(ANIM)
mesh = unreal.load_asset("/Game/Art/HeroSkelV4/SCB2Hero")
length = a.get_play_length()
print(f"JUMPSCAN: len={length:.2f}s")
# find a hips-ish bone
opts = unreal.AnimPoseEvaluationOptions()
opts.evaluation_type = unreal.AnimDataEvalType.RAW
pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
names = unreal.AnimPoseExtensions.get_bone_names(pose0)
hips = None
for n in names:
    s = str(n).lower()
    if "hip" in s or "pelvis" in s or "spine" in s:
        hips = n
        break
print(f"JUMPSCAN: tracking bone {hips} of {len(names)} bones")
t = 0.0
while t < length:
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, t, opts)
    tr = unreal.AnimPoseExtensions.get_bone_pose(pose, hips, unreal.AnimPoseSpaces.WORLD)
    print(f"JUMPSCAN: t={t:5.2f}  frac={t/length:.3f}  z={tr.translation.z:7.2f}")
    t += 0.25
print("JUMPSCAN_DONE")
