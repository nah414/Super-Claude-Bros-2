"""Diagnose the 5.7 CollectionParameter binding: compare a failing material's
MPC node against the (apparently) passing river. Read-only."""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

mpc = EAL.load_asset("/Game/Art/Verdant/MPC_VerdantBreath")
print(f"DIAG: MPC scalars: {[str(p.get_editor_property('parameter_name')) for p in mpc.get_editor_property('scalar_parameters')]}")
for p in mpc.get_editor_property("scalar_parameters"):
    print(f"DIAG: scalar {p.get_editor_property('parameter_name')} id={p.get_editor_property('id') if hasattr(p, 'id') else 'n/a'}")

for mat_name in ("M_VR_Canopy", "M_VR_WaterFlow"):
    m = EAL.load_asset(f"/Game/Art/Verdant/{mat_name}")
    exprs = MEL.get_material_expressions(m) if hasattr(MEL, "get_material_expressions") else m.get_editor_property("expressions")
    n_cp = 0
    for e in exprs:
        if isinstance(e, unreal.MaterialExpressionCollectionParameter):
            n_cp += 1
            props = {}
            for prop in ("parameter_name", "collection"):
                try:
                    props[prop] = str(e.get_editor_property(prop))
                except Exception as ex:
                    props[prop] = f"ERR {ex}"
            print(f"DIAG: {mat_name} CP#{n_cp}: {props}")
            print(f"DIAG: {mat_name} CP#{n_cp} dir: "
                  f"{[p for p in dir(e) if 'param' in p.lower() or 'id' in p.lower()]}")
    print(f"DIAG: {mat_name} has {n_cp} CollectionParameter nodes")
print("DIAG_DONE")
