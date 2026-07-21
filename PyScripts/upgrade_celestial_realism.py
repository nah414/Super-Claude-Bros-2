"""Celestial realism upgrade (Adam 2026-07-21, Meshy credits green-lit):
  * moon_large_red + planet_gasgiant: fresh Meshy RETEXTURE (realistic craters /
    Jupiter banding) imported at 4K with their normal maps.
  * moon_small_pale: original textures, now also at 4K + normal map.
  * All three M_*_lit materials rebuilt: base color x tint x NORMAL-MAP RELIEF
    (a fixed sun direction dotted against the normal map) — craters and cloud
    bands finally cast visible shading instead of the flat billboard look.
Meshes already reference these materials, so the sky updates in place.
Run: UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/upgrade_celestial_realism.py
     -unattended -nosplash -RenderOffscreen -nopause
"""
import os

import unreal

# Interchange crashes headless texture imports (same reason import_celestial.py
# disables it for FBX) — force the legacy importers for this commandlet.
for flag in ("Interchange.FeatureFlags.Import.Textures", "Interchange.FeatureFlags.Import.Texture",
             "Interchange.FeatureFlags.Import.PNG", "Interchange.FeatureFlags.Import.FBX"):
    try:
        unreal.SystemLibrary.execute_console_command(None, f"{flag} false")
    except Exception:
        pass

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

RETEX = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\celestial_retex"
ORIG = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\celestial"
DEST = "/Game/Art/Celestial"

# body -> (src_dir, tint, brightness)
BODIES = {
    "moon_large_red":  (RETEX, (1.00, 0.42, 0.30), 0.55),
    "planet_gasgiant": (RETEX, (1.00, 0.97, 0.90), 1.05),
    "moon_small_pale": (ORIG,  (0.45, 0.40, 0.38), 0.60),
}

SUN_DIR = (0.45, 0.18, 0.88)   # fixed key-light direction for the relief shading


def import_tex(png, dest, name):
    t = unreal.AssetImportTask()
    t.filename = png
    t.destination_path = dest
    t.destination_name = name
    t.automated = True
    t.save = True
    t.replace_existing = True
    tools.import_asset_tasks([t])
    tex = EAL.load_asset(f"{dest}/{name}")
    return tex


def build_mat(name, dest, base, normal, tint, bright):
    path = f"{dest}/{name}"
    mat = EAL.load_asset(path)
    if not mat:
        mat = tools.create_asset(name, dest, unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(mat)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)

    ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -700, -60)
    ts.set_editor_property("texture", base)

    ns = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -700, 220)
    ns.set_editor_property("texture", normal)
    try:
        ns.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    except Exception as e:
        unreal.log_warning(f"sampler {name}: {e}")

    sun = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, 420)
    sun.set_editor_property("constant", unreal.LinearColor(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2], 1.0))

    dp = MEL.create_material_expression(mat, unreal.MaterialExpressionDotProduct, -480, 300)
    MEL.connect_material_expressions(ns, "", dp, "A")
    MEL.connect_material_expressions(sun, "", dp, "B")

    cl = MEL.create_material_expression(mat, unreal.MaterialExpressionClamp, -360, 300)
    MEL.connect_material_expressions(dp, "", cl, "")

    k = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -360, 400)
    k.set_editor_property("r", 0.70)
    m1 = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -240, 330)
    MEL.connect_material_expressions(cl, "", m1, "A")
    MEL.connect_material_expressions(k, "", m1, "B")
    k2 = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -240, 430)
    k2.set_editor_property("r", 0.30)
    shade = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, -120, 350)
    MEL.connect_material_expressions(m1, "", shade, "A")
    MEL.connect_material_expressions(k2, "", shade, "B")

    tintc = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -480, 60)
    tintc.set_editor_property("constant",
                              unreal.LinearColor(tint[0] * bright, tint[1] * bright, tint[2] * bright, 1.0))
    m2 = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -300, 0)
    MEL.connect_material_expressions(ts, "", m2, "A")
    MEL.connect_material_expressions(tintc, "", m2, "B")
    m3 = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -60, 60)
    MEL.connect_material_expressions(m2, "", m3, "A")
    MEL.connect_material_expressions(shade, "", m3, "B")

    MEL.connect_material_property(m3, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    return mat


done = 0
for body, (src, tint, bright) in BODIES.items():
    bdir = f"{DEST}/{body}"
    base_png = os.path.join(src, body, f"{body}_tex0_base_color.png")
    norm_png = os.path.join(src, body, f"{body}_tex0_normal.png")
    if not (os.path.isfile(base_png) and os.path.isfile(norm_png)):
        unreal.log_warning(f"CELUP MISSING_PNG {body}")
        continue
    base = import_tex(base_png, bdir, f"T_{body}_base4k")
    norm = import_tex(norm_png, bdir, f"T_{body}_normal4k")
    if not (base and norm):
        unreal.log_warning(f"CELUP IMPORT_FAIL {body}")
        continue
    for tx, is_norm in ((base, False), (norm, True)):
        try:
            tx.set_editor_property("max_texture_size", 4096)
            if is_norm:
                tx.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                tx.set_editor_property("srgb", False)
            EAL.save_loaded_asset(tx)
        except Exception as e:
            unreal.log_warning(f"CELUP texprop {tx.get_name()}: {e}")
    build_mat(f"M_{body}_lit", bdir, base, norm, tint, bright)
    unreal.log_warning(f"CELUP OK {body}: 4K base+normal, relief-shaded material rebuilt")
    done += 1

EAL.save_directory(DEST, recursive=True)
unreal.log_warning(f"CELUP_DONE {done}/3")
