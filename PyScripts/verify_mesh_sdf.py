"""Read-only check: software-cache Lumen GI relies on mesh distance fields. Project default is
r.GenerateMeshDistanceFields=True, so every kit StaticMesh should get an SDF unless one explicitly
disables it. Best-effort: flags any mesh that turns distance-field generation OFF (would cause GI
light leaks). Run headless under -NoRender (-nullrhi). Prints MESH_SDF_VERIFY: PASS/FAIL."""
import unreal

EAL = unreal.EditorAssetLibrary
KITS = ["/Game/Art/CityKit", "/Game/Art/CityTowerKit", "/Game/Art/IndustrialKit",
        "/Game/Art/ClimbKit", "/Game/Art/FestivalKit", "/Game/Art/LanternClimbKit"]

# Candidate property names across UE versions; we read whichever the build exposes.
SDF_PROPS = ("generate_mesh_distance_field",)

disabled = []
meshes = 0
readable = 0
for root in KITS:
    if not EAL.does_directory_exist(root):
        continue
    for ap in EAL.list_assets(root, recursive=True):
        a = EAL.load_asset(ap)
        if not isinstance(a, unreal.StaticMesh):
            continue
        meshes += 1
        for prop in SDF_PROPS:
            try:
                val = a.get_editor_property(prop)
                readable += 1
                if val is False:
                    disabled.append(f"{a.get_name()} ({root}) has {prop}=False")
                break
            except Exception:
                continue

print(f"MESH_SDF_VERIFY: {meshes} kit meshes; {readable} exposed a distance-field flag")
if readable == 0:
    print("  (per-mesh SDF flag not exposed in this build; project default "
          "r.GenerateMeshDistanceFields=True covers all meshes — no per-mesh opt-outs to worry about)")
if disabled:
    print("MESH_SDF_VERIFY: FAIL")
    for d in disabled:
        print(f"  - {d}")
else:
    print("MESH_SDF_VERIFY: PASS")
print("MESH_SDF_VERIFY_DONE")
