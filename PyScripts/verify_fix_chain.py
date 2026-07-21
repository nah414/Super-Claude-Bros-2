"""Post-fix verification for the Roster Hall freeze repair — one headless session.
  1. verify_texture_caps.py  — every kit Texture2D capped (CityKit must now pass; was 4K)
  2. verify_roster_hall.py   — 15 stations + heroes present, no dupes (writes _prep/hall_verify_result.json)
Run: UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/verify_fix_chain.py
        -unattended -nosplash -nullrhi -nopause
verify_roster_hall.py raises SystemExit(1) on failure, so it runs LAST.
"""
import os
import runpy
import traceback

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
CHAIN = ["verify_texture_caps.py", "verify_roster_hall.py"]

for s in CHAIN:
    p = os.path.join(HERE, s)
    unreal.log(f"=== VERIFY_RUN: {s} ===")
    try:
        runpy.run_path(p, run_name="__main__")
        unreal.log(f"=== VERIFY_OK: {s} ===")
    except SystemExit as e:
        unreal.log(f"=== VERIFY_EXIT {s}: code={e.code} ===")
        if e.code not in (0, None):
            unreal.log(f"=== VERIFY_FAILED at {s} ===")
            break
    except Exception:
        unreal.log(f"=== VERIFY_FAIL: {s} ===")
        traceback.print_exc()
        break

unreal.log("VERIFY_FIX_CHAIN_DONE")
