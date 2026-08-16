"""THE WATER KIT — shared material subgraph builders (Round 5, "The Water Reads").

Water is not a picture; the eye reads it as a set of STATES (the fourth-walk
study, root cause in one sentence): DEPTH (how much water am I looking
through), MOTION (layers at unequal speeds, patterns deforming as they
travel), CONTACT (banks, rocks, feet, plunge), AERATION (foam only where
energy demands it). Every builder here serves one of those states, so the
river, the falls, the pond — and every water in Worlds 1-6 after them — are
COMPOSITIONS of the same proven pieces instead of hand-wired one-offs.

House laws honored: DepthFade-in-unlit (round 2), Float4 MPC mask (round 3),
sway-only WPO amplitudes (the 8GB audit), Brightness War (emissives damped,
EV-clamp calibrated). Used by build_verdant_materials.py; import via
sys.path.append(this dir).
"""
import unreal

MEL = unreal.MaterialEditingLibrary


# ---------------------------------------------------------------- node atoms
def _const(mat, v, x, y):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, x, y)
    n.set_editor_property("r", v)
    return n


def _const3(mat, r, g, b, x, y):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, x, y)
    n.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    return n


def _mul(mat, a, b, x, y, a_out="", b_out=""):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, x, y)
    MEL.connect_material_expressions(a, a_out, n, "A")
    MEL.connect_material_expressions(b, b_out, n, "B")
    return n


def _add(mat, a, b, x, y, a_out="", b_out=""):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, x, y)
    MEL.connect_material_expressions(a, a_out, n, "A")
    MEL.connect_material_expressions(b, b_out, n, "B")
    return n


def _sub(mat, a, b, x, y, a_out="", b_out=""):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionSubtract, x, y)
    MEL.connect_material_expressions(a, a_out, n, "A")
    MEL.connect_material_expressions(b, b_out, n, "B")
    return n


def _sample(mat, texture, x, y):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, x, y)
    n.texture = texture
    n.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    return n


def _depth_fade(mat, x, y, dist):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionDepthFade, x, y)
    n.set_editor_property("fade_distance_default", dist)
    return n


def _panner(mat, x, y, sx, sy):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionPanner, x, y)
    n.set_editor_property("speed_x", sx)
    n.set_editor_property("speed_y", sy)
    return n


# ------------------------------------------------------- MOTION: the shear
def ripple_distort(mat, ripple_tex, x, y, s1=0.024, s2=0.016,
                   v1=0.22, v2=0.13, x2=0.045):
    # R6 (walk 5a: "vibrating, not flowing" — EL-007): the warp amplitudes and
    # speeds are DAMPED so oscillation stops dominating; the directional streak
    # layers now carry the current and the warp rides them as texture.
    """Two unequal-speed panners over the RG distortion field -> a 2-channel
    UV warp. ADD the result to any water UV so its pattern shears and wobbles
    as it travels — the ice-bar killer (EL-005: translation is not motion).
    Layer 2 runs ~0.6x layer 1 with a slight cross-flow angle and its own
    tiling so the two fields never phase-lock."""
    p1 = _panner(mat, x, y, 0.0, v1)
    r1 = _sample(mat, ripple_tex, x + 170, y)
    MEL.connect_material_expressions(p1, "", r1, "Coordinates")
    tc2 = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate,
                                         x - 150, y + 170)
    tc2.set_editor_property("u_tiling", 1.7)
    tc2.set_editor_property("v_tiling", 1.7)
    p2 = _panner(mat, x, y + 170, x2, v2)
    MEL.connect_material_expressions(tc2, "", p2, "Coordinate")
    r2 = _sample(mat, ripple_tex, x + 170, y + 170)
    MEL.connect_material_expressions(p2, "", r2, "Coordinates")
    half = _const(mat, 0.5, x + 330, y + 90)
    w1 = _mul(mat, _sub(mat, r1, half, x + 380, y, a_out="RG"),
              _const(mat, s1, x + 380, y + 70), x + 500, y + 20)
    w2 = _mul(mat, _sub(mat, r2, half, x + 380, y + 170, a_out="RG"),
              _const(mat, s2, x + 380, y + 240), x + 500, y + 190)
    return _add(mat, w1, w2, x + 620, y + 100)


