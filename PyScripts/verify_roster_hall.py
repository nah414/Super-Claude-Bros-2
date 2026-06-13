"""Verify /Game/Maps/RosterHall on disk — READ-ONLY post-build checker.

Pairs with build_roster_hall.py: that script writes the Hall and prints a
MANIFEST line; this one re-opens the persisted map and proves the invariants
held *after* the save, independent of the build process that claimed success.

HARD RULE — this script is read-only. It NEVER spawns, deletes, edits, or saves.
It loads the level, counts what is there, compares against the source bank, and
prints a verdict. Run it as its own headless pass:

    UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/verify_roster_hall.py
        -unattended -nosplash -nullrhi

Output contract:
    VERIFY_PASS / VERIFY_FAIL: <reason>   (grep these from the headless log)
    VERIFY_MANIFEST: {json}               (machine-parseable summary)
On failure it also raises SystemExit(1) so an unattended run returns non-zero.
"""
import json
import unreal

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MAP_PATH = "/Game/Maps/RosterHall"
ROSTER_DIR = "/Game/Art/Roster"

failures = []


def fail(reason):
    failures.append(reason)
    print(f"VERIFY_FAIL: {reason}")


# ---- the map itself must exist on disk before we can verify anything ----
if not EAL.does_asset_exist(MAP_PATH):
    print(f"VERIFY_FAIL: MAP_MISSING: {MAP_PATH} does not exist")
    raise SystemExit(1)

# ---- expected cast: every StaticMesh under the source bank, by actor label ----
# load_asset is read-only; we never modify these. The build labels each roster
# actor with sm.get_name(), so the source names are exactly the labels to find.
expected_names = set()
for path in EAL.list_assets(ROSTER_DIR, recursive=True):
    if "/SM_" not in path:
        continue
    sm = EAL.load_asset(path)
    if isinstance(sm, unreal.StaticMesh):
        expected_names.add(sm.get_name())

if not expected_names:
    # Mirror the build's own loud guard: an empty bank means nothing to verify
    # against, which is itself a regression worth surfacing as a failure.
    fail(f"ROSTER_SOURCE_EMPTY: no StaticMesh under {ROSTER_DIR}")

# ---- open the persisted level (read-only navigation, no dirtying/saving) ----
assert les.load_level(MAP_PATH), f"LOAD_LEVEL_FAILED: {MAP_PATH}"
actors = eas.get_all_level_actors()
labels = set()
for a in actors:
    try:
        labels.add(a.get_actor_label())
    except Exception:
        pass

# ---- core invariants ----
# 1. Every source character must be standing in the Hall (no silent drops).
missing = sorted(expected_names - labels)
if missing:
    fail(f"ROSTER_INCOMPLETE: {len(missing)} missing, e.g. {missing[:5]}")

# 2. The room must be walkable & framed: a visitor start, a floor, a sun.
for required in ("PlayerStart", "HallFloor", "Sun"):
    if required not in labels:
        fail(f"STAGING_MISSING: {required}")

# ---- soft report (not failures): optional live actors & hero exhibits ----
roster_present = len(expected_names & labels)
heroes_present = sorted(l for l in labels if l.startswith("Exhibit_"))
live_present = sorted(l for l in labels if l.startswith("Live"))

manifest = {
    "map": MAP_PATH,
    "total_actors": len(actors),
    "roster_expected": len(expected_names),
    "roster_present": roster_present,
    "roster_missing": len(missing),
    "heroes_present": heroes_present,
    "live_present": live_present,
}
print("VERIFY_MANIFEST: " + json.dumps(manifest, sort_keys=True))

if failures:
    print(f"VERIFY_FAIL: {len(failures)} invariant(s) broken")
    raise SystemExit(1)
print(f"VERIFY_PASS: {roster_present}/{len(expected_names)} cast present, staging intact")
