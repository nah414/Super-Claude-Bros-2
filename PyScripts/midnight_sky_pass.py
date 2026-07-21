"""Midnight sky pass (Adam 2026-07-21, bedtime round):
  1. KILL THE STREAKS: delete WOW_AuroraBand — its curtains read as sky-wide white
     beams from below, washing walls and striping across the moon. Gone.
  2. MAKE THE FOG REAL: SpaceFog reconfigured as a visible ground-hugging city haze
     (it was tuned so subtle it vanished).
  3. SEAT THE SKY: retune the three celestial materials (softer tints so the Meshy
     surface detail shows, deeper relief shading) and give each body an additive
     fresnel GLOW HALO — the planet/moons become luminous objects IN the sky
     instead of stickers on the star dome.
  4. FOREGROUND: exposure -1.8 -> -2.0 (the glow does the lighting).
Run: UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/midnight_sky_pass.py
     -unattended -nosplash -RenderOffscreen -nopause
"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_FAILED"
actors = list(eas.get_all_level_actors())


def lab(a):
    try:
        return a.get_actor_label()
    except Exception:
        return ""


# ---- 1. The streaks: delete the aurora band ---------------------------------
killed = 0
for a in list(actors):
    if lab(a) in ("WOW_AuroraBand", "AuroraRing"):
        eas.destroy_actor(a)
        killed += 1
unreal.log_warning(f"MID streaks_removed={killed}")
actors = list(eas.get_all_level_actors())

# ---- 2. Visible city haze ----------------------------------------------------
for a in actors:
    try:
        fogc = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
    except Exception:
        fogc = None
    if not fogc:
        continue
    loc = a.get_actor_location()
    a.set_actor_location(unreal.Vector(loc.x, loc.y, 150.0), False, False)
    for prop, val in (
        ("fog_density", 0.02),
        ("fog_height_falloff", 0.03),
        ("start_distance", 500.0),
        ("fog_max_opacity", 0.85),
        ("enable_volumetric_fog", True),
        ("volumetric_fog_scattering_distribution", 0.4),
        ("volumetric_fog_extinction_scale", 1.4),
    ):
        try:
            fogc.set_editor_property(prop, val)
        except Exception as e:
            unreal.log_warning(f"MID fog_skip {prop}: {e}")
    unreal.log_warning(f"MID fog=VISIBLE ({lab(a)}: z150, density .02, falloff .03)")
    break

# ---- 3a. Celestial retune: softer tints, deeper relief ----------------------
SUN = (0.45, 0.18, 0.88)
TUNE = {
    "moon_large_red":  ((1.00, 0.62, 0.50), 0.50),
    "planet_gasgiant": ((1.00, 0.95, 0.88), 1.00),
    "moon_small_pale": ((0.50, 0.46, 0.44), 0.55),
}


def rebuild(body, tint, bright):
    bdir = f"/Game/Art/Celestial/{body}"
    mat = EAL.load_asset(f"{bdir}/M_{body}_lit")
    base = EAL.load_asset(f"{bdir}/T_{body}_base4k")
    norm = EAL.load_asset(f"{bdir}/T_{body}_normal4k")
    if not (mat and base and norm):
        unreal.log_warning(f"MID celestial_skip {body}")
        return
    MEL.delete_all_material_expressions(mat)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -700, -60)
    ts.set_editor_property("texture", base)
    ns = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -700, 220)
    ns.set_editor_property("texture", norm)
    try:
        ns.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    except Exception:
        pass
    sun = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, 420)
    sun.set_editor_property("constant", unreal.LinearColor(SUN[0], SUN[1], SUN[2], 1.0))
    dp = MEL.create_material_expression(mat, unreal.MaterialExpressionDotProduct, -480, 300)
    MEL.connect_material_expressions(ns, "", dp, "A")
    MEL.connect_material_expressions(sun, "", dp, "B")
    cl = MEL.create_material_expression(mat, unreal.MaterialExpressionClamp, -360, 300)
    MEL.connect_material_expressions(dp, "", cl, "")
    k = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -360, 400)
    k.set_editor_property("r", 0.85)   # deeper relief than round 1 (0.70)
    m1 = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -240, 330)
    MEL.connect_material_expressions(cl, "", m1, "A")
    MEL.connect_material_expressions(k, "", m1, "B")
    k2 = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -240, 430)
    k2.set_editor_property("r", 0.15)
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
    unreal.log_warning(f"MID celestial_retuned {body}")


for body, (tint, bright) in TUNE.items():
    rebuild(body, tint, bright)

# ---- 3b. Glow halos: the bodies join the sky --------------------------------
HALO = {
    "moon_large_red":  ((1.00, 0.34, 0.20), 1.1),
    "planet_gasgiant": ((1.00, 0.82, 0.55), 0.8),
    "moon_small_pale": ((0.45, 0.45, 0.55), 0.45),
}


def halo_mat(body, color, strength):
    name = f"M_halo_{body}"
    dest = f"/Game/Art/Celestial/{body}"
    path = f"{dest}/{name}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    mat = tools.create_asset(name, dest, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property("two_sided", True)
    fr = MEL.create_material_expression(mat, unreal.MaterialExpressionFresnel, -500, 100)
    fr.set_editor_property("exponent", 2.6)
    col = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -500, -80)
    col.set_editor_property("constant",
                            unreal.LinearColor(color[0] * strength, color[1] * strength, color[2] * strength, 1.0))
    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -260, 0)
    MEL.connect_material_expressions(col, "", mul, "A")
    MEL.connect_material_expressions(fr, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    return mat


# clear old halos, then place fresh ones on every celestial body in the map
for a in list(actors):
    if lab(a).startswith("WOW_Halo_"):
        eas.destroy_actor(a)
sphere = unreal.load_asset("/Engine/BasicShapes/Sphere")
halos = 0
for a in eas.get_all_level_actors():
    try:
        smc = a.static_mesh_component if isinstance(a, unreal.StaticMeshActor) else None
        sm = smc.static_mesh if smc else None
    except Exception:
        sm = None
    if not sm:
        continue
    p = sm.get_path_name()
    body = next((b for b in HALO if f"/Celestial/{b}/" in p), None)
    if body is None:
        continue
    color, strength = HALO[body]
    origin, extent = a.get_actor_bounds(False)
    radius = max(extent.x, extent.y, extent.z)
    h = eas.spawn_actor_from_class(unreal.StaticMeshActor, origin)
    h.static_mesh_component.set_static_mesh(sphere)
    h.set_actor_scale3d(unreal.Vector(radius * 1.16 / 50.0, radius * 1.16 / 50.0, radius * 1.16 / 50.0))
    h.static_mesh_component.set_material(0, halo_mat(body, color, strength))
    h.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for prop, val in (("cast_shadow", False), ("visible_in_ray_tracing", False)):
        try:
            h.static_mesh_component.set_editor_property(prop, val)
        except Exception:
            pass
    h.set_actor_label(f"WOW_Halo_{body}_{halos}")
    halos += 1
unreal.log_warning(f"MID halos_placed={halos}")

# ---- 4. Foreground: one notch deeper ----------------------------------------
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.PostProcessVolume):
        pps = a.get_editor_property("settings")
        for prop, val in (("auto_exposure_min_brightness", -2.0),
                          ("auto_exposure_max_brightness", -2.0)):
            try:
                pps.set_editor_property(prop, val)
            except Exception as e:
                unreal.log_warning(f"MID pps_skip {prop}: {e}")
        a.set_editor_property("settings", pps)
        unreal.log_warning("MID exposure=-2.0")
        break

ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log_warning(f"MID_SAVED={ok}")