def flowed_sample(mat, texture, distort, x, y, sx=0.0, sy=0.5,
                  u_tiling=1.0, v_tiling=1.0):
    """A texture sample whose UVs pan with the flow AND wobble with the ripple
    field. The mask says WHERE, the texture supplies MOTION (the Flow Law) —
    and the distortion supplies DEFORMATION (the round-5 addendum)."""
    tc = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate,
                                        x - 150, y)
    tc.set_editor_property("u_tiling", u_tiling)
    tc.set_editor_property("v_tiling", v_tiling)
    p = _panner(mat, x, y, sx, sy)
    MEL.connect_material_expressions(tc, "", p, "Coordinate")
    warped = _add(mat, p, distort, x + 130, y + 40)
    smp = _sample(mat, texture, x + 260, y)
    MEL.connect_material_expressions(warped, "", smp, "Coordinates")
    return smp


# --------------------------------------------------------- DEPTH: the ramp
def depth_ramp(mat, x, y, dist, shallow_rgb, deep_rgb):
    """Shallow -> deep color ramp on scene-depth-behind-surface (DepthFade
    computes SceneDepth - PixelDepth internally; proven in unlit translucency
    since round 2). Returns (color_lerp, depth_node) — depth_node is 0 at the
    waterline, 1 in the deeps: reuse it for opacity ramps and foam gating."""
    depth = _depth_fade(mat, x, y + 140, dist)
    lerp = MEL.create_material_expression(mat,
                                          unreal.MaterialExpressionLinearInterpolate,
                                          x + 320, y + 40)
    MEL.connect_material_expressions(
        _const3(mat, *shallow_rgb, x, y - 60), "", lerp, "A")
    MEL.connect_material_expressions(
        _const3(mat, *deep_rgb, x + 150, y - 60), "", lerp, "B")
    MEL.connect_material_expressions(depth, "", lerp, "Alpha")
    return lerp, depth


# ------------------------------------------------------ CONTACT: the shore
def shore_bands(mat, x, y, tight=55.0, feather=180.0):
    """Two inverse DepthFades: a thin bright contact band that hugs whatever
    the water touches (banks, rocks, feet — EL-004: water must touch its
    banks) and a wider faint feather. Multiply each by an advected foam
    texture so the band is lacy and alive, never a painted stripe."""
    b_tight = MEL.create_material_expression(mat, unreal.MaterialExpressionOneMinus,
                                             x + 170, y)
    MEL.connect_material_expressions(_depth_fade(mat, x, y, tight), "", b_tight, "")
    b_feather = MEL.create_material_expression(mat, unreal.MaterialExpressionOneMinus,
                                               x + 170, y + 150)
    MEL.connect_material_expressions(_depth_fade(mat, x, y + 150, feather), "",
                                     b_feather, "")
    return b_tight, b_feather


# ----------------------------------------------------- MOTION: the breathing
def bob_wpo(mat, x, y, amp1=1.8, amp2=1.4, f1=1.3, f2=2.1):
    """Two offset sine bobs, Z-only, ~3uu total — the surface silhouette is
    never a rigid plane. Sway-only: inside the 8GB WPO audit."""
    t = MEL.create_material_expression(mat, unreal.MaterialExpressionTime, x, y)
    wp = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition,
                                        x, y + 120)
    wx = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask,
                                        x + 130, y + 120)
    wx.set_editor_property("r", True)
    wx.set_editor_property("g", False)
    wx.set_editor_property("b", False)
    wx.set_editor_property("a", False)
    MEL.connect_material_expressions(wp, "", wx, "")
    wy = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask,
                                        x + 130, y + 200)
    wy.set_editor_property("r", False)
    wy.set_editor_property("g", True)
    wy.set_editor_property("b", False)
    wy.set_editor_property("a", False)
    MEL.connect_material_expressions(wp, "", wy, "")
    ph1 = _add(mat, _mul(mat, t, _const(mat, f1, x + 130, y - 60), x + 240, y - 30),
               _mul(mat, wx, _const(mat, 0.002, x + 240, y + 120), x + 350, y + 90),
               x + 460, y)
    s1 = MEL.create_material_expression(mat, unreal.MaterialExpressionSine, x + 560, y)
    MEL.connect_material_expressions(ph1, "", s1, "")
    ph2 = _add(mat, _mul(mat, t, _const(mat, f2, x + 130, y + 280), x + 240, y + 300),
               _mul(mat, wy, _const(mat, 0.0017, x + 240, y + 380), x + 350, y + 350),
               x + 460, y + 320)
    s2 = MEL.create_material_expression(mat, unreal.MaterialExpressionSine, x + 560, y + 320)
    MEL.connect_material_expressions(ph2, "", s2, "")
    z = _add(mat, _mul(mat, s1, _const(mat, amp1, x + 660, y + 40), x + 740, y),
             _mul(mat, s2, _const(mat, amp2, x + 660, y + 360), x + 740, y + 320),
             x + 850, y + 160)
    flat = MEL.create_material_expression(mat, unreal.MaterialExpressionAppendVector,
                                          x + 950, y + 100)
    MEL.connect_material_expressions(_const(mat, 0.0, x + 850, y + 40), "", flat, "A")
    MEL.connect_material_expressions(_const(mat, 0.0, x + 850, y + 70), "", flat, "B")
    wpo = MEL.create_material_expression(mat, unreal.MaterialExpressionAppendVector,
                                         x + 1050, y + 130)
    MEL.connect_material_expressions(flat, "", wpo, "A")
    MEL.connect_material_expressions(z, "", wpo, "B")
    return wpo


