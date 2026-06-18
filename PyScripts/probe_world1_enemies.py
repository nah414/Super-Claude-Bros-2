"""Read-only census of the 25 World-1 enemies: total, by type, by zone, + confirm the anti-lag
config landed (mesh draw-distance cull + shadowless moth lights). Run -RenderOffscreen (the actors'
components need render state to introspect cleanly)."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity")

by_type, zones = {}, {"street": 0, "siderooms": 0, "canyon": 0}
culled_ok, moth_shadow_off = 0, 0
enemies = [a for a in eas.get_all_level_actors() if a.get_actor_label().startswith("Enemy_")]

for a in enemies:
    kind = a.get_actor_label().split("_")[1]
    by_type[kind] = by_type.get(kind, 0) + 1
    loc = a.get_actor_location()
    if loc.x > 9700:
        zones["canyon"] += 1
    elif abs(loc.y) > 1200:
        zones["siderooms"] += 1
    else:
        zones["street"] += 1
    # anti-lag spot-check
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        try:
            if c.get_editor_property("ld_max_draw_distance") > 0:
                culled_ok += 1
                break
        except Exception:
            pass
    if kind == "FlitMoth":
        for lt in a.get_components_by_class(unreal.PointLightComponent):
            try:
                if not lt.get_editor_property("cast_shadows"):
                    moth_shadow_off += 1
            except Exception:
                pass

# colored-skin spot-check: body slot-0 material should be one of the M_Enemy* tints
tinted_ok = 0
for a in enemies:
    for sm in a.get_components_by_class(unreal.StaticMeshComponent):
        if "Eye" in sm.get_name():
            continue
        m = sm.get_material(0)
        if m and m.get_name().startswith("M_Enemy"):
            tinted_ok += 1
        break

total = len(enemies)
print(f"W1_ENEMY_PROBE total={total} by_type={by_type} zones={zones}")
print(f"  anti-lag: draw-cull set on {culled_ok}/{total}; moth lights shadow-off {moth_shadow_off}")
print(f"  colored skin (M_Enemy* on body slot0): {tinted_ok}/{total}")
ok = (total == 40 and by_type.get("Glimmer") == 22 and by_type.get("Roly") == 12
      and by_type.get("FlitMoth") == 6 and culled_ok == total and tinted_ok == total)
print("W1_ENEMY_PROBE: " + ("PASS" if ok else "FAIL"))
print("W1_ENEMY_PROBE_DONE")
