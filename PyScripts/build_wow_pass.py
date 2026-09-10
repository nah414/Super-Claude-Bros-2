"""WOW pass placement (Adam 2026-07-21): ember-mote drift volumes across the play
spaces (anchored to lantern clusters — sparks gather near kept-fire), and the aurora
returned as a DISTANT high band over the skyline (subtle, far from the stage).
Counts via log_warning so they surface in the commandlet summary.
Run: UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/build_wow_pass.py
     -unattended -nosplash -RenderOffscreen -nopause
"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_FAILED"
actors = list(eas.get_all_level_actors())


def lab(a):
    try:
        return a.get_actor_label()
    except Exception:
        return ""


# ---- clear any prior WOW actors (idempotent re-runs) ------------------------
for a in list(actors):
    if lab(a).startswith("WOW_"):
        eas.destroy_actor(a)
actors = list(eas.get_all_level_actors())

# ---- Ember drift volumes at well-spaced lantern anchors ---------------------
EMBER_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.EmberDrift")
lanterns = [a for a in actors if a.get_class().get_name() == "Lantern"]
picked = []
for a in lanterns:
    loc = a.get_actor_location()
    ok = True
    for p in picked:
        if ((loc.x - p.x) ** 2 + (loc.y - p.y) ** 2 + (loc.z - p.z) ** 2) ** 0.5 < 2600.0:
            ok = False
            break
    if ok:
        picked.append(loc)
    if len(picked) >= 8:
        break

placed = 0
for i, p in enumerate(picked):
    e = eas.spawn_actor_from_class(EMBER_CLASS, unreal.Vector(p.x, p.y, p.z + 350.0))
    try:
        e.set_editor_property("num_motes", 50)
        e.set_editor_property("extent", unreal.Vector(1500.0, 1500.0, 650.0))
    except Exception as ex:
        unreal.log_warning(f"EMBER_PROP_SKIP: {ex}")
    e.set_actor_label(f"WOW_EmberDrift_{i:02d}")
    placed += 1
unreal.log_warning(f"WOW ember_volumes_placed={placed} (of {len(lanterns)} lanterns)")

# ---- The distant aurora band: high over the skyline, far from the stage -----
mat = unreal.EditorAssetLibrary.load_asset("/Game/Art/CityMat/M_Aurora")
if mat:
    cyl = unreal.load_asset("/Engine/BasicShapes/Cylinder")
    ring = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(6000.0, 0.0, 11800.0))
    smc = ring.static_mesh_component
    smc.set_static_mesh(cyl)
    ring.set_actor_scale3d(unreal.Vector(640.0, 640.0, 34.0))   # r~32000, a thin far ribbon
    smc.set_material(0, mat)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for p, v in (("visible_in_ray_tracing", False), ("cast_shadow", False)):
        try:
            smc.set_editor_property(p, v)
        except Exception:
            pass
    ring.set_actor_label("WOW_AuroraBand")
    unreal.log_warning("WOW aurora_band=PLACED r~32000 z=11800 (distant + high)")
else:
    unreal.log_warning("WOW aurora SKIPPED - M_Aurora asset not found")

ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log_warning(f"WOW_SAVED={ok}")
