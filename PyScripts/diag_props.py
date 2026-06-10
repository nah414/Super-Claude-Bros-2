import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
# 1. are the planted actors in the level?
found = [a.get_actor_label() for a in eas.get_all_level_actors() if a.get_actor_label().startswith("TEST_")]
print(f"DIAG planted actors present: {found}")
# 2. is Nanite enabled on the imported meshes?
for p in ("/Game/Art/Hero/SparkHero/StaticMeshes/SparkHero",
          "/Game/Art/Kit/Pine_Tall/StaticMeshes/Pine_Tall",
          "/Game/Art/Kit/IslandChunk/StaticMeshes/IslandChunk"):
    m = unreal.EditorAssetLibrary.load_asset(p)
    if m:
        try:
            ns = m.get_editor_property("nanite_settings")
            print(f"DIAG {p.split('/')[-1]} nanite_enabled={ns.get_editor_property('enabled')}")
        except Exception as e:
            print(f"DIAG {p.split('/')[-1]} nanite query failed: {e}")
