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

print("PROBE_SPAWN_DONE")
