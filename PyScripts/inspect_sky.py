"""Read-only: report the saved NeonCity sky setup so we know the GROUND TRUTH (did the SkyLight
real_time_capture edit persist? is M_StarNebula is_sky? any SkyAtmosphere/Cloud left?)."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity")

for a in eas.get_all_level_actors():
    cls = a.get_class().get_name()
    if isinstance(a, unreal.SkyLight):
        c = a.get_component_by_class(unreal.SkyLightComponent)
        print(f"SKYLIGHT '{a.get_actor_label()}': real_time_capture="
              f"{c.get_editor_property('real_time_capture')} "
              f"source_type={c.get_editor_property('source_type')} "
              f"intensity={c.get_editor_property('intensity')}")
    elif isinstance(a, unreal.SkyAtmosphere):
        print(f"SKYATMOSPHERE present: '{a.get_actor_label()}'")
    elif "Cloud" in cls:
        print(f"CLOUD actor: '{a.get_actor_label()}' ({cls})")
    elif a.get_actor_label() == "StarDome":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        m = smc.get_material(0) if smc else None
        print(f"STARDOME mesh material[0]={m.get_name() if m else None}")

mat = EAL.load_asset("/Game/Art/CityMat/M_StarNebula")
print(f"M_StarNebula is_sky={mat.get_editor_property('is_sky') if mat else 'ASSET_MISSING'}")
print("INSPECT_SKY_DONE")
