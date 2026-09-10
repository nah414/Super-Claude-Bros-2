"""Enable Nanite on the Festival/Edge kit meshes. The high-poly Meshy props blew the
ray-tracing 'always resident geometry' budget; Nanite gives them a compact streamed RT
representation (and fast LOD), which collapses that cost while keeping the detail."""
import unreal

EAL = unreal.EditorAssetLibrary
n = 0
for ap in EAL.list_assets("/Game/Art/FestivalKit", recursive=True):
    a = EAL.load_asset(ap)
    if isinstance(a, unreal.StaticMesh):
        try:
            ns = a.get_editor_property("nanite_settings")
            ns.set_editor_property("enabled", True)
            a.set_editor_property("nanite_settings", ns)
            EAL.save_loaded_asset(a)
            n += 1
        except Exception as e:
            unreal.log_warning(f"NANITE_SKIP {a.get_name()}: {e}")
print(f"NANITE_DONE: {n} meshes")
