"""Neon City night pass 2 (Adam 2026-07-21, round-2 screenshots):
  1. DARKER: exposure lock -1.4 -> -1.8 + the glade cinematic stack (grain/vignette/fringe).
  2. FESTIVAL BLOWOUTS: clamp any non-lantern light whose intensity floods building walls.
  3. SPIRAL TORCHES REDESIGNED: delete every remaining spire torch; place ONE short
     (0.45-scale, so it can never poke through the loop above) bright lantern per landing,
     tucked toward the spire core, base snapped to the surface.
  4. ATMOSPHERE: volumetric fog + moonlight scattering — the missing air and depth.
Counts are logged via log_warning so they surface in the commandlet summary.
Run: UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/fix_neon_night_pass2.py
     -unattended -nosplash -RenderOffscreen -nopause
"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_FAILED"
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = list(eas.get_all_level_actors())


def lab(a):
    try:
        return a.get_actor_label()
    except Exception:
        return ""


def setp(a, names, value):
    for n in names:
        try:
            a.set_editor_property(n, value)
            return True
        except Exception:
            continue
    return False


def ground_at(x, y, z_top, ignore):
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, y, z_top), unreal.Vector(x, y, z_top - 700.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore,
            unreal.DrawDebugTrace.NONE, True)
        if hit:
            t = hit.to_tuple()
            if t[0]:
                return t[5]
    except Exception:
        pass
    return None


# ---- 1. Deeper night + cinematic stack --------------------------------------
for a in actors:
    if isinstance(a, unreal.PostProcessVolume):
        pps = a.get_editor_property("settings")
        for prop, val in (
            ("override_auto_exposure_min_brightness", True),
            ("auto_exposure_min_brightness", -1.8),
            ("override_auto_exposure_max_brightness", True),
            ("auto_exposure_max_brightness", -1.8),
            ("override_bloom_threshold", True),
            ("bloom_threshold", 2.0),
            ("override_bloom_intensity", True),
            ("bloom_intensity", 0.8),
            ("override_lens_flare_intensity", True),
            ("lens_flare_intensity", 0.25),
            ("override_film_grain_intensity", True),
            ("film_grain_intensity", 0.12),
            ("override_vignette_intensity", True),
            ("vignette_intensity", 0.35),
            ("override_scene_fringe_intensity", True),
            ("scene_fringe_intensity", 0.25),
        ):
            try:
                pps.set_editor_property(prop, val)
            except Exception as e:
                unreal.log_warning(f"PPS_SKIP {prop}: {e}")
        a.set_editor_property("settings", pps)
        a.set_editor_property("unbound", True)
        unreal.log_warning(f"NIGHT2 ppv={lab(a)} exposure=-1.8 + cinematic stack")
        break

# ---- 2. Clamp the festival blow-out lights (never lantern flames) -----------
clamped = 0
LIGHT_CLASSES = (unreal.PointLightComponent, unreal.SpotLightComponent, unreal.RectLightComponent)
for a in actors:
    if a.get_class().get_name() == "Lantern":
        continue   # lantern flames are the Color Law — untouched
    for cls in LIGHT_CLASSES:
        try:
            comps = a.get_components_by_class(cls)
        except Exception:
            comps = []
        for c in comps:
            try:
                cur = float(c.get_editor_property("intensity"))
                if cur > 4000.0:
                    c.set_editor_property("intensity", cur * 0.35)
                    clamped += 1
                    unreal.log_warning(
                        f"NIGHT2 clamp {lab(a)}/{c.get_name()}: {cur:.0f} -> {cur * 0.35:.0f}")
            except Exception:
                continue
unreal.log_warning(f"NIGHT2 lights_clamped={clamped}")

# ---- 3. Spiral torches: wipe and re-lay -------------------------------------
LANTERN_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.Lantern")
core = None
for a in actors:
    if "LC_SpireCore" in lab(a):
        core = a.get_actor_location()
        break

removed = 0
for a in list(actors):
    lb = lab(a)
    if "LC_Lantern_spire" in lb:      # spire_* AND spiremid_*
        eas.destroy_actor(a)
        removed += 1
unreal.log_warning(f"NIGHT2 old_spire_torches_removed={removed}")

placed = 0
if core is not None:
    landings = [a for a in eas.get_all_level_actors() if "LC_SpiralLand_" in lab(a)]
    for land in landings:
        loc = land.get_actor_location()
        d = unreal.Vector(core.x - loc.x, core.y - loc.y, 0.0)
        dist = max((d.x ** 2 + d.y ** 2) ** 0.5, 1.0)
        # Tuck toward the spire core, but stay ON the landing (500-wide -> 190 in).
        tx = loc.x + d.x / dist * 190.0
        ty = loc.y + d.y / dist * 190.0
        gp = ground_at(tx, ty, loc.z + 150.0, [land])
        tz = (gp.z + 2.0) if gp is not None else (loc.z + 22.0)
        t = eas.spawn_actor_from_class(LANTERN_CLASS, unreal.Vector(tx, ty, tz))
        setp(t, ["lit_intensity", "LitIntensity"], 1800.0)
        setp(t, ["lit_radius", "LitRadius"], 1150.0)
        setp(t, ["relight_by_hero_radius", "RelightByHeroRadius"], 300.0)
        setp(t, ["auto_relight_seconds", "AutoRelightSeconds"], 9.0)
        t.set_actor_scale3d(unreal.Vector(0.45, 0.45, 0.45))   # SHORT: never pierces the loop above
        t.set_actor_label(f"LC_Lantern_spireB_{placed:02d}")
        placed += 1
else:
    unreal.log_warning("NIGHT2 SpireCore not found - torch relay skipped")
unreal.log_warning(f"NIGHT2 new_spiral_torches_placed={placed}")

# ---- 4. Atmosphere: volumetric fog + moon scattering ------------------------
fog_done, moon_done = False, False
for a in actors:
    try:
        fogc = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
    except Exception:
        fogc = None
    if fogc and not fog_done:
        for prop, val in (
            ("volumetric_fog", True),
            ("volumetric_fog_scattering_distribution", 0.35),
            ("volumetric_fog_extinction_scale", 1.2),
            ("fog_density", 0.012),
            ("fog_height_falloff", 0.22),
        ):
            try:
                fogc.set_editor_property(prop, val)
            except Exception as e:
                unreal.log_warning(f"FOG_SKIP {prop}: {e}")
        fog_done = True
        unreal.log_warning(f"NIGHT2 volumetric_fog=ON via {lab(a)}")
    try:
        moonc = a.get_component_by_class(unreal.DirectionalLightComponent)
    except Exception:
        moonc = None
    if moonc and not moon_done:
        try:
            moonc.set_editor_property("volumetric_scattering_intensity", 2.5)
            moon_done = True
            unreal.log_warning(f"NIGHT2 moon_shafts=ON via {lab(a)}")
        except Exception as e:
            unreal.log_warning(f"MOON_SKIP: {e}")

ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log_warning(f"NIGHT2_SAVED={ok}")
