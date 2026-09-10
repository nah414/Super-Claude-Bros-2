"""Forge the hero SKINS — the guardians' aspects, granted to the Spark Hero.
Each skin recolors his own base texture (keeping every detail) + a per-skin
surface: Classic Spark gold, the Sleek Knight's polished silver, the Heroic
Tank's matte bark, the Powerhouse's steel sheen.
"""
import unreal

MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
DEST = "/Game/Art/HeroSkelV4"

base_tex = unreal.load_asset(f"{DEST}/T_Hero_BaseColor")
norm_tex = unreal.load_asset(f"{DEST}/T_Hero_Normal")

# name: (tint, roughness, metallic)
SKINS = {
    "Classic":    (unreal.LinearColor(1.55, 1.05, 0.42), 0.45, 0.00),   # the original golden Spark
    "Knight":     (unreal.LinearColor(1.30, 1.45, 1.75), 0.20, 0.15),   # polished silver-crystal
    "Tank":       (unreal.LinearColor(0.72, 0.95, 0.48), 0.72, 0.00),   # matte bark/moss
    "Powerhouse": (unreal.LinearColor(0.80, 0.92, 1.18), 0.34, 0.62),   # steel sheen
}

made = 0
for name, (tint, rough, metal) in SKINS.items():
    mat = tools.create_asset(f"M_HeroSkin_{name}", DEST, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("used_with_skeletal_mesh", True)

    ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -720, -200)
    if base_tex:
        ts.texture = base_tex
    tintc = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -720, 30)
    tintc.set_editor_property("constant", tint)
    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -420, -120)
    MEL.connect_material_expressions(ts, "RGB", mul, "A")
    MEL.connect_material_expressions(tintc, "", mul, "B")
    ok_base = MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)

    if norm_tex:
        ns = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -720, 280)
        ns.texture = norm_tex
        ns.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        MEL.connect_material_property(ns, "RGB", unreal.MaterialProperty.MP_NORMAL)

    r = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -720, 520)
    r.set_editor_property("r", rough)
    MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -720, 640)
    m.set_editor_property("r", metal)
    MEL.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)

    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    made += 1
    print(f"SKIN_DONE: {name} base={ok_base}")

print(f"HERO_SKINS_DONE: {made}/4")
