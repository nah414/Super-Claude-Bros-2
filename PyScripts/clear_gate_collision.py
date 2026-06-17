"""F2 (Adam): "Our oriental festival gates are like walls... characters should be able to walk
THROUGH these gates, not around them."

Root cause: dress_festival_streets.fprop() already sets the gate COMPONENT to NO_COLLISION, but
the festival-gate StaticMesh ASSETS carry baked simple collision. After a level save / cook the
component flag can revert to the mesh's default (BlockAll using simple collision) and the gate
becomes a wall. The robust fix is to strip the simple collision from the gate MESH ASSETS once,
so there is no collision geometry left to block — passable no matter what the component does.

Run headless (NO -nullrhi needed; this is an asset edit, not a material/character build):
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/clear_gate_collision.py
    -unattended -nosplash
Idempotent: re-running on an already-cleared mesh is a no-op.
"""
import unreal

EAL = unreal.EditorAssetLibrary
SMES = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

# Decorative festival gates you walk THROUGH. (Scan-friendly: any FestivalKit mesh whose name
# contains one of these gets its simple collision stripped.)
GATE_KEYS = ("torii", "arch", "gate")
KIT_ROOT = "/Game/Art/FestivalKit"

# Resolve the concrete gate mesh paths.
gate_paths = []
for name in EAL.list_assets(KIT_ROOT, recursive=True, include_folder=False):
    low = name.lower()
    if low.endswith("_c"):          # skip blueprint/redirector class entries
        continue
    if any(k in low for k in GATE_KEYS) and "/sm_" in low:
        gate_paths.append(name.split(".")[0])

# Always include the two known gates explicitly in case the scan misses naming, plus the seam
# rubble piles (F3): they're decorative pass-through props too — the spawned-component
# NO_COLLISION flag doesn't survive the level save, so strip their mesh collision instead.
for explicit in (f"{KIT_ROOT}/neon_torii/SM_neon_torii",
                 f"{KIT_ROOT}/festival_arch/SM_festival_arch",
                 "/Game/Art/CityTowerKit/rubble_pile/SM_rubble_pile",
                 "/Game/Art/CityTowerKit/debris_chunks/SM_debris_chunks"):
    if explicit not in gate_paths and EAL.does_asset_exist(explicit):
        gate_paths.append(explicit)

unreal.log(f"GATE_TARGETS: {gate_paths}")

cleared = 0
for path in gate_paths:
    sm = EAL.load_asset(path)
    if not sm:
        unreal.log_warning(f"GATE_MISSING: {path}")
        continue
    try:
        before = SMES.get_simple_collision_count(sm)
    except Exception:
        before = -1
    # Strip simple collision primitives, then make the (now-empty) simple collision authoritative
    # for queries so the mesh never falls back to per-poly complex blocking.
    SMES.remove_collisions(sm)
    bs = sm.get_editor_property("body_setup")
    if bs:
        bs.set_editor_property("collision_trace_flag",
                               unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    try:
        after = SMES.get_simple_collision_count(sm)
    except Exception:
        after = -1
    EAL.save_asset(path)
    cleared += 1
    unreal.log(f"GATE_CLEARED: {path} simple_collision {before}->{after}")

unreal.log(f"CLEAR_GATE_COLLISION_DONE: cleared={cleared}/{len(gate_paths)}")
print(f"CLEAR_GATE_COLLISION_DONE: cleared={cleared}/{len(gate_paths)}")
