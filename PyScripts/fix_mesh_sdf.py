"""Enable mesh distance-field generation on every kit StaticMesh. The legacy FBX import left
generate_mesh_distance_field=False on all 92 Meshy meshes, which starves software-cache Lumen GI
(the GI half of the hybrid) of the global distance field it traces against -> GI light leaks, and
the software-Lumen fallback can't work. SDFs are modest in memory and do NOT cause the Nanite-style
load freeze. The flag persists on save; the SDF itself builds from DDC on the next load/cook.
Run headless under -nullrhi (asset edit; the build is deferred to load/cook)."""
import unreal

EAL = unreal.EditorAssetLibrary
KITS = ["/Game/Art/CityKit", "/Game/Art/CityTowerKit", "/Game/Art/IndustrialKit",
        "/Game/Art/ClimbKit", "/Game/Art/FestivalKit", "/Game/Art/LanternClimbKit"]

n = 0
already = 0
for root in KITS:
    if not EAL.does_directory_exist(root):
        continue
    for ap in EAL.list_assets(root, recursive=True):
        a = EAL.load_asset(ap)
        if not isinstance(a, unreal.StaticMesh):
            continue
        try:
            if a.get_editor_property("generate_mesh_distance_field") is True:
                already += 1
                continue
            a.set_editor_property("generate_mesh_distance_field", True)
            EAL.save_loaded_asset(a)
            n += 1
        except Exception as e:
            unreal.log_warning(f"SDF_SET_SKIP {a.get_name()}: {e}")

print(f"MESH_SDF_FIX_DONE: enabled {n} meshes ({already} already on)")
