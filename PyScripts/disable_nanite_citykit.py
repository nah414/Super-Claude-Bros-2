"""Revert Nanite on the CityKit building meshes.

`patch_citykit_nanite.py` turned Nanite ON for every /Game/Art/CityKit SM_* mesh "for the
ray-tracing budget warning". That was both redundant and HARMFUL here:

  * REDUNDANT — build_roster_hall.py already pulls every static mesh off ray tracing
    (visible_in_ray_tracing=False), and ray tracing is OFF project-wide (software Lumen,
    r.RayTracing=False). So the meshes are not in any RT scene to budget.

  * HARMFUL — these are dense Meshy buildings (~1.3M tris each). On the next UNCOOKED
    `-game` launch the engine had to build the full Nanite hierarchy SYNCHRONOUSLY at boot
    (one mesh alone estimated ~9.5 GB), several in parallel, which overwhelmed the 8 GB
    laptop GPU and HARD-FROZE the whole machine while loading /Game/Maps/RosterHall.

Identical lesson to disable_nanite_festival.py — turn Nanite back OFF on the kit. The render
budget stays handled by visible_in_ray_tracing=False; texture VRAM is handled separately by
optimize_citykit_textures.py.
"""
import unreal

EAL = unreal.EditorAssetLibrary
n = 0
skipped = 0
for ap in EAL.list_assets("/Game/Art/CityKit", recursive=True):
    if "/SM_" not in ap:
        continue
    a = EAL.load_asset(ap)
    if not isinstance(a, unreal.StaticMesh):
        continue
    try:
        ns = a.get_editor_property("nanite_settings")
        if not ns.get_editor_property("enabled"):
            skipped += 1
            continue
        ns.set_editor_property("enabled", False)
        a.set_editor_property("nanite_settings", ns)
        EAL.save_loaded_asset(a)
        n += 1
    except Exception as e:
        unreal.log_warning(f"NANITE_OFF_SKIP {a.get_name()}: {e}")
print(f"CITYKIT_NANITE_DISABLED: {n} meshes turned off, {skipped} already off")