# ------------------------------------------------- DEPTH/LIGHT: the sky tint
def fresnel_sky(mat, x, y, sky_rgb=(0.55, 0.68, 0.78), exponent=4.0,
                base_fraction=0.02):
    """Grazing-angle sky tint — the stylized mirror for free (Adam's ruling:
    sky-tint fresnel, no cubemap). Add to emissive; strongest where the eye
    skims the surface, gone looking straight down."""
    fres = MEL.create_material_expression(mat, unreal.MaterialExpressionFresnel, x, y)
    fres.set_editor_property("exponent", exponent)
    fres.set_editor_property("base_reflect_fraction", base_fraction)
    return _mul(mat, fres, _const3(mat, *sky_rgb, x, y + 150), x + 150, y + 60)


def saturate(mat, node, x, y):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionSaturate, x, y)
    MEL.connect_material_expressions(node, "", n, "")
    return n


# ------------------- GEOMETRIC depth/contact (the -game-proof alternative)
# Round-5 finding: DepthFade reads ~zero scene thickness in -game runs on this
# engine build (editor viewports lie greener) — every DepthFade cue was
# vacuous on Adam's walks. These builders derive depth and shore from the
# authored geometry itself: the ribbon's cross-UV (0 at one skirt, 1 at the
# other, waterline near the edges) — view-independent, deterministic, and it
# wanders with the baked width sway exactly like the real waterline.
def _edge_prox(mat, x, y):
    """abs(uv.x - 0.5) * 2 -> 0 mid-channel, 1 at the skirts."""
    tc = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate,
                                        x, y)
    ux = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask,
                                        x + 130, y)
    ux.set_editor_property("r", True)
    ux.set_editor_property("g", False)
    ux.set_editor_property("b", False)
    ux.set_editor_property("a", False)
    MEL.connect_material_expressions(tc, "", ux, "")
    off = _sub(mat, ux, _const(mat, 0.5, x + 130, y + 80), x + 250, y)
    ab = MEL.create_material_expression(mat, unreal.MaterialExpressionAbs, x + 350, y)
    MEL.connect_material_expressions(off, "", ab, "")
    return _mul(mat, ab, _const(mat, 2.0, x + 350, y + 80), x + 460, y)


def _ramp(mat, node, lo, width, x, y):
    """saturate((node - lo) / width)"""
    d = _sub(mat, node, _const(mat, lo, x, y + 80), x + 110, y)
    dv = MEL.create_material_expression(mat, unreal.MaterialExpressionDivide, x + 220, y)
    MEL.connect_material_expressions(d, "", dv, "A")
    MEL.connect_material_expressions(_const(mat, width, x + 110, y + 80), "", dv, "B")
    return saturate(mat, dv, x + 330, y)


def uv_depth_ramp(mat, x, y, shallow_rgb, deep_rgb, waterline=1.0, span=0.45):
    """Depth from the channel cross-section: 1 mid-channel, 0 at the visible
    waterline (edge_prox ~0.86 at mean width). Returns (color_lerp, depth)."""
    ep = _edge_prox(mat, x, y)
    inv = _sub(mat, _const(mat, waterline, x + 590, y + 90), ep, x + 700, y)
    dv = MEL.create_material_expression(mat, unreal.MaterialExpressionDivide, x + 800, y)
    MEL.connect_material_expressions(inv, "", dv, "A")
    MEL.connect_material_expressions(_const(mat, span, x + 700, y + 90), "", dv, "B")
    depth = saturate(mat, dv, x + 900, y)
    lerp = MEL.create_material_expression(
        mat, unreal.MaterialExpressionLinearInterpolate, x + 1030, y)
    MEL.connect_material_expressions(_const3(mat, *shallow_rgb, x + 900, y - 90), "",
                                     lerp, "A")
    MEL.connect_material_expressions(_const3(mat, *deep_rgb, x + 1030, y - 90), "",
                                     lerp, "B")
    MEL.connect_material_expressions(depth, "", lerp, "Alpha")
    return lerp, depth


