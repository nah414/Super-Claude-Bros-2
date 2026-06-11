"""Neon District textures + materials — the wet-street look, verified connects.

Imports ArtSource/textures_city/*.png then builds:
  M_WetAsphalt    dark asphalt; roughness lerps 0.5 dry -> 0.04 in puddles
                  (puddle mask sampled in WORLD XY so puddles anchor to the street)
  M_Sidewalk      plain dark concrete
  M_Sign_<name>   one emissive material per PIL sign face (x7)
  M_Windows_<v>   emissive lit-window sheets for backdrop towers (x3)
  M_RainStreak    unlit translucent panner — the rain curtain skin
  M_HoloBillboard sign_district face with a slow sine flicker

Lessons baked in: save_loaded_asset right after recompile; every connect checked.
"""
import os

import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

TEX_SRC = r"C:\Users\Atomn\mario2\SuperClaudeBros2\ArtSource\textures_city"
TEX_DEST = "/Game/Art/CityTex"
MAT_DEST = "/Game/Art/CityMat"

SIGNS = ["kraken", "spark", "lumen", "moth", "warden", "glimmer", "district"]
WINDOWS = ["a", "b", "c"]


def import_texture(png_name, asset_name, srgb=True):
    src = os.path.join(TEX_SRC, png_name)
    if not os.path.isfile(src):
        raise SystemExit(f"TEX_MISSING: {src}")
    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = TEX_DEST
    task.destination_name = asset_name
    task.automated = True
    task.save = True
    task.replace_existing = True
    TOOLS.import_asset_tasks([task])
    tex = unreal.load_asset(f"{TEX_DEST}/{asset_name}")
    if not tex:
        raise SystemExit(f"TEX_IMPORT_FAILED: {asset_name}")
    tex.set_editor_property("srgb", srgb)
    EAL.save_loaded_asset(tex)
    print(f"TEX_OK: {asset_name}")
    return tex


def new_material(name):
    path = f"{MAT_DEST}/{name}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    return TOOLS.create_asset(name, MAT_DEST, unreal.Material, unreal.MaterialFactoryNew())


def finish(mat, name, checks):
    for label, ok in checks:
        print(f"CONNECT {name}.{label}: {ok}")
        if not ok:
            raise SystemExit(f"MATERIAL_CONNECT_FAILED: {name}.{label}")
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    print(f"MAT_OK: {name}")


# ---- textures ----
textures = {}
for s in SIGNS:
    textures[f"sign_{s}"] = import_texture(f"sign_{s}.png", f"T_Sign_{s}", srgb=True)
for v in WINDOWS:
    textures[f"win_{v}"] = import_texture(f"windows_{v}.png", f"T_Windows_{v}", srgb=True)
textures["rain"] = import_texture("rain_streak.png", "T_RainStreak", srgb=False)
textures["puddle"] = import_texture("puddle_mask.png", "T_PuddleMask", srgb=False)

# ---- M_WetAsphalt ----
mat = new_material("M_WetAsphalt")
wp = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1200, 0)
mask_xy = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -1000, 0)
mask_xy.set_editor_property("r", True)
mask_xy.set_editor_property("g", True)
mask_xy.set_editor_property("b", False)
mask_xy.set_editor_property("a", False)
div = MEL.create_material_expression(mat, unreal.MaterialExpressionDivide, -800, 0)
scale = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -1000, 140)
scale.set_editor_property("r", 2600.0)  # one mask tile per 26m of street
MEL.connect_material_expressions(wp, "", mask_xy, "")
MEL.connect_material_expressions(mask_xy, "", div, "A")
MEL.connect_material_expressions(scale, "", div, "B")
pud = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -600, 0)
pud.set_editor_property("texture", textures["puddle"])
pud.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
MEL.connect_material_expressions(div, "", pud, "UVs")
rough = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -350, 60)
dry = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -600, 180)
dry.set_editor_property("r", 0.5)
wet = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -600, 260)
wet.set_editor_property("r", 0.04)
MEL.connect_material_expressions(dry, "", rough, "A")
MEL.connect_material_expressions(wet, "", rough, "B")
MEL.connect_material_expressions(pud, "R", rough, "Alpha")
base = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -350, -160)
dryc = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -600, -260)
dryc.set_editor_property("constant", unreal.LinearColor(0.020, 0.022, 0.028, 1.0))
wetc = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -600, -100)
wetc.set_editor_property("constant", unreal.LinearColor(0.008, 0.009, 0.013, 1.0))
MEL.connect_material_expressions(dryc, "", base, "A")
MEL.connect_material_expressions(wetc, "", base, "B")
MEL.connect_material_expressions(pud, "R", base, "Alpha")
finish(mat, "M_WetAsphalt", [
    ("base", MEL.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)),
    ("rough", MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)),
])

