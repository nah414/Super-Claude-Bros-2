"""Read-only audit: every kit Texture2D must be capped (color/normal <= 2048, others <= 1024,
and NEVER 0 = uncapped/source-size). Catches kits that silently re-imported back to 4K.
Run headless under -NoRender (-nullrhi). Prints TEX_CAP_VERIFY: PASS/FAIL + offenders."""
import unreal

EAL = unreal.EditorAssetLibrary
KITS = ["/Game/Art/CityKit", "/Game/Art/CityTowerKit", "/Game/Art/IndustrialKit",
        "/Game/Art/ClimbKit", "/Game/Art/FestivalKit", "/Game/Art/LanternClimbKit"]

offenders = []
checked = 0
for root in KITS:
    if not EAL.does_directory_exist(root):
        print(f"  (skip missing kit {root})")
        continue
    for ap in EAL.list_assets(root, recursive=True):
        a = EAL.load_asset(ap)
        if not isinstance(a, unreal.Texture2D):
            continue
        checked += 1
        nm = a.get_name().lower()
        cap = 2048 if ("color" in nm or "normal" in nm or "albedo" in nm or "basecolor" in nm) else 1024
        mx = a.get_editor_property("max_texture_size")
        if mx == 0 or mx > cap:
            offenders.append(f"{a.get_name()} max_texture_size={mx} (cap {cap}) in {root}")

print(f"TEX_CAP_VERIFY: checked {checked} textures across {len(KITS)} kits")
if offenders:
    print("TEX_CAP_VERIFY: FAIL")
    for o in offenders[:80]:
        print(f"  - {o}")
    print(f"  ...({len(offenders)} total offenders)")
else:
    print("TEX_CAP_VERIFY: PASS")
print("TEX_CAP_VERIFY_DONE")
