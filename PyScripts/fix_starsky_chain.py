"""Real star sky in ONE editor session:
  1. build_city_materials.py — rebuilds CityMat incl. the new M_Star_* color materials + the
                               M_StarNebula MILKY WAY BAND (replaces the procedural pinpoint stars).
  2. build_starfield.py      — places ~523 real HYG stars (mag <= 4) as emissive spheres at real
                               directions, sized by magnitude + colored by B-V; pulls the dome closer;
                               saves NeonCity.
Map save needs a render device, so run WITH a real RHI (offscreen), NOT -nullrhi:
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/fix_starsky_chain.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import os
import runpy
import traceback

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
CHAIN = ["build_city_materials.py", "build_starfield.py"]

ok_all = True
for s in CHAIN:
    unreal.log(f"=== STARSKY_RUN: {s} ===")
    print(f"=== STARSKY_RUN: {s} ===", flush=True)
    try:
        runpy.run_path(os.path.join(HERE, s), run_name="__main__")
        print(f"=== STARSKY_OK: {s} ===", flush=True)
    except SystemExit as e:
        if e.code not in (0, None):
            print(f"=== STARSKY_STOP at {s} (exit {e.code}) ===", flush=True)
            ok_all = False
            break
    except Exception:
        print(f"=== STARSKY_FAIL: {s} ===", flush=True)
        traceback.print_exc()
        ok_all = False
        break

unreal.log("FIX_STARSKY_DONE: " + ("ALL_OK" if ok_all else "STOPPED_EARLY"))
print("FIX_STARSKY_DONE: " + ("ALL_OK" if ok_all else "STOPPED_EARLY"), flush=True)
