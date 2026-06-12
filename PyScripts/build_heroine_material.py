"""Forge M_HeroinePBR — kill the Meshy baked-emission glow (the Brightness War, body edition).

The FBX importer wired texture_0_ncl1_1 (a full albedo copy, Meshy's baked
emission channel) into Material_1's EMISSIVE — the whole body self-emits and
blooms to white. New material: lit, opaque, base color + sane roughness, NO
emissive. We forge fresh rather than edit Material_1 (a reimport would clobber it).
"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
DEST = "/Game/Art/HeroineSkelV2"
MAT_PATH = f"{DEST}/M_HeroinePBR"

if EAL.does_asset_exist(MAT_PATH):
    EAL.delete_asset(MAT_PATH)

tools = unreal.AssetToolsHelpers.get_asset_tools()
mat = tools.create_asset("M_HeroinePBR", DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("used_with_skeletal_mesh", True)

base_tex = unreal.load_asset(f"{DEST}/texture_0")
ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, -100)
ts.texture = base_tex
ok_base = MEL.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

rough = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 150)
rough.set_editor_property("r", 0.55)
ok_rough = MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

metal = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 300)
metal.set_editor_property("r", 0.0)
ok_metal = MEL.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)

spec = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 450)
spec.set_editor_property("r", 0.35)
ok_spec = MEL.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)

MEL.recompile_material(mat)
print(f"HMATFIX: connects base={ok_base} rough={ok_rough} metal={ok_metal} spec={ok_spec}")
saved_mat = EAL.save_loaded_asset(mat)

mesh = unreal.load_asset(f"{DEST}/SCB2Heroine")
mats = mesh.get_editor_property("materials")
new_mats = []
for m in mats:
    slot = m.get_editor_property("material_slot_name")
    new_mats.append(unreal.SkeletalMaterial(material_interface=mat, material_slot_name=slot))
mesh.set_editor_property("materials", new_mats)
saved_mesh = EAL.save_loaded_asset(mesh)
print(f"HMATFIX: assigned {len(new_mats)} slot(s); mat_saved={saved_mat} mesh_saved={saved_mesh}")
print("HMATFIX_DONE")
