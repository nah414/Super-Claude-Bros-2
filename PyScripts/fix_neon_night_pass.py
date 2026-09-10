"""Neon City night pass (Adam 2026-07-21, from six playtest screenshots):
  1. RE-GROUND every Glimmer: they spawned half-sunk in the spiral ramps/landings.
  2. LOWER the floating torches: LC_Lantern_spire*/spiremid* spawned ~50uu above the
     walkway; snap each pole base onto the surface below it.
  3. CLEAN THE CROWN: delete the torch cluster crowding the FIRST beacon + flagpole.
  4. DARKEN the night: lock exposure low + tame bloom/flares, so the sky, neon and
     torches DO the lighting instead of an over-lit foreground.
  5. TAG the world's edges NoClimb (boundary walls, cliffs, caps, sky shells) for the
     hero's new boundary law (SparkHeroCharacter::TryStartClimb).
Run with a render device (map save):
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/fix_neon_night_pass.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_NEONCITY_FAILED"
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = list(eas.get_all_level_actors())


def label_of(a):
    try:
        return a.get_actor_label()
    except Exception:
        return ""


def ground_under(a, x, y, z_top, depth=600.0):
    """Impact point of a straight-down visibility trace, or None."""
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, y, z_top), unreal.Vector(x, y, z_top - depth),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [a],
            unreal.DrawDebugTrace.NONE, True)
        if hit:
            t = hit.to_tuple()
            if t[0]:                      # blocking_hit
                return t[5]               # impact_point
    except Exception as e:
        unreal.log_warning(f"TRACE_FAIL {label_of(a)}: {e}")
    return None


# ---- 1. Re-ground the Glimmers (half-sunk on the spiral) --------------------
reground = 0
for a in actors:
    if a.get_class().get_name() != "GlimmerEnemy":
        continue
    loc = a.get_actor_location()
    gp = ground_under(a, loc.x, loc.y, loc.z + 300.0)
    if gp is None:
        continue
    want_z = gp.z + 41.0                  # capsule half-height 40 + settle margin
    if abs(loc.z - want_z) > 4.0:
        a.set_actor_location(unreal.Vector(loc.x, loc.y, want_z), False, False)
        reground += 1
print(f"GLIMMERS_REGROUNDED: {reground}")

# ---- Locate the crown (the FIRST beacon) for the cleanup radius -------------
crown = None
for a in actors:
    if "LC_Lantern_FIRST" in label_of(a):
        crown = a.get_actor_location()
        break

# ---- 2 + 3. Torches: snap the floaters down; delete the crown crowders ------
lowered, deleted = 0, 0
for a in actors:
    lb = label_of(a)
    if "LC_Lantern_" not in lb or "FIRST" in lb:
        continue
    loc = a.get_actor_location()
    # Crown crowders: any spire torch within 800uu (XY) + 500uu (Z) of the beacon goes.
    if crown is not None and ("spire" in lb):
        dx, dy, dz = loc.x - crown.x, loc.y - crown.y, loc.z - crown.z
        if (dx * dx + dy * dy) ** 0.5 <= 800.0 and abs(dz) <= 500.0:
            eas.destroy_actor(a)
            deleted += 1
            continue
    # Floaters: pole base hovering >15uu above the surface below -> set it down.
    gp = ground_under(a, loc.x, loc.y, loc.z + 60.0)
    if gp is not None and (loc.z - gp.z) > 15.0:
        a.set_actor_location(unreal.Vector(loc.x, loc.y, gp.z + 2.0), False, False)
        lowered += 1
print(f"TORCHES_LOWERED: {lowered}  CROWN_TORCHES_DELETED: {deleted}")

# ---- 4. The night tint: exposure lock + tamed bloom/flares ------------------
ppv = None
for a in actors:
    if isinstance(a, unreal.PostProcessVolume):
        ppv = a
        break
if ppv is None:
    ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    ppv.set_actor_label("PP_NeonNight")
try:
    ppv.set_editor_property("unbound", True)
    pps = ppv.get_editor_property("settings")
    for prop, val in (
        # LOCK the eye DARK: the glade trick — auto-exposure can't re-brighten the
        # night. Neon windows, torch flames and the star sky now carry the scene.
        ("override_auto_exposure_min_brightness", True),
        ("auto_exposure_min_brightness", -1.4),
        ("override_auto_exposure_max_brightness", True),
        ("auto_exposure_max_brightness", -1.4),
        # Only genuinely HOT pixels bloom, and gently — kills the nuclear flares.
        ("override_bloom_threshold", True),
        ("bloom_threshold", 1.8),
        ("override_bloom_intensity", True),
        ("bloom_intensity", 0.9),
        ("override_lens_flare_intensity", True),
        ("lens_flare_intensity", 0.35),
    ):
        try:
            pps.set_editor_property(prop, val)
        except Exception as e:
            unreal.log_warning(f"PPS_SKIP {prop}: {e}")
    ppv.set_editor_property("settings", pps)
    print("NIGHT_TINT: exposure locked -1.4, bloom 0.9/thr 1.8, flares 0.35")
except Exception as e:
    unreal.log_warning(f"PPV_FAIL: {e}")

# ---- Dim the ambient skylight so shadowed streets read as NIGHT -------------
for a in actors:
    if "skylight" in label_of(a).lower():
        try:
            comp = a.get_component_by_class(unreal.SkyLightComponent)
            if comp:
                cur = comp.get_editor_property("intensity")
                comp.set_editor_property("intensity", cur * 0.6)
                print(f"SKYLIGHT_DIMMED: {label_of(a)} {cur:.2f} -> {cur * 0.6:.2f}")
        except Exception as e:
            unreal.log_warning(f"SKYLIGHT_SKIP {label_of(a)}: {e}")

# ---- 5. NoClimb tags on the world's edges -----------------------------------
EDGE_KEYS = ("boundary", "cliffw", "cliffe", "_caps", "_capn", "skydome", "skysphere", "sky_dome", "dome")
tagged = 0
noclimb = unreal.Name("NoClimb")
for a in actors:
    lb = label_of(a).lower()
    if not any(k in lb for k in EDGE_KEYS):
        continue
    try:
        tags = list(a.get_editor_property("tags"))
        if noclimb not in tags:
            tags.append(noclimb)
            a.set_editor_property("tags", tags)
            tagged += 1
    except Exception as e:
        unreal.log_warning(f"TAG_SKIP {label_of(a)}: {e}")
print(f"NOCLIMB_TAGGED: {tagged}")

# ---- Save -------------------------------------------------------------------
ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
print(f"NIGHT_PASS_SAVED: {ok}")
