"""Empirical 5.7 CollectionParameter fix test: forge a scratch material whose
emissive reads MPC Breath, trying candidate bindings; the log tells which
compiles ('invalid parameter None' gone)."""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DEST = "/Game/Art/Verdant"

mpc = EAL.load_asset(f"{DEST}/MPC_VerdantBreath")
assert mpc

# introspect the collection's parameter entries
for arr in ("scalar_parameters", "vector_parameters"):
    for p in mpc.get_editor_property(arr):
        pid = "unexposed"
        try:
            pid = str(p.get_editor_property("id"))
        except Exception as ex:
            pid = f"ERR:{ex}"
        print(f"MPCFIX: {arr} {p.get_editor_property('parameter_name')} id={pid}")


def scratch(name, bind):
    path = f"{DEST}/{name}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    m = tools.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    node = MEL.create_material_expression(
        m, unreal.MaterialExpressionCollectionParameter, -400, 0)
    node.set_editor_property("collection", mpc)
    node.set_editor_property("parameter_name", "Breath")
    bind(node)
    MEL.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    print(f"MPCFIX: {name} forged+saved — check log for 'invalid parameter' near this line")
    return node


def bind_none(node):
    print("MPCFIX: A = name only (the failing status quo)")


def bind_guid(node):
    try:
        for p in mpc.get_editor_property("scalar_parameters"):
            if str(p.get_editor_property("parameter_name")) == "Breath":
                node.set_editor_property("parameter_id", p.get_editor_property("id"))
                print("MPCFIX: B = parameter_id set from collection GUID — OK")
                return
    except Exception as ex:
        print(f"MPCFIX: B parameter_id bind failed: {ex}")


def bind_pec(node):
    try:
        node.post_edit_change()
        print("MPCFIX: C = post_edit_change() — OK")
    except Exception as ex:
        print(f"MPCFIX: C post_edit_change failed: {ex}")


n = scratch("M_ZZ_MPCTestA", bind_none)
print(f"MPCFIX: node prop probe: "
      f"{[a for a in dir(n) if 'param' in a.lower() or 'edit' in a.lower()]}")
scratch("M_ZZ_MPCTestB", bind_guid)
scratch("M_ZZ_MPCTestC", bind_pec)
print("MPCFIX_DONE")
