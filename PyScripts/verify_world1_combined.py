"""Read-only check of the COMBINED World 1 in /Game/Maps/NeonCity (festival street + the
appended Lantern Climb canyon). Asserts the merge is clean: one spawn, one goal at the canyon
crown, the old rooftop finale gone, the seam floor continuous, the west-cliff entry doorway
present, and the climb architecture placed."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity")
actors = eas.get_all_level_actors()

playerstarts = 0
goals = []
old_finale = []
fest = lc_ramps = climb_arch = 0
canyon_floor_top = None
gap = {"S": False, "N": False, "solid": False}
CLIMB_NAMES = ("fire_escape_run", "brick_ledge_stack", "pipe_rung_ladder", "tenement_balcony_climb",
               "scaffold_run", "vent_duct_ledges", "drainpipe_climb", "rebar_handholds",
               "window_sill_run", "cable_conduit_bundle")
OLD = ("GoalBeacon", "GoalShaft", "GoalGlow", "Ledge_", "ClimbWall_", "ClimbSign_",
       "Fest_Lantern_FIRST")

for a in actors:
    lbl = a.get_actor_label()
    loc = a.get_actor_location()
    if a.get_class().get_name() == "PlayerStart":
        playerstarts += 1
    if lbl == "LC_Lantern_FIRST":
        goals.append(round(loc.z))
    if any(lbl.startswith(p) for p in OLD):
        old_finale.append(lbl)
    if lbl.startswith("Fest_"):
        fest += 1
    if lbl.startswith("LC_Ramp_"):
        lc_ramps += 1
    if lbl == "LC_Floor":
        canyon_floor_top = round(loc.z + 150)        # 300-tall block centred -> top = z+150
    if lbl == "LC_CliffW_S":
        gap["S"] = True
    if lbl == "LC_CliffW_N":
        gap["N"] = True
    if lbl == "LC_CliffW":
        gap["solid"] = True
    if any(nm in lbl for nm in CLIMB_NAMES):
        climb_arch += 1

print("==================== WORLD 1 COMBINED ====================")
print(f"TOTAL_ACTORS: {len(actors)}")
print(f"PLAYERSTARTS: {playerstarts} (want 1)")
print(f"GOAL_LANTERNS z: {goals} (want exactly 1 at the crown ~8300)")
print(f"OLD_FINALE_SURVIVORS: {old_finale[:8]} (want none)")
print(f"FEST_ACTORS: {fest}   LC_RAMPS: {lc_ramps}   (both > 0 = one map holds both regions)")
print(f"CANYON_FLOOR_TOP_Z: {canyon_floor_top} (want ~0 = flush with the street)")
print(f"WEST_CLIFF_DOORWAY: S={gap['S']} N={gap['N']} solid={gap['solid']} (want S+N, not solid)")
print(f"CLIMB_ARCHITECTURE_PROPS: {climb_arch} (want >= 8)")
ok = (playerstarts == 1 and len(goals) == 1 and goals and goals[0] > 7500 and not old_finale
      and fest > 20 and lc_ramps > 10 and canyon_floor_top is not None and abs(canyon_floor_top) < 80
      and gap["S"] and gap["N"] and not gap["solid"] and climb_arch >= 8)
print(f"VERIFY_WORLD1: {'PASS' if ok else 'FAIL'}")
print("VERIFY_WORLD1_DONE")
