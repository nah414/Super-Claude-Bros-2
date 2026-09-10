"""Remove the World-1 rain: destroy the spawned ARainCurtain (the "Rain" actor) from NeonCity + save.
Idempotent — safe to re-run (no Rain actor -> removed=0). Run -RenderOffscreen (map save needs render).
(Adam, June 19: "eliminate the rain all together". The ARainCurtain class + M_RainStreak material stay
in the project, dormant; we just unspawn it. The rain AMBIENCE is removed separately in
SparkHeroGameMode -> amb_night_loop. build_neon_city.py no longer spawns rain, so a full chain rebuild
also stays rain-free; this script just clears the actor from the already-saved map.)"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_NEONCITY_FAILED"

removed = 0
for a in list(eas.get_all_level_actors()):
    if a.get_class().get_name() == "RainCurtain" or a.get_actor_label() == "Rain":
        eas.destroy_actor(a)
        removed += 1

# census any survivors (should be 0)
left = sum(1 for a in eas.get_all_level_actors()
          if a.get_class().get_name() == "RainCurtain" or a.get_actor_label() == "Rain")
print(f"RAIN_STRIPPED: {removed} remaining={left}")
saved = les.save_current_level()
print(f"RAIN_STRIP_SAVED: {saved}")
print("RAIN_STRIP_DONE")
