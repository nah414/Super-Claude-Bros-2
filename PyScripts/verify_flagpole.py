# ============================================================================
# verify_flagpole.py -- READ-ONLY check that the capture flagpole is in place.
# ----------------------------------------------------------------------------
# Loads /Game/Maps/LanternClimb (the standalone World-1 test level) and confirms
# an AFlagpoleGoal actor exists at the crown, beside the goal lantern. Read-only:
# it loads + inspects, never saves. Safe under -nullrhi (-NoRender).
#
#   powershell -File Scripts/run_pyscript.ps1 -Script ..\PyScripts\verify_flagpole.py -NoRender
#
# Exit/print: prints VERIFY_PASS or VERIFY_FAIL with the actor details.
# ============================================================================

import unreal

MAP = "/Game/Maps/LanternClimb"
CROWN_Z = 8650.0
EXPECT_Z = CROWN_Z - 90.0    # the flagpole base sits flush with the final landing (standalone: no offset)

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(m):
    print("[verify_flagpole] {}".format(m))
    try:
        unreal.log("[verify_flagpole] {}".format(m))
    except Exception:
        pass


def main():
    log("loading {}".format(MAP))
    les.load_level(MAP)
    actors = eas.get_all_level_actors()

    flags = [a for a in actors if a.get_class().get_name() == "FlagpoleGoal"]
    goal_lanterns = [a for a in actors
                     if a.get_class().get_name() == "Lantern"
                     and "FIRST" in a.get_actor_label()]

    log("found {} FlagpoleGoal actor(s), {} goal lantern(s)".format(len(flags), len(goal_lanterns)))

    ok = False
    for a in flags:
        loc = a.get_actor_location()
        ph = None
        for nm in ("pole_height", "PoleHeight"):
            try:
                ph = a.get_editor_property(nm)
                break
            except Exception:
                continue
        log("  {} @ ({:.0f},{:.0f},{:.0f})  PoleHeight={}".format(
            a.get_actor_label(), loc.x, loc.y, loc.z, ph))
        if abs(loc.x) < 50 and abs(loc.y) < 50 and abs(loc.z - EXPECT_Z) < 120:
            ok = True

    for a in goal_lanterns:
        loc = a.get_actor_location()
        log("  goal lantern {} @ ({:.0f},{:.0f},{:.0f})".format(a.get_actor_label(), loc.x, loc.y, loc.z))

    if flags and ok:
        log("VERIFY_PASS -- flagpole present at the crown")
    elif flags:
        log("VERIFY_FAIL -- flagpole exists but not at the expected crown position")
    else:
        log("VERIFY_FAIL -- no FlagpoleGoal actor found in the level")


if __name__ == "__main__":
    main()
