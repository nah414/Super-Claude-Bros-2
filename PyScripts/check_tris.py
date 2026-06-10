import unreal
for p in ("/Game/Art/Hero/SparkHero/StaticMeshes/SparkHero",
          "/Game/Art/Kit/Pine_Tall/StaticMeshes/Pine_Tall",
          "/Game/Art/Kit/IslandChunk/StaticMeshes/IslandChunk",
          "/Game/Art/Kit/Rock_Small/StaticMeshes/Rock_Small"):
    m = unreal.EditorAssetLibrary.load_asset(p)
    name = p.split("/")[-1]
    if not m:
        print(f"TRI {name}: MISSING")
        continue
    try:
        lods = m.get_num_lods()
        tris = m.get_num_triangles(0)
        sections = m.get_num_sections(0)
        verts = m.get_num_vertices(0)
        print(f"TRI {name}: lods={lods} sections={sections} tris={tris} verts={verts}")
    except Exception as e:
        print(f"TRI {name}: query failed: {e}")
