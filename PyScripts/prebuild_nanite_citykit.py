"""Nanite detail pass — CityKit (Adam, 2026-07-21). THE SAFE WAY this time.

History: patch_citykit_nanite.py enabled Nanite on these ~1.3M-tri Meshy buildings but
the hierarchies then got built SYNCHRONOUSLY at the next -game boot, which hard-froze
the machine (see disable_nanite_citykit.py). The meshes have been rendering brute-force
ever since — full triangle cost every frame, detail wasted.

THIS script re-enables Nanite the correct way: headless in the EDITOR process, where
each mesh's Nanite hierarchy is built now and cached to the DerivedDataCache + saved
into the asset. Game launches afterwards just LOAD the prebuilt data — no boot build,
no freeze, and the city renders through Nanite's auto-LOD clusters: full detail up
close, cheap clusters at distance, LESS GPU time than brute force.

Run headless (expect 30-90 min, CPU-heavy — kick off when not playing):
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/prebuild_nanite_citykit.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import time

import unreal

EAL = unreal.EditorAssetLibrary

enabled_now = 0
already_on = 0
failed = 0
t0 = time.time()

assets = [ap for ap in EAL.list_assets("/Game/Art/CityKit", recursive=True) if "/SM_" in ap]
print(f"NANITE_PREBUILD: {len(assets)} candidate CityKit meshes")

for ap in assets:
    a = EAL.load_asset(ap)
    if not isinstance(a, unreal.StaticMesh):
        continue
    try:
        ns = a.get_editor_property("nanite_settings")
        if ns.get_editor_property("enabled"):
            already_on += 1
            continue
        t1 = time.time()
        ns.set_editor_property("enabled", True)
        a.set_editor_property("nanite_settings", ns)
        # save_loaded_asset triggers the Nanite build in-process and caches it to DDC
        EAL.save_loaded_asset(a)
        enabled_now += 1
        print(f"NANITE_BUILT {a.get_name()} in {time.time() - t1:.1f}s")
    except Exception as e:
        failed += 1
        unreal.log_warning(f"NANITE_PREBUILD_FAIL {a.get_name()}: {e}")

print(
    f"NANITE_PREBUILD_DONE: {enabled_now} built+saved, {already_on} already on, "
    f"{failed} failed, total {(time.time() - t0) / 60.0:.1f} min"
)
