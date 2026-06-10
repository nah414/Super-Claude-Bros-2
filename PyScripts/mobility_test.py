import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
hero = unreal.EditorAssetLibrary.load_asset("/Game/Art/Hero/SparkHero/StaticMeshes/SparkHero")
for mob, pos, label in ((unreal.ComponentMobility.STATIC,  unreal.Vector(-3800, -250, 0), "MOBTEST_Static"),
                        (unreal.ComponentMobility.MOVABLE, unreal.Vector(-3800,  250, 0), "MOBTEST_Movable")):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, pos)
    a.set_actor_label(label)
    a.set_mobility(mob)
    ok = a.static_mesh_component.set_static_mesh(hero)
    print(f"MOBTEST planted {label} set_mesh={ok}")
les.save_current_level()
found = [x.get_actor_label() for x in eas.get_all_level_actors() if x.get_actor_label().startswith("MOBTEST")]
print(f"MOBTEST persisted: {found}")
