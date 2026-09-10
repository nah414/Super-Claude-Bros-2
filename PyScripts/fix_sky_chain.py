"""Neon District sky fix in ONE editor session:
  1. build_city_materials.py  — rebuilds all CityMat materials; picks up the reduced M_StarNebula
                                star count (threshold 0.985 -> 0.994). Materials are referenced by
                                path, so the StarDome auto-shows the thinner starfield.
  2. build_sky_props.py       — re-places the two moons + ring (build_neon_city wipes them on rebuild),
                                now in the WESTERN sky behind the spawn, and saves NeonCity.
Map save in step 2 needs a render device, so run this WITH a real RHI (offscreen), NOT -nullrhi:
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/fix_sky_chain.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import os
import runpy
import traceback

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
CHAIN = ["build_city_materials.py", "build_sky_props.py"]

ok_all = True
for s in CHAIN:
    p = os.path.join(HERE, s)
    unreal.log(f"=== SKY_CHAIN_RUN: {s} ===")
    print(f"=== SKY_CHAIN_RUN: {s} ===", flush=True)
    try:
        runpy.run_path(p, run_name="__main__")
        print(f"=== SKY_CHAIN_OK: {s} ===", flush=True)
    except SystemExit as e:
        if e.code not in (0, None):
            print(f"=== SKY_CHAIN_STOP at {s} (exit {e.code}) ===", flush=True)
            ok_all = False
            break
    except Exception:
        print(f"=== SKY_CHAIN_FAIL: {s} ===", flush=True)
        traceback.print_exc()
        ok_all = False
        break

unreal.log("FIX_SKY_CHAIN_DONE: " + ("ALL_OK" if ok_all else "STOPPED_EARLY"))
print("FIX_SKY_CHAIN_DONE: " + ("ALL_OK" if ok_all else "STOPPED_EARLY"), flush=True)
