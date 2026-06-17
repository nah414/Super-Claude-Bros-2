"""Turn OFF the NeonCity SkyLight's real-time capture. The star sky is static, so per-frame
re-capture is pure cost (~3 GB of cubemap render targets -> 6.4 GB peak on the 8 GB card) and it
was also the thing demanding a SkyAtmosphere/IsSky sky. With the IsSky StarDome present, a one-time
CapturedScene grab gives the dim star ambient; real-time off drops VRAM back to ~3.2 GB and removes
the 'needs a sky' error/loop. Run with -RenderOffscreen (loads + saves the heavy map; 8 GB-safe)."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_FAILED"

n = 0
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        if comp:
            comp.set_editor_property("real_time_capture", False)
            n += 1
            print(f"SKYLIGHT_RT_OFF: {a.get_actor_label()}")

saved = les.save_current_level()
print(f"SKYLIGHT_REALTIME_OFF_DONE: {n} skylights, saved={saved}")
