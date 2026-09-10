"""Read-only check of the night pass — logs via unreal.log so the commandlet shows it."""
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


def ground(a, x, y, z_top):
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, y, z_top), unreal.Vector(x, y, z_top - 600.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [a],
            unreal.DrawDebugTrace.NONE, True)
        if hit:
            t = hit.to_tuple()
            if t[0]:
                return t[5]
    except Exception:
        pass
    return None


glim_total, glim_sunk, glim_float = 0, 0, 0
for a in actors:
    if a.get_class().get_name() != "GlimmerEnemy":
        continue
    glim_total += 1
    loc = a.get_actor_location()
    gp = ground(a, loc.x, loc.y, loc.z + 300.0)
    if gp is None:
        continue
    off = loc.z - (gp.z + 41.0)
    if off < -8.0:
        glim_sunk += 1
    elif off > 25.0:
        glim_float += 1
unreal.log(f"VERIFY glimmers={glim_total} still_sunk={glim_sunk} floating={glim_float}")

lant_total, lant_float, crown_near = 0, 0, 0
crown = None
for a in actors:
    if "LC_Lantern_FIRST" in lab(a):
        crown = a.get_actor_location()
for a in actors:
    lb = lab(a)
    if "LC_Lantern_" not in lb or "FIRST" in lb:
        continue
    lant_total += 1
    loc = a.get_actor_location()
    gp = ground(a, loc.x, loc.y, loc.z + 60.0)
    if gp is not None and (loc.z - gp.z) > 15.0:
        lant_float += 1
    if crown is not None and "spire" in lb:
        d2 = (loc.x - crown.x) ** 2 + (loc.y - crown.y) ** 2
        if d2 ** 0.5 <= 800.0 and abs(loc.z - crown.z) <= 500.0:
            crown_near += 1
unreal.log(f"VERIFY lanterns={lant_total} still_floating={lant_float} still_crowding_crown={crown_near}")

ppv_report = "none"
for a in actors:
    if isinstance(a, unreal.PostProcessVolume):
        s = a.get_editor_property("settings")
        try:
            ppv_report = (f"{lab(a)} minB={s.get_editor_property('auto_exposure_min_brightness')} "
                          f"maxB={s.get_editor_property('auto_exposure_max_brightness')} "
                          f"bloom={s.get_editor_property('bloom_intensity')}")
        except Exception as e:
            ppv_report = f"{lab(a)} read_fail {e}"
        break
unreal.log(f"VERIFY ppv: {ppv_report}")

tagged = sum(1 for a in actors if unreal.Name("NoClimb") in list(a.get_editor_property("tags")))
unreal.log(f"VERIFY noclimb_tagged={tagged}")
