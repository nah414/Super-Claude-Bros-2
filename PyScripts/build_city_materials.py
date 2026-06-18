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
    # Reuse the already-imported texture if present — the AssetImportTask PNG import CRASHES
    # under headless -run=pythonscript (Slate CurrentApplication.IsValid assertion). Loading an
    # existing asset is safe headless; only a first-time import needs the GUI editor.
    existing = unreal.load_asset(f"{TEX_DEST}/{asset_name}")
    if existing:
        print(f"TEX_REUSE: {asset_name}")
        return existing
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
    boost.set_editor_property("r", 4.0)
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
    boost.set_editor_property("r", 0.8)  # windows glitter; they must not LIGHT the city
    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, 80)
    MEL.connect_material_expressions(t, "RGB", mul, "A")
    MEL.connect_material_expressions(boost, "", mul, "B")
    dark = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, -180)
    dark.set_editor_property("constant", unreal.LinearColor(0.075, 0.073, 0.080, 1.0))  # visible concrete, not a void
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

# ============================================================================
# GRITTY-INDUSTRIAL PBR LIBRARY (M1) — Adam's art direction: raw concrete, rusted
# metal, warm grimy windows, under the warm night light. All PROCEDURAL (Noise +
# masks, no scanned textures) so it's free + texture-light for the 8GB GPU.
# ============================================================================

def _x(mat, cls, x, y):
    return MEL.create_material_expression(mat, cls, x, y)


def _const(mat, v, x, y):
    e = _x(mat, unreal.MaterialExpressionConstant, x, y)
    e.set_editor_property("r", v)
    return e


def _rgb(mat, rgb, x, y):
    e = _x(mat, unreal.MaterialExpressionConstant3Vector, x, y)
    e.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    return e


def _noise(mat, x, y, scale=0.02, levels=4, omin=0.0, omax=1.0):
    n = _x(mat, unreal.MaterialExpressionNoise, x, y)
    try:
        n.set_editor_property("scale", scale)
        n.set_editor_property("levels", levels)
        n.set_editor_property("output_min", omin)
        n.set_editor_property("output_max", omax)
    except Exception as e:
        unreal.log_warning(f"noise prop skip: {e}")
    return n


def _lerp(mat, a, b, alpha, x, y, apin=""):
    l = _x(mat, unreal.MaterialExpressionLinearInterpolate, x, y)
    MEL.connect_material_expressions(a, "", l, "A")
    MEL.connect_material_expressions(b, "", l, "B")
    MEL.connect_material_expressions(alpha, apin, l, "Alpha")
    return l


def _mul(mat, a, b, x, y, apin="", bpin=""):
    m = _x(mat, unreal.MaterialExpressionMultiply, x, y)
    MEL.connect_material_expressions(a, apin, m, "A")
    MEL.connect_material_expressions(b, bpin, m, "B")
    return m


def _worldZ01(mat, x, y, low=0.0, high=2000.0):
    """A 0..1 gradient from world Z (low->0, high->1) — for grime-at-the-base / rust drips."""
    wp = _x(mat, unreal.MaterialExpressionWorldPosition, x, y)
    mz = _x(mat, unreal.MaterialExpressionComponentMask, x + 150, y)
    mz.set_editor_property("r", False); mz.set_editor_property("g", False)
    mz.set_editor_property("b", True); mz.set_editor_property("a", False)
    MEL.connect_material_expressions(wp, "", mz, "")
    sub = _x(mat, unreal.MaterialExpressionSubtract, x + 320, y)
    lo = _const(mat, low, x + 150, y + 120)
    MEL.connect_material_expressions(mz, "", sub, "A")
    MEL.connect_material_expressions(lo, "", sub, "B")
    dv = _x(mat, unreal.MaterialExpressionDivide, x + 480, y)
    sp = _const(mat, max(1.0, high - low), x + 320, y + 120)
    MEL.connect_material_expressions(sub, "", dv, "A")
    MEL.connect_material_expressions(sp, "", dv, "B")
    cl = _x(mat, unreal.MaterialExpressionClamp, x + 640, y)
    MEL.connect_material_expressions(dv, "", cl, "")
    return cl


