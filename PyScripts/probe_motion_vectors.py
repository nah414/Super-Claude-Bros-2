"""MOTION-VECTOR AUDIT (July 23 research verdict): TSR ghosting on characters =
missing skinned velocity. Check every skeletal mesh's per-bone motion blur and
skin-cache usage; FORCE per-bone motion blur ON wherever it is off."""
import unreal

EAL = unreal.EditorAssetLibrary
fixed = 0
for path in EAL.list_assets("/Game/Art", recursive=True):
    asset = None
    if "SCB2" in path:
        asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.SkeletalMesh):
        continue
    name = asset.get_name()
    try:
        pbmb = asset.get_editor_property("per_bone_motion_blur")
    except Exception as e:
        print(f"MV_PROBE {name}: per_bone_motion_blur unreadable ({e})")
        continue
    try:
        cache = asset.get_editor_property("skin_cache_usage")
    except Exception:
        cache = "?"
    print(f"MV_PROBE {name}: per_bone_motion_blur={pbmb} skin_cache_usage={cache}")
    if not pbmb:
        asset.set_editor_property("per_bone_motion_blur", True)
        EAL.save_loaded_asset(asset)
        fixed += 1
        print(f"MV_FIXED {name}: per_bone_motion_blur -> True")
print(f"MV_DONE: {fixed} meshes fixed")
