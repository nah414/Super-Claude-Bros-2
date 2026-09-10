"""Clean two things out of /Game/Maps/NeonCity (Adam):
  1. The AuroraRing actor — remove the aurora borealis from this stage.
  2. Any enemy spawned too close to the PlayerStart (the Glimmer that aggro'd the hero on spawn).
Operates on the already-built map (the source fix in dress_festival_streets.py stops it recurring).
Run with a render device (map save):
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/cleanup_neon_sky.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import math

import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

SAFE_RADIUS = 1000.0   # clear enemies within this of the spawn (catches the ~700uu behind-spawn camper)

assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_NEONCITY_FAILED"
actors = eas.get_all_level_actors()

# spawn location (PlayerStart); fallback to the known boulevard spawn
spawn = unreal.Vector(-4500.0, 0.0, 120.0)
for a in actors:
    try:
        if a.get_actor_label() == "PlayerStart" or isinstance(a, unreal.PlayerStart):
            spawn = a.get_actor_location()
            break
    except Exception:
        pass
print(f"SPAWN: ({spawn.x:.0f},{spawn.y:.0f},{spawn.z:.0f})")

aurora = 0
enemies = 0
for a in list(actors):
    try:
        label = a.get_actor_label()
    except Exception:
        continue
    if label == "AuroraRing":
        eas.destroy_actor(a)
        aurora += 1
        continue
    if label.startswith("Enemy_"):
        loc = a.get_actor_location()
        d = math.hypot(loc.x - spawn.x, loc.y - spawn.y)
        if d <= SAFE_RADIUS:
            eas.destroy_actor(a)
            enemies += 1
            print(f"REMOVED_SPAWN_ENEMY: {label} @ {d:.0f}uu from spawn")

print(f"CLEANUP: removed {aurora} aurora ring(s), {enemies} spawn-area enemy(ies)")
saved = les.save_current_level()
print(f"CLEANUP_SAVED: {saved}")
print("CLEANUP_DONE")
