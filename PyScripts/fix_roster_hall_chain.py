"""Roster Hall freeze fix — run the whole repair in ONE headless editor session.

Order:
  1. disable_nanite_citykit.py   — turn Nanite OFF on the CityKit buildings (root cause of the
                                    synchronous boot-time build that hard-froze the PC)
  2. optimize_citykit_textures.py — cap CityKit textures to 2K/1K (kills the Final 4K encode at
                                    boot; trims peak VRAM on the 8 GB GPU)
  3. warm_roster_hall_ddc.py     — load the Hall and force-build all mesh/texture derived data so
                                    the next `-game` launch performs NO synchronous build at boot

Steps 1-2 edit + save assets; step 3 only loads. All are CPU-side — run this headless under
-nullrhi (no GPU), so it cannot repeat the GPU freeze:
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/fix_roster_hall_chain.py
      -unattended -nosplash -nullrhi -nopause
"""
import os
import runpy
import traceback

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
CHAIN = [
    "disable_nanite_citykit.py",
    "optimize_citykit_textures.py",
    "warm_roster_hall_ddc.py",
]

ok_all = True
for s in CHAIN:
    p = os.path.join(HERE, s)
    unreal.log(f"=== FIX_CHAIN_RUN: {s} ===")
    print(f"=== FIX_CHAIN_RUN: {s} ===", flush=True)
    try:
        runpy.run_path(p, run_name="__main__")
        print(f"=== FIX_CHAIN_OK: {s} ===", flush=True)
    except SystemExit as e:
        if e.code not in (0, None):
            print(f"=== FIX_CHAIN_STOP at {s} (exit {e.code}) ===", flush=True)
            ok_all = False
            break
    except Exception:
        print(f"=== FIX_CHAIN_FAIL: {s} ===", flush=True)
        traceback.print_exc()
        ok_all = False
        break

print("FIX_ROSTER_HALL_CHAIN_DONE: " + ("ALL_OK" if ok_all else "STOPPED_EARLY"), flush=True)
