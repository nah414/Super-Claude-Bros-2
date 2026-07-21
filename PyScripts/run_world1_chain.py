"""Run the full World-1 rebuild chain in ONE editor session (saves 4 editor boots).
Order: cap CityTowerKit textures -> build the neon street -> dress the festival -> merge the
canyon -> verify the combined world. Each step runs as __main__ (identical to -ExecutePythonScript).
Stops at the first hard failure and prints the traceback.
"""
import builtins
import os
import runpy
import traceback
import unreal

builtins._LC_SUPPRESS_AUTORUN = True        # so merge can import the canyon builder safely
HERE = os.path.dirname(os.path.abspath(__file__))

CHAIN = [
    "optimize_citytowerkit_textures.py",
    "build_neon_city.py",
    "dress_festival_streets.py",
    "merge_world1.py",
    "build_sky_props.py",          # the two moons + ring (build_neon_city wiped them on rebuild)
    "build_city_materials.py",     # rebuild star color mats + Milky Way band before placing stars
    "build_starfield.py",          # ~523 real HYG stars (mag<=4) + dome pulled closer (also wiped on rebuild)
    "verify_world1_combined.py",
]

for s in CHAIN:
    p = os.path.join(HERE, s)
    unreal.log(f"=== CHAIN_RUN: {s} ===")
    print(f"=== CHAIN_RUN: {s} ===", flush=True)
    try:
        runpy.run_path(p, run_name="__main__")
        print(f"=== CHAIN_OK: {s} ===", flush=True)
    except SystemExit as e:
        print(f"=== CHAIN_EXIT {s}: code={e.code} ===", flush=True)
        if e.code not in (0, None):
            print(f"=== CHAIN_STOP at {s} (nonzero exit) ===", flush=True)
            break
    except Exception:
        print(f"=== CHAIN_FAIL: {s} ===", flush=True)
        traceback.print_exc()
        break

print("WORLD1_CHAIN_DONE", flush=True)
