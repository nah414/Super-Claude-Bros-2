"""Second instrument: render VertexColor.R as emissive on the river. Black
V-wakes-on-dark = the baked foam mask arrived; solid WHITE = the mask was lost
in the Blender->FBX->UE chain and VC defaults to 1 (the eternal-lace cause)."""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DEST = "/Game/Art/Verdant"

path = f"{DEST}/M_ZZ_VCDebug"
if EAL.does_asset_exist(path):
    EAL.delete_asset(path)
m = tools.create_asset("M_ZZ_VCDebug", DEST, unreal.Material,
                       unreal.MaterialFactoryNew())
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)
vc = MEL.create_material_expression(m, unreal.MaterialExpressionVertexColor, -400, 0)
MEL.connect_material_property(vc, "R", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
op = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 200)
op.set_editor_property("r", 1.0)
MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
MEL.recompile_material(m)
EAL.save_loaded_asset(m)

mesh = EAL.load_asset(f"{DEST}/river_surface")
mesh.set_material(0, m)
EAL.save_loaded_asset(mesh)
print("VCDEBUG: river renders its vertex color — shoot and read")
print("VCDEBUG_DONE")
