"""Sky tweak round 3 in ONE editor session:
  1. import_celestial.py  — re-import + RE-TINT the moons (large light, small dark) + planet.
  2. build_aurora.py      — build M_Aurora + place the aurora ring (loads + saves the map).
  3. build_sky_props.py   — re-place the moons (depth-separated) + planet (loads + saves the map).
Each map step loads then saves, so they compose. Run with a render device (map save):
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/fix_sky_v3_chain.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import os
import runpy
import traceback

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
CHAIN = ["import_celestial.py", "build_aurora.py", "build_sky_props.py"]

ok_all = True
for s in CHAIN:
    unreal.log(f"=== SKY3_RUN: {s} ===")
    print(f"=== SKY3_RUN: {s} ===", flush=True)
    try:
        runpy.run_path(os.path.join(HERE, s), run_name="__main__")
        print(f"=== SKY3_OK: {s} ===", flush=True)
    except SystemExit as e:
        if e.code not in (0, None):
            print(f"=== SKY3_STOP at {s} (exit {e.code}) ===", flush=True)
            ok_all = False
            break
    except Exception:
        print(f"=== SKY3_FAIL: {s} ===", flush=True)
        traceback.print_exc()
        ok_all = False
        break

unreal.log("FIX_SKY3_DONE: " + ("ALL_OK" if ok_all else "STOPPED_EARLY"))
print("FIX_SKY3_DONE: " + ("ALL_OK" if ok_all else "STOPPED_EARLY"), flush=True)
