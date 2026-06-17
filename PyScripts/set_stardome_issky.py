"""Flag M_StarNebula as an 'Is Sky' material so the real-time-capture SkyLight has a sky to
capture. F4 removed the SkyAtmosphere (to kill the blue) but left the SkyLight on real-time
capture -> "needs a SkyAtmosphere / VolumetricCloud / IsSky mesh" error + a re-capture loop.
The StarDome sphere already wears this material; making it Is Sky satisfies the capture and keeps
the starry-space look. Run with -RenderOffscreen (material change -> recompile; NOT -nullrhi)."""
import unreal

EAL = unreal.EditorAssetLibrary
mat = EAL.load_asset("/Game/Art/CityMat/M_StarNebula")
if not mat:
    print("STARDOME_MAT_MISSING: /Game/Art/CityMat/M_StarNebula")
else:
    set_ok = False
    for prop in ("is_sky", "b_is_sky"):
        try:
            mat.set_editor_property(prop, True)
            set_ok = prop
            break
        except Exception as e:
            unreal.log_warning(f"is_sky prop '{prop}' not settable: {e}")
    if set_ok:
        EAL.save_loaded_asset(mat)
        try:
            print(f"STARDOME_ISSKY_SET via '{set_ok}': is_sky={mat.get_editor_property('is_sky')}")
        except Exception:
            print(f"STARDOME_ISSKY_SET via '{set_ok}'")
    else:
        print("STARDOME_ISSKY_FAIL: no settable is_sky property found")
