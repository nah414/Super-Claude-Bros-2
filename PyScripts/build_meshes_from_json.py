"""Build StaticMesh assets from JSON geometry via GeometryScript — NO Interchange.

The glb importer's unit conversion proved non-deterministic across re-imports
(microscopic one run, colossal the next). This pipeline owns every number:
ArtSource/json/*.json (verts already in UE units, winding already left-handed)
-> DynamicMesh -> StaticMesh asset at a FLAT path /Game/Art/Kit/<Name> (or
/Game/Art/Hero/SparkHero), with vertex colors, our materials, Nanite off.
"""
import json
import os
import unreal

JSON_DIR = r"C:\Users\Atomn\mario2\SuperClaudeBros2\ArtSource\json"
EAL = unreal.EditorAssetLibrary

EMISSIVE_NAMES = ("crystal", "monument")


def get_material(name):
    p = f"/Game/Art/{name}"
    return EAL.load_asset(p) if EAL.does_asset_exist(p) else None


M_LIT = get_material("M_VertexLit")
M_EMIS = get_material("M_VertexLitEmissive")


def build_asset(jpath):
    with open(jpath) as fh:
        data = json.load(fh)
    name = data["name"]
    dest_folder = "/Game/Art/Hero" if name == "SparkHero" else "/Game/Art/Kit"
    asset_path = f"{dest_folder}/{name}"

    # Buffers (5.7 python names: GeometryScriptSimpleMeshBuffers / GeometryScript_MeshEdits)
    buffers = unreal.GeometryScriptSimpleMeshBuffers()
    buffers.vertices = [unreal.Vector(v[0], v[1], v[2]) for v in data["vertices"]]
    buffers.triangles = [unreal.IntVector(t[0], t[1], t[2]) for t in data["triangles"]]
    buffers.vertex_colors = [unreal.LinearColor(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, 1.0)
                             for c in data["colors"]]
    # StaticMesh build asserts NumUVs > 0 — supply simple planar UVs (we're vertex-colored).
    buffers.uv0 = [unreal.Vector2D(v[0] / 100.0, v[1] / 100.0) for v in data["vertices"]]

    dyn = unreal.DynamicMesh()
    res = unreal.GeometryScript_MeshEdits.append_buffers_to_mesh(dyn, buffers, material_id=0)
    dyn = res[0] if isinstance(res, tuple) else res        # multi-return -> tuple in python
    # Recompute normals so the low-poly facets shade correctly.
    opts = unreal.GeometryScriptCalculateNormalsOptions()
    res = unreal.GeometryScript_Normals.recompute_normals(dyn, opts)
    dyn = res[0] if isinstance(res, tuple) else res

    # Fresh asset (delete stale Interchange leftovers at BOTH possible paths).
    for stale in (asset_path, f"{dest_folder}/{name}/StaticMeshes/{name}"):
        if EAL.does_asset_exist(stale):
            EAL.delete_asset(stale)
    if EAL.does_directory_exist(f"{dest_folder}/{name}"):
        EAL.delete_directory(f"{dest_folder}/{name}")

    sm_opts = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    result = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        dyn, asset_path, sm_opts)
    # Multi-return order varies; find the StaticMesh in the tuple.
    asset = None
    for item in (result if isinstance(result, tuple) else (result,)):
        if isinstance(item, unreal.StaticMesh):
            asset = item
            break
    if asset is None:
        print(f"GEOBUILD_FAIL: {name} ({result})")
        return False

    # Material + Nanite off + save
    want = M_EMIS if any(k in name.lower() for k in EMISSIVE_NAMES) else M_LIT
    if want:
        n_mats = max(1, len(asset.get_editor_property("static_materials")))
        for i in range(n_mats):
            asset.set_material(i, want)
    try:
        ns = asset.get_editor_property("nanite_settings")
        ns.set_editor_property("enabled", False)
        asset.set_editor_property("nanite_settings", ns)
    except Exception:
        pass
    EAL.save_loaded_asset(asset)
    b = asset.get_bounding_box()
    size = b.max - b.min
    print(f"GEOBUILD: {name} -> {asset_path}  ({size.x:.0f} x {size.y:.0f} x {size.z:.0f} uu)")
    return True


ok = fail = 0
for f in sorted(os.listdir(JSON_DIR)):
    if f.endswith(".json"):
        if build_asset(os.path.join(JSON_DIR, f)):
            ok += 1
        else:
            fail += 1
print(f"GEOBUILD_DONE: ok={ok} fail={fail}")
