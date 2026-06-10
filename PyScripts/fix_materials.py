"""Diagnose + repair the vertex-color materials and their assignment.

The kit rendered WHITE on first light: either the M_VertexLit graph connections
failed silently or the slot assignment missed the Interchange-nested mesh paths.
This script prints hard evidence for every step and force-repairs both.
Run via UnrealEditor-Cmd -ExecutePythonScript.
"""
import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

KIT = ["Rock_Small", "Rock_Medium", "Rock_Large", "Pine_Small", "Pine_Tall",
       "Crystal_Small", "Crystal_Tall", "Column", "Arch", "GrassTuft",
       "Monument", "IslandChunk"]


def rebuild_material(path, name, emissive):
    """(Re)create a vertex-color material with VERIFIED connections."""
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(name, "/Game/Art", unreal.Material, unreal.MaterialFactoryNew())
    vc = MEL.create_material_expression(mat, unreal.MaterialExpressionVertexColor, -500, 0)
    ok_base = MEL.connect_material_property(vc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 220)
    rough.set_editor_property("r", 0.7)
    ok_rough = MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    ok_emis = True
    if emissive:
        mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -300, 420)
        vc2 = MEL.create_material_expression(mat, unreal.MaterialExpressionVertexColor, -500, 380)
        k = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 520)
        k.set_editor_property("r", 8.0)
        MEL.connect_material_expressions(vc2, "", mul, "A")
        MEL.connect_material_expressions(k, "", mul, "B")
        ok_emis = MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    print(f"MATFIX: {name} connections base={ok_base} rough={ok_rough} emissive={ok_emis}")
    return mat


def find_mesh(base, name):
    for p in (f"{base}/{name}/StaticMeshes/{name}", f"{base}/{name}"):
        if EAL.does_asset_exist(p):
            return EAL.load_asset(p), p
    return None, None


def rebuild_flat_material(path, name, r, g, b, roughness):
    """A simple constant-color PBR material (for level geometry: ground, stone)."""
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(name, "/Game/Art", unreal.Material, unreal.MaterialFactoryNew())
    col = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -500, 0)
    col.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    ok = MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rgh = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 220)
    rgh.set_editor_property("r", roughness)
    MEL.connect_material_property(rgh, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    print(f"MATFIX: {name} base={ok}")
    return mat


m_lit = rebuild_material("/Game/Art/M_VertexLit", "M_VertexLit", emissive=False)
m_emis = rebuild_material("/Game/Art/M_VertexLitEmissive", "M_VertexLitEmissive", emissive=True)
# Night-level geometry materials: deep blue-green ground, cool stone.
rebuild_flat_material("/Game/Art/M_NightGround", "M_NightGround", 0.02, 0.04, 0.028, 0.95)
rebuild_flat_material("/Game/Art/M_Stone", "M_Stone", 0.16, 0.17, 0.21, 0.85)

targets = [("/Game/Art/Kit", n) for n in KIT] + [("/Game/Art/Hero", "SparkHero")]
fixed, missing = 0, 0
for base, name in targets:
    mesh, path = find_mesh(base, name)
    if mesh is None:
        print(f"MATFIX_MISSING: {base}/{name}")
        missing += 1
        continue
    want = m_emis if ("crystal" in name.lower() or "monument" in name.lower()) else m_lit
    n_slots = mesh.get_num_sections(0) if hasattr(mesh, "get_num_sections") else 1
    n_mats = len(mesh.get_editor_property("static_materials"))
    before = [str(sm.material_interface.get_name()) if sm.material_interface else "None"
              for sm in mesh.get_editor_property("static_materials")]
    for i in range(n_mats):
        mesh.set_material(i, want)
    # Nanite OFF: Interchange auto-enables it, but these are sub-2k-tri stylized
    # meshes — Nanite is pure overhead and one more way to render nothing.
    try:
        ns = mesh.get_editor_property("nanite_settings")
        if ns.get_editor_property("enabled"):
            ns.set_editor_property("enabled", False)
            mesh.set_editor_property("nanite_settings", ns)
            print(f"MATFIX: {name} nanite disabled")
    except Exception as e:
        print(f"MATFIX: {name} nanite toggle failed: {e}")
    EAL.save_loaded_asset(mesh)
    after = [str(sm.material_interface.get_name()) if sm.material_interface else "None"
             for sm in mesh.get_editor_property("static_materials")]
    print(f"MATFIX: {name} slots={n_mats} {before} -> {after}")
    fixed += 1

print(f"MATFIX_DONE: fixed={fixed} missing={missing}")
