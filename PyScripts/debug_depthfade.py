"""Decisive DepthFade instrument: dress the river in a material whose emissive
IS DepthFade(400). If the -game shot shows the river BLACK, scene-depth reads
zero thickness there (every depth cue vacuous); white-in-the-deeps means
DepthFade works and the flood has another cause. Restore with
restore_river_material.py."""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DEST = "/Game/Art/Verdant"

path = f"{DEST}/M_ZZ_DepthDebug"
if EAL.does_asset_exist(path):
    EAL.delete_asset(path)
m = tools.create_asset("M_ZZ_DepthDebug", DEST, unreal.Material,
                       unreal.MaterialFactoryNew())
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)
df = MEL.create_material_expression(m, unreal.MaterialExpressionDepthFade, -400, 0)
df.set_editor_property("fade_distance_default", 400.0)
MEL.connect_material_property(df, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
op = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 200)
op.set_editor_property("r", 1.0)
MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
MEL.recompile_material(m)
EAL.save_loaded_asset(m)

mesh = EAL.load_asset(f"{DEST}/river_surface")
mesh.set_material(0, m)
EAL.save_loaded_asset(mesh)
print("DEPTHDEBUG: river wears the instrument — shoot, read, restore")
print("DEPTHDEBUG_DONE")
