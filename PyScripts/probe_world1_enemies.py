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

# --- the World-1 first boss: Shellback Alpha, dormant at the spiral base ---
bosses = [a for a in eas.get_all_level_actors() if a.get_actor_label().startswith("Boss_ShellbackAlpha_W1")]
boss_ok = False
if len(bosses) == 1:
    b = bosses[0]
    bl = b.get_actor_location()
    try:
        aggro = b.get_editor_property("AggroRadius")
    except Exception:
        aggro = -1.0
    near_base = abs(bl.x - 10300) < 500 and abs(bl.y + 1600) < 500 and abs(bl.z - 95) < 500
    boss_ok = near_base and abs(aggro - 1400.0) < 1.0
    print(f"  boss: 1x Boss_ShellbackAlpha_W1 at ({bl.x:.0f},{bl.y:.0f},{bl.z:.0f}) AggroRadius={aggro:.0f} "
          f"near_base={near_base}")
else:
    print(f"  boss: FAIL expected 1 Boss_ShellbackAlpha_W1, found {len(bosses)}")

ok = (total == 40 and by_type.get("Glimmer") == 22 and by_type.get("Roly") == 12
      and by_type.get("FlitMoth") == 6 and culled_ok == total and tinted_ok == total and boss_ok)
print("W1_ENEMY_PROBE: " + ("PASS" if ok else "FAIL"))
print("W1_ENEMY_PROBE_DONE")

# The UE headless stdout log is UTF-16 with Python print() bytes mixed in — unreliable to grep.
# Write a clean single-line UTF-8 verdict that the agent can Read directly.
import os as _os
_bd = "none"
if len(bosses) == 1:
    _bd = f"at({bl.x:.0f},{bl.y:.0f},{bl.z:.0f}) AggroRadius={aggro:.0f}"
_verdict = (f"total={total} by_type={by_type} culled={culled_ok}/{total} tinted={tinted_ok}/{total} "
            f"moth_shadow_off={moth_shadow_off} boss={len(bosses)} {_bd} boss_ok={boss_ok} :: "
            + ("PASS" if ok else "FAIL"))
with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_world1_probe_result.txt"),
          "w", encoding="utf-8") as _fh:
    _fh.write(_verdict + "\n")
