"""Enable Nanite on every CityKit static mesh — dense Meshy buildings get
auto-LOD rasterization AND cheap proxy meshes in the ray-tracing scene
(the fix for the on-screen 'ray tracing budget' warning)."""
import unreal

EAL = unreal.EditorAssetLibrary
count = 0
for path in EAL.list_assets("/Game/Art/CityKit", recursive=True):
    if "/SM_" not in path:
        continue
    sm = unreal.load_asset(path)
    if not isinstance(sm, unreal.StaticMesh):
        continue
    ns = sm.get_editor_property("nanite_settings")
    ns.set_editor_property("enabled", True)
    sm.set_editor_property("nanite_settings", ns)
    EAL.save_loaded_asset(sm)
    count += 1
print(f"NANITE_ON: {count} city meshes")
