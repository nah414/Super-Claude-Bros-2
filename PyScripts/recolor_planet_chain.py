"""One-session: recolor the ringed planet rust-red, then render the look-back sky shots to
verify it. Saves an editor boot.
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/recolor_planet_chain.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import os
import runpy
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
for s in ("recolor_ringed_planet.py", "capture_neon_lookback.py"):
    print(f"=== RECOLOR_RUN: {s} ===", flush=True)
    try:
        runpy.run_path(os.path.join(HERE, s), run_name="__main__")
        print(f"=== RECOLOR_OK: {s} ===", flush=True)
    except Exception:
        print(f"=== RECOLOR_FAIL: {s} ===", flush=True)
        traceback.print_exc()
        break
print("RECOLOR_CHAIN_DONE", flush=True)
