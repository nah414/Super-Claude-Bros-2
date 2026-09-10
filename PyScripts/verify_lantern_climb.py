"""Read-only structural check of /Game/Maps/LanternClimb. Confirms the climb is WALKABLE
(no ramp steeper than the walkable limit), the canyon has a solid floor (no void), and the
key actors (goal lantern, PlayerStart, shells, manager) are present. Uses only reliable
actor calls (label/location/rotation/scale) so its prints always land."""
import unreal
from collections import defaultdict

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/LanternClimb")

actors = eas.get_all_level_actors()
cat = defaultdict(int)
ramp_pitches = []
steep = []
zmin, zmax = 1e9, -1e9
floor_ok = goal_ok = start_ok = mgr_ok = False
lanterns = shells_walls = 0
flight_lands = []          # M2: switchback landings must NOT stack at one (X,Y)

for a in actors:
    lbl = a.get_actor_label()
    loc = a.get_actor_location()
    zmin = min(zmin, loc.z)
    zmax = max(zmax, loc.z)
    key = lbl.replace("LC_", "").split("_")[0]
    cat[key] += 1
    if lbl.startswith("LC_Land_"):
        flight_lands.append((round(loc.x), round(loc.y)))
    if lbl.startswith("LC_Ramp_") or lbl.startswith("LC_Spiral_") or "Gond" in lbl:
        p = a.get_actor_rotation().pitch
        ramp_pitches.append(round(p, 1))
        if abs(p) > 30.0:
            steep.append((lbl, round(p, 1)))
    if lbl == "LC_Floor":
        floor_ok = True
    if lbl == "LC_Lantern_FIRST":
        goal_ok = True
    if lbl == "LC_PlayerStart":
        start_ok = True
    if lbl == "LC_LightNetworkManager":
        mgr_ok = True
    if lbl.startswith("LC_Lantern_"):
        lanterns += 1

print("==================== LANTERN CLIMB HEALTH ====================")
print(f"TOTAL_ACTORS: {len(actors)}")
print(f"Z_RANGE: {round(zmin)} .. {round(zmax)}  (climb should reach ~8600)")
print(f"RAMPS: {len(ramp_pitches)}  pitch range: "
      f"{min(ramp_pitches) if ramp_pitches else 0} .. {max(ramp_pitches) if ramp_pitches else 0}")
print(f"STEEP_RAMPS (>30deg, not walkable): {steep}")
print(f"LANTERNS: {lanterns}")
print(f"FLOOR(no-void)={floor_ok}  GOAL_LANTERN={goal_ok}  PLAYERSTART={start_ok}  MANAGER={mgr_ok}")
# M2: assert no two switchback landings share an (X,Y) -> the staircase no longer stacks overhead.
stacked = []
for i in range(len(flight_lands)):
    for j in range(i + 1, len(flight_lands)):
        if abs(flight_lands[i][0] - flight_lands[j][0]) < 100 and \
           abs(flight_lands[i][1] - flight_lands[j][1]) < 100:
            stacked.append((flight_lands[i], flight_lands[j]))
print(f"SWITCHBACK_LANDINGS: {len(flight_lands)}  STACKED_OVERHEAD(bad): {stacked[:6]}")
print("CATEGORY CENSUS:")
for k in sorted(cat, key=lambda k: -cat[k]):
    print(f"   {cat[k]:4d}  {k}")
ok = floor_ok and goal_ok and start_ok and mgr_ok and not steep and zmax > 8000 and not stacked
print(f"VERIFY_CLIMB: {'PASS' if ok else 'FAIL'}")
print("VERIFY_CLIMB_DONE")