# ---- M_Concrete: brutalist raw concrete, mottled + grimy (default wall/cliff skin) ----
mat = new_material("M_Concrete")
nbig = _noise(mat, -1100, -200, scale=0.010, levels=4)        # big stain mottle
nfin = _noise(mat, -1100, 200, scale=0.060, levels=3)         # fine grain
darkc = _rgb(mat, (0.060, 0.061, 0.066), -800, -320)
litec = _rgb(mat, (0.185, 0.180, 0.165), -800, -180)
col = _lerp(mat, darkc, litec, nbig, -560, -240)
grime = _worldZ01(mat, -1500, 360, low=0.0, high=900.0)       # dirtier near the ground
grimed = _lerp(mat, _rgb(mat, (0.4, 0.4, 0.42), -560, -60), _rgb(mat, (1.0, 1.0, 1.0), -560, 40),
               grime, -360, -20)
basecol = _mul(mat, col, grimed, -180, -160)
rdry = _const(mat, 0.88, -560, 200)
rsmooth = _const(mat, 0.62, -560, 300)
rough = _lerp(mat, rdry, rsmooth, nfin, -360, 240)
finish(mat, "M_Concrete", [
    ("base", MEL.connect_material_property(basecol, "", unreal.MaterialProperty.MP_BASE_COLOR)),
    ("rough", MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)),
])

# ---- M_RustMetal: painted industrial metal, rusted + streaked (spire, machinery, cliffs) ----
mat = new_material("M_RustMetal")
nrust = _noise(mat, -1100, -200, scale=0.018, levels=4)       # rust patch mask
drip = _worldZ01(mat, -1500, 360, low=0.0, high=1400.0)       # rust runs DOWN -> invert
inv = _x(mat, unreal.MaterialExpressionOneMinus, -760, 380)
MEL.connect_material_expressions(drip, "", inv, "")
rustmask = _mul(mat, nrust, inv, -560, 80)                    # rust where noise AND low
paintc = _rgb(mat, (0.045, 0.060, 0.065), -800, -320)         # muted teal-grey industrial paint
rustc = _rgb(mat, (0.18, 0.075, 0.030), -800, -180)           # rust orange-brown
basecol = _lerp(mat, paintc, rustc, rustmask, -360, -240)
metal = _lerp(mat, _const(mat, 0.85, -560, 440), _const(mat, 0.05, -560, 520), rustmask, -360, 460)
rough = _lerp(mat, _const(mat, 0.45, -560, 620), _const(mat, 0.92, -560, 700), rustmask, -360, 640)
finish(mat, "M_RustMetal", [
    ("base", MEL.connect_material_property(basecol, "", unreal.MaterialProperty.MP_BASE_COLOR)),
    ("metal", MEL.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)),
    ("rough", MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)),
])

# ---- M_IndustrialWindow: warm grimy lit windows on a concrete frame (building facades) ----
mat = new_material("M_IndustrialWindow")
wt = _x(mat, unreal.MaterialExpressionTextureSample, -1100, 0)
wt.set_editor_property("texture", textures["win_a"])
wt.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
warm = _rgb(mat, (1.45, 0.82, 0.40), -1100, 240)              # warm sodium interior glow
emis0 = _mul(mat, wt, warm, -820, 60, apin="RGB")
# Lower window emissive so it doesn't blow out, and a VISIBLE concrete wall (was near-black ->
# buildings read as "see-through" voids). Now the wall is solid grey concrete WITH lit windows.
emis = _mul(mat, emis0, _const(mat, 1.25, -1100, 340), -620, 80)
nconc = _noise(mat, -1100, -320, scale=0.05, levels=3)
fbase = _lerp(mat, _rgb(mat, (0.105, 0.100, 0.094), -820, -360),
              _rgb(mat, (0.225, 0.215, 0.195), -820, -260), nconc, -560, -300)
frough = _const(mat, 0.72, -560, -180)
finish(mat, "M_IndustrialWindow", [
    ("emissive", MEL.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)),
    ("base", MEL.connect_material_property(fbase, "", unreal.MaterialProperty.MP_BASE_COLOR)),
    ("rough", MEL.connect_material_property(frough, "", unreal.MaterialProperty.MP_ROUGHNESS)),
])

# ---- M_Interior: warm industrial ROOM INTERIOR (concrete/plaster, NO windows) ----
# So the side rooms read as the inside of a building, not its window-covered exterior.
mat = new_material("M_Interior")
nin = _noise(mat, -1000, -100, scale=0.045, levels=3)
ibase = _lerp(mat, _rgb(mat, (0.115, 0.104, 0.092), -700, -260),
              _rgb(mat, (0.205, 0.188, 0.160), -700, -120), nin, -460, -200)
