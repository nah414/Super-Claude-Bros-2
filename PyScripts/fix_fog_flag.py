"""Flip the volumetric-fog enable flag with the right property name + save."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_FAILED"
done = False
for a in eas.get_all_level_actors():
    try:
        fogc = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
    except Exception:
        fogc = None
    if not fogc:
        continue
    for name in ("enable_volumetric_fog", "b_enable_volumetric_fog", "volumetric_fog"):
        try:
            fogc.set_editor_property(name, True)
            unreal.log_warning(f"FOGFLAG set via '{name}' on {a.get_actor_label()}")
            done = True
            break
        except Exception:
            continue
    break
if not done:
    unreal.log_warning("FOGFLAG FAILED - no property name matched")
unreal.log_warning(f"FOGFLAG_SAVED={unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)}")