def uv_shore_bands(mat, x, y, tight_lo=0.85, tight_w=0.10,
                   feather_lo=0.78, feather_w=0.18):
    """Contact bands from the cross-UV: the tight band rises 0->1 approaching
    the waterline (and stays lit into the tuck, which terrain hides); the
    feather leads it. Multiply by advected foam so the band lives."""
    ep = _edge_prox(mat, x, y)
    b_tight = _ramp(mat, ep, tight_lo, tight_w, x + 600, y)
    b_feather = _ramp(mat, ep, feather_lo, feather_w, x + 600, y + 170)
    return b_tight, b_feather


def _const2(mat, a, b, x, y):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant2Vector,
                                       x, y)
    n.set_editor_property("r", a)
    n.set_editor_property("g", b)
    return n


def rapids_wakes(mat, rapids, x, y, length=900.0, w0=100.0, w1=220.0):
    """AERATION where energy demands it: analytic V-wakes opening downstream
    of each rapids stone, computed from the field JSON's world coordinates
    (the round-3 vertex-color bake never survived the FBX chain — UE read
    white everywhere, the eternal-lace bug; geometry-derived masks cannot be
    lost in transit). Returns a 0..1 mask; multiply by advected foam."""
    wp = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition,
                                        x, y - 120)
    wpRG = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask,
                                          x + 130, y - 120)
    wpRG.set_editor_property("r", True)
    wpRG.set_editor_property("g", True)
    wpRG.set_editor_property("b", False)
    wpRG.set_editor_property("a", False)
    MEL.connect_material_expressions(wp, "", wpRG, "")
    total = None
    for i, rp in enumerate(rapids):
        yy = y + i * 300
        d = _sub(mat, wpRG, _const2(mat, rp["x"], rp["y"], x, yy), x + 260, yy)
        dot_a = MEL.create_material_expression(
            mat, unreal.MaterialExpressionDotProduct, x + 400, yy)
        MEL.connect_material_expressions(d, "", dot_a, "A")
        MEL.connect_material_expressions(
            _const2(mat, rp["tx"], rp["ty"], x + 260, yy + 90), "", dot_a, "B")
        dot_l = MEL.create_material_expression(
            mat, unreal.MaterialExpressionDotProduct, x + 400, yy + 150)
        MEL.connect_material_expressions(d, "", dot_l, "A")
        MEL.connect_material_expressions(
            _const2(mat, -rp["ty"], rp["tx"], x + 260, yy + 200), "", dot_l, "B")
        lat = MEL.create_material_expression(mat, unreal.MaterialExpressionAbs,
                                             x + 520, yy + 150)
        MEL.connect_material_expressions(dot_l, "", lat, "")
        gate = _ramp(mat, dot_a, 0.0, 60.0, x + 540, yy - 60)
        fade_raw = _sub(mat, _const(mat, 1.0, x + 540, yy + 40),
                        _mul(mat, dot_a, _const(mat, 1.0 / length, x + 540, yy + 90),
                             x + 660, yy + 60), x + 780, yy + 30)
        fade = saturate(mat, fade_raw, x + 880, yy + 30)
        half_w = _add(mat, _const(mat, w0, x + 660, yy + 190),
                      _mul(mat, _sub(mat, _const(mat, 1.0, x + 540, yy + 250),
                                     fade, x + 640, yy + 250),
                           _const(mat, w1, x + 640, yy + 320), x + 760, yy + 260),
                      x + 880, yy + 210)
        lat_div = MEL.create_material_expression(
            mat, unreal.MaterialExpressionDivide, x + 1000, yy + 170)
        MEL.connect_material_expressions(lat, "", lat_div, "A")
        MEL.connect_material_expressions(half_w, "", lat_div, "B")
        lat_term = saturate(mat, _sub(mat, _const(mat, 1.0, x + 1000, yy + 90),
                                      lat_div, x + 1110, yy + 130),
                            x + 1220, yy + 130)
        wake_i = _mul(mat, _mul(mat, gate, fade, x + 1000, yy - 20),
                      lat_term, x + 1330, yy + 40)
        total = wake_i if total is None else _add(mat, total, wake_i,
                                                  x + 1450, yy + 20)
    return saturate(mat, total, x + 1570, y + 40)