igr = _worldZ01(mat, -1400, 240, low=0.0, high=600.0)        # grimier toward the floor
igrimed = _lerp(mat, _rgb(mat, (0.55, 0.55, 0.57), -460, 120), _rgb(mat, (1.0, 1.0, 1.0), -460, 200),
                igr, -260, 140)
ibasecol = _mul(mat, ibase, igrimed, -100, -60)
irough = _const(mat, 0.82, -460, 320)
finish(mat, "M_Interior", [
    ("base", MEL.connect_material_property(ibasecol, "", unreal.MaterialProperty.MP_BASE_COLOR)),
    ("rough", MEL.connect_material_property(irough, "", unreal.MaterialProperty.MP_ROUGHNESS)),
])

# ---- M_StarNebula: a starfield + faint nebula for the sky dome (city floating in space) ----
# Unlit, two-sided (renders from inside the dome). Emissive = sparse white stars (thresholded
# high-freq noise) + a faint violet/teal nebula (low-freq noise). No textures.
mat = new_material("M_StarNebula")
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", True)
# Is Sky = True so the real-time-capture SkyLight captures the StarDome as the sky (F4 removed the
# SkyAtmosphere; without a sky the SkyLight errors + re-capture loops). Keeps the starry-space look.
try:
    mat.set_editor_property("is_sky", True)
except Exception as _e:
    unreal.log_warning(f"M_StarNebula is_sky not settable: {_e}")
# stars: high-freq noise -> (n - 0.90) * 4 -> clamp 0..1 = a SPARSE, dim mask (Adam: was too dense)
nstar = _noise(mat, -1200, -200, scale=2.6, levels=1)
ssub = _x(mat, unreal.MaterialExpressionSubtract, -980, -200)
MEL.connect_material_expressions(nstar, "", ssub, "A")
MEL.connect_material_expressions(_const(mat, 0.90, -1200, -60), "", ssub, "B")
sscl = _mul(mat, ssub, _const(mat, 4.0, -980, -60), -800, -200)
sclamp = _x(mat, unreal.MaterialExpressionClamp, -640, -200)
MEL.connect_material_expressions(sscl, "", sclamp, "")
star = _mul(mat, sclamp, _rgb(mat, (2.0, 2.1, 2.4), -640, -60), -460, -200)   # white-blue stars
# nebula: low-freq noise -> faint violet<->teal tint
nneb = _noise(mat, -1200, 260, scale=0.045, levels=4)
nneb2 = _noise(mat, -1200, 460, scale=0.02, levels=3)
nebtint = _lerp(mat, _rgb(mat, (0.060, 0.022, 0.090), -980, 320),
                _rgb(mat, (0.012, 0.055, 0.070), -980, 440), nneb2, -800, 380)
neb = _mul(mat, nneb, nebtint, -600, 320)                                     # faint nebula clouds
emis = _x(mat, unreal.MaterialExpressionAdd, -300, 60)
MEL.connect_material_expressions(star, "", emis, "A")
MEL.connect_material_expressions(neb, "", emis, "B")
finish(mat, "M_StarNebula", [
    ("emissive", MEL.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)),
])

# ---- ENEMY NEON SKINS: cheap UNLIT emissive tints so the low-level critters read against the dusk
# (Adam: the dark enemies need color). Applied to body slot 0 at spawn (dress/merge _tint_enemy).
for _ename, _ecol, _eglow in (("M_EnemyGlimmer", (0.20, 0.85, 1.00), 1.8),   # cool teal-cyan
                              ("M_EnemyRoly",    (1.10, 0.50, 0.16), 1.5),   # warm amber-rust
                              ("M_EnemyMoth",    (1.30, 0.95, 0.40), 2.3)):  # warm gold glow
    _em = new_material(_ename)
    _em.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    _ee = _mul(_em, _rgb(_em, _ecol, -600, 0), _const(_em, _eglow, -600, 200), -360, 60)
    finish(_em, _ename, [("emissive",
           MEL.connect_material_property(_ee, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR))])

print("GRITTY_MATERIALS_DONE")
print("CITY_MATERIALS_DONE")