# ---- M_Sidewalk ----
mat = new_material("M_Sidewalk")
c = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -500, 0)
c.set_editor_property("constant", unreal.LinearColor(0.045, 0.047, 0.055, 1.0))
r = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 180)
r.set_editor_property("r", 0.55)
finish(mat, "M_Sidewalk", [
    ("base", MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)),
    ("rough", MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)),
])

# ---- M_Sign_<name> x7 ----
for s in SIGNS:
    mat = new_material(f"M_Sign_{s}")
    t = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -700, 0)
    t.set_editor_property("texture", textures[f"sign_{s}"])
    t.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    boost = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 220)
    boost.set_editor_property("r", 6.0)
    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, 80)
    MEL.connect_material_expressions(t, "RGB", mul, "A")
    MEL.connect_material_expressions(boost, "", mul, "B")
    finish(mat, f"M_Sign_{s}", [
        ("emissive", MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)),
        ("base", MEL.connect_material_property(t, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)),
    ])

# ---- M_Windows_<v> x3 ----
for v in WINDOWS:
    mat = new_material(f"M_Windows_{v}")
    t = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -700, 0)
    t.set_editor_property("texture", textures[f"win_{v}"])
    t.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    boost = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 220)
    boost.set_editor_property("r", 2.5)
    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, 80)
    MEL.connect_material_expressions(t, "RGB", mul, "A")
    MEL.connect_material_expressions(boost, "", mul, "B")
    dark = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, -180)
    dark.set_editor_property("constant", unreal.LinearColor(0.01, 0.011, 0.014, 1.0))
    finish(mat, f"M_Windows_{v}", [
        ("emissive", MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)),
        ("base", MEL.connect_material_property(dark, "", unreal.MaterialProperty.MP_BASE_COLOR)),
    ])

# ---- M_RainStreak (unlit translucent panner) ----
mat = new_material("M_RainStreak")
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", True)
tc = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
tc.set_editor_property("u_tiling", 4.0)
tc.set_editor_property("v_tiling", 2.0)
pan = MEL.create_material_expression(mat, unreal.MaterialExpressionPanner, -900, 0)
pan.set_editor_property("speed_y", -1.6)  # rain falls
MEL.connect_material_expressions(tc, "", pan, "Coordinate")
t = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -650, 0)
t.set_editor_property("texture", textures["rain"])
t.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
MEL.connect_material_expressions(pan, "", t, "UVs")
tint = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -650, -200)
tint.set_editor_property("constant", unreal.LinearColor(0.85, 0.95, 1.20, 1.0))
emul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, -80)
MEL.connect_material_expressions(t, "R", emul, "A")
MEL.connect_material_expressions(tint, "", emul, "B")
omul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, 160)
ok_ = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -650, 240)
ok_.set_editor_property("r", 0.46)
MEL.connect_material_expressions(t, "R", omul, "A")
MEL.connect_material_expressions(ok_, "", omul, "B")
finish(mat, "M_RainStreak", [
    ("emissive", MEL.connect_material_property(emul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)),
    ("opacity", MEL.connect_material_property(omul, "", unreal.MaterialProperty.MP_OPACITY)),
])

# ---- M_HoloBillboard (district face + slow sine flicker) ----
mat = new_material("M_HoloBillboard")
t = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -900, 0)
t.set_editor_property("texture", textures["sign_district"])
t.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
tm = MEL.create_material_expression(mat, unreal.MaterialExpressionTime, -900, 260)
sine = MEL.create_material_expression(mat, unreal.MaterialExpressionSine, -740, 260)
sine.set_editor_property("period", 3.5)
MEL.connect_material_expressions(tm, "", sine, "")
half = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -580, 260)
hk = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -740, 380)
hk.set_editor_property("r", 0.8)
MEL.connect_material_expressions(sine, "", half, "A")
MEL.connect_material_expressions(hk, "", half, "B")
basek = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -580, 380)
basek.set_editor_property("r", 4.0)
flick = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, -420, 300)
MEL.connect_material_expressions(half, "", flick, "A")
MEL.connect_material_expressions(basek, "", flick, "B")
mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -260, 80)
MEL.connect_material_expressions(t, "RGB", mul, "A")
MEL.connect_material_expressions(flick, "", mul, "B")
finish(mat, "M_HoloBillboard", [
    ("emissive", MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)),
    ("base", MEL.connect_material_property(t, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)),
])

print("CITY_MATERIALS_DONE")
