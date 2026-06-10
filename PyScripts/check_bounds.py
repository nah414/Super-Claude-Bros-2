import unreal
for p in ("/Game/Art/Hero/SparkHero/StaticMeshes/SparkHero",
          "/Game/Art/Kit/Pine_Tall/StaticMeshes/Pine_Tall",
          "/Game/Art/Kit/IslandChunk/StaticMeshes/IslandChunk"):
    m = unreal.EditorAssetLibrary.load_asset(p)
    if m:
        b = m.get_bounding_box()
        size = b.max - b.min
        print(f"BOUNDS {p.split('/')[-1]}: {size.x:.1f} x {size.y:.1f} x {size.z:.1f} uu")
    else:
        print(f"MISSING {p}")
