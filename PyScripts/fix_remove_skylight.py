"""Remove the SkyLight (+ any SkyAtmosphere/VolumetricCloud) from NeonCity. An SLS_CAPTURED_SCENE
SkyLight with no SkyAtmosphere shows the on-screen "We need a SkyAtmosphere / VolumetricCloud /
IsSky mesh ... or the problem will return" warning and keeps re-validating/relighting (the
first-seconds 'loop'). real_time_capture=False + an IsSky dome does NOT silence it — the IsSky path
only satisfies REAL-TIME capture, not the static captured-scene capture. The SkyLight was intensity
0.015 (negligible — moon directional + ~55 lights + neon + Lumen GI carry the scene), so deleting it
is the clean fix. The IsSky StarDome stays as the visible starry sky. Run with -RenderOffscreen
(loads + saves the heavy map). Deletion persists reliably (unlike component-property edits)."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_FAILED"

removed = []
for a in list(eas.get_all_level_actors()):
    cls = a.get_class().get_name()
    if isinstance(a, (unreal.SkyLight, unreal.SkyAtmosphere)) or "Cloud" in cls:
        removed.append(f"{a.get_actor_label()} ({cls})")
        eas.destroy_actor(a)

saved = les.save_current_level()
print(f"SKY_ACTORS_REMOVED: {removed} saved={saved}")
