"""Verify /Game/Maps/RosterHall on disk — READ-ONLY post-build checker.

Pairs with build_roster_hall.py (the dedup catalog + boss range). That script writes
the Hall; this one re-opens the persisted map and proves the invariants held AFTER the
save, independent of the build that claimed success.

HARD RULE — read-only. It NEVER spawns, deletes, edits, or saves. Run as its own pass:

    UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/verify_roster_hall.py
        -unattended -nosplash -nullrhi

Output contract:
    VERIFY_PASS / VERIFY_FAIL: <reason>   (grep these from the headless log)
    VERIFY_MANIFEST: {json}
On failure it raises SystemExit(1) so an unattended run returns non-zero.
"""
import json
import unreal

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MAP_PATH = "/Game/Maps/RosterHall"

# The 15 boss testing stations — KEEP IN SYNC with build_roster_hall.py STATIONS.
EXPECTED_STATIONS = [
    "LiveSleekKnight", "LiveHeroicTank", "LivePowerhouse", "LiveClassicSpark",
    "LiveRolyShellback", "LiveKrakenBoss", "LiveEmberReaver", "LiveVoidStalker",
    "LiveRustWarlord", "LiveShellbackAlpha", "LiveBramblehulk", "LiveHollowWarden",
    "LiveFoundryKing", "LiveLumenDragonlord", "LiveUnlight",
]

failures = []


def fail(reason):
    failures.append(reason)
    print(f"VERIFY_FAIL: {reason}")


if not EAL.does_asset_exist(MAP_PATH):
    print(f"VERIFY_FAIL: MAP_MISSING: {MAP_PATH} does not exist")
    raise SystemExit(1)

assert les.load_level(MAP_PATH), f"LOAD_LEVEL_FAILED: {MAP_PATH}"
actors = eas.get_all_level_actors()
labels = []
for a in actors:
    try:
        labels.append(a.get_actor_label())
    except Exception:
        pass
label_set = set(labels)

# ---- core invariants ----
# 1. Every boss station must be standing (no silent drops). This is the heart of the
#    Hall now: 15 live bosses, one each.
missing = [s for s in EXPECTED_STATIONS if s not in label_set]
if missing:
    fail(f"STATIONS_INCOMPLETE: {len(missing)} missing: {missing}")

# 2. The room must be walkable & framed.
for required in ("PlayerStart", "HallFloor", "Sun"):
    if required not in label_set:
        fail(f"STAGING_MISSING: {required}")

# 3. DEDUP LAW: one copy of each character. No label may appear twice (the old static
#    line-up + live-boss double is exactly what this guards against).
dupes = sorted({lbl for lbl in labels if labels.count(lbl) > 1})
# The City Kit may legitimately repeat a base name only if two assets share it; flag
# any duplicated CHARACTER/Live label loudly, but don't trip on unlabeled engine bits.
char_dupes = [d for d in dupes if d.startswith("Live") or d.startswith("Exhibit_")]
if char_dupes:
    fail(f"DUPLICATE_CHARACTERS: {char_dupes}")

# ---- soft report ----
stations_present = sorted(s for s in EXPECTED_STATIONS if s in label_set)
heroes_present = sorted(l for l in label_set if l.startswith("Exhibit_"))
noncombat = sorted(l for l in ("LiveLumenLamplighter", "LiveFlitMoth", "LiveGlimmer")
                   if l in label_set)

manifest = {
    "map": MAP_PATH,
    "total_actors": len(actors),
    "stations_expected": len(EXPECTED_STATIONS),
    "stations_present": len(stations_present),
    "stations_missing": missing,
    "heroes_present": heroes_present,
    "noncombat_present": noncombat,
    "duplicate_characters": char_dupes,
}
print("VERIFY_MANIFEST: " + json.dumps(manifest, sort_keys=True))

# Headless print() does not reliably reach the redirected log under -run=pythonscript,
# so also drop the verdict to a file the caller can read. (Still read-only w.r.t. the
# game's content — this writes only to the OS temp dir.)
try:
    verdict = {"pass": not failures, "failures": failures, **manifest}
    with open(r"C:\Users\Atomn\mario2\_prep\hall_verify_result.json", "w") as f:
        json.dump(verdict, f, indent=2)
except Exception as e:
    print(f"VERIFY_WRITE_SKIPPED: {e}")

if failures:
    print(f"VERIFY_FAIL: {len(failures)} invariant(s) broken")
    raise SystemExit(1)
print(f"VERIFY_PASS: {len(stations_present)}/{len(EXPECTED_STATIONS)} stations present, "
      f"{len(heroes_present)} heroes, no character dupes, staging intact")
