"""Revert Nanite on the Festival/Edge kit meshes.

Enabling Nanite on these small decorative Meshy props (~190uu, 30-80k tris) was a
mistake: it forced a full Nanite build + per-material recompile on the next -game
launch (the multi-minute black-screen "freeze"), and left the prop materials
without bUsedWithNanite=True -> "Default Material will be used in game" (gray props).

The actual ray-tracing budget fix is visible_in_ray_tracing=False on each placed
prop (done in the dressing pass), which removes them from the RT resident-geometry
budget WITHOUT Nanite. So Nanite was both redundant and harmful here -> turn it off.
"""
import unreal

EAL = unreal.EditorAssetLibrary
n = 0
for ap in EAL.list_assets("/Game/Art/FestivalKit", recursive=True):
    a = EAL.load_asset(ap)
    if isinstance(a, unreal.StaticMesh):
        try:
            ns = a.get_editor_property("nanite_settings")
            ns.set_editor_property("enabled", False)
            a.set_editor_property("nanite_settings", ns)
            EAL.save_loaded_asset(a)
            n += 1
        except Exception as e:
            unreal.log_warning(f"NANITE_OFF_SKIP {a.get_name()}: {e}")
print(f"NANITE_DISABLED: {n} meshes")
