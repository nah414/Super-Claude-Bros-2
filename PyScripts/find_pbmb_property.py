"""Where did bPerBoneMotionBlur live in 5.7? Dump candidate property names."""
import unreal

mesh = unreal.load_asset("/Game/Art/WarlordSkelV2/SCB2Warlord")
print(f"PBMB_CLASS: {type(mesh).__name__}")
for p in dir(mesh):
    lp = p.lower()
    if "motion" in lp or "blur" in lp or "velocity" in lp:
        print(f"PBMB_CANDIDATE(attr): {p}")

# Sweep every editor property name via the class
try:
    for prop in unreal.SkeletalMesh.static_class().get_editor_property("children") or []:
        pass
except Exception:
    pass
# Brute: try known spellings
for name in ("b_per_bone_motion_blur", "per_bone_motion_blur", "bPerBoneMotionBlur",
             "support_ray_tracing", "skin_cache_usage"):
    try:
        v = mesh.get_editor_property(name)
        print(f"PBMB_TRY {name} = {v}")
    except Exception:
        print(f"PBMB_TRY {name} = <absent>")

# Per-LOD info flags?
try:
    lods = mesh.get_editor_property("lod_info")
    for i, lod in enumerate(lods):
        for cand in dir(lod):
            if "motion" in cand.lower() or "blur" in cand.lower():
                print(f"PBMB_LOD{i}_CANDIDATE: {cand}")
except Exception as e:
    print(f"PBMB_LOD: {e}")
print("PBMB_DONE")
