import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/Maps/FeelGym")
names = ["Rock_Small","Rock_Medium","Rock_Large","Pine_Small","Pine_Tall",
         "Crystal_Small","Crystal_Tall","Column","Arch","GrassTuft","Monument","IslandChunk"]
x = 500
planted = []
for n in names:
    p = f"/Game/Art/Kit/{n}/StaticMeshes/{n}"
    m = unreal.EditorAssetLibrary.load_asset(p)
    if m:
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, -400, 0))
        a.set_actor_label(f"LINEUP_{n}")
        a.static_mesh_component.set_static_mesh(m)
        planted.append(n)
    x += 350
hero = unreal.EditorAssetLibrary.load_asset("/Game/Art/Hero/SparkHero/StaticMeshes/SparkHero")
if hero:
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(330, -180, 0))
    a.set_actor_label("LINEUP_SparkHero")
    a.static_mesh_component.set_static_mesh(hero)
    planted.append("SparkHero")
les.save_current_level()
print(f"LINEUP planted: {planted}")
