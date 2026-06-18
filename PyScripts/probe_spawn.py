"""Is there solid (colliding) floor under the PlayerStart? If not, the hero falls past
RespawnBelowZ(-2000), respawns at the spawn (still over the void), and falls again = the
~2-second respawn loop. Read-only. Run -RenderOffscreen (collision bounds)."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity")

actors = eas.get_all_level_actors()
starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
print(f"PLAYERSTART_COUNT: {len(starts)}")

for ps in starts:
    loc = ps.get_actor_location()
    sx, sy, sz = loc.x, loc.y, loc.z
    print(f"PLAYERSTART '{ps.get_actor_label()}' at ({sx:.0f},{sy:.0f},{sz:.0f})")
    best = None
    cover = []
    for a in actors:
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        try:
            origin, ext = a.get_actor_bounds(True)   # colliding components only
        except Exception:
            continue
        if ext.x < 1.0 and ext.y < 1.0 and ext.z < 1.0:
            continue                                  # no collision geometry
        if (origin.x - ext.x) <= sx <= (origin.x + ext.x) and \
           (origin.y - ext.y) <= sy <= (origin.y + ext.y):
            top = origin.z + ext.z
            cover.append((a.get_actor_label(), top))
            if top <= sz + 120 and (best is None or top > best[1]):
                best = (a.get_actor_label(), top)
    if best:
        print(f"  FLOOR UNDER SPAWN: '{best[0]}' top_z={best[1]:.0f} (hero lands {sz-best[1]:.0f}uu below spawn)")
    else:
        print(f"  *** NO COLLIDING FLOOR under spawn XY -> hero falls into the void (RespawnBelowZ=-2000) ***")
    print(f"  (colliding actors spanning spawn XY: {sorted(cover, key=lambda t:-t[1])[:6]})")

# --- Enclosure census: the CityWall must line both sides of the street with no big gaps ---
walls = {"N": [], "S": []}
caps = 0
faces = 0
for a in actors:
    lbl = a.get_actor_label()
    if lbl.startswith("CityWall_N_"):
        walls["N"].append(a.get_actor_location().x)
    elif lbl.startswith("CityWall_S_"):
        walls["S"].append(a.get_actor_location().x)
    elif lbl.startswith("CityWall_WCap_"):
        caps += 1
    elif lbl.startswith("CityWallFace_"):
        faces += 1
print(f"WALL_CENSUS: N={len(walls['N'])} S={len(walls['S'])} wcap={caps} faces={faces}")
for side in ("N", "S"):
    xs = sorted(walls[side])
    if len(xs) < 8:
        print(f"  *** {side} wall too sparse ({len(xs)}) — void may show ***")
    else:
        biggest_gap = max((xs[i + 1] - xs[i] for i in range(len(xs) - 1)), default=0)
        flag = "  <-- GAP!" if biggest_gap > 1600 else ""
        print(f"  {side} wall: {len(xs)} segs, x[{xs[0]:.0f}..{xs[-1]:.0f}] biggest_gap={biggest_gap:.0f}{flag}")

# --- Rubble must now be SOLID (colliding bounds present) ---
for a in actors:
    if a.get_actor_label().startswith("Seam_Rubble"):
        try:
            _o, e = a.get_actor_bounds(True)
            solid = (e.x > 1 or e.y > 1 or e.z > 1)
        except Exception:
            solid = False
        print(f"RUBBLE: {a.get_actor_label()} solid_bounds={solid} tag={a.actor_has_tag(unreal.Name('Climbable'))}")

print("PROBE_SPAWN_DONE")
