"""Functional check: trace from the spawn outward to where the dome shell is (~50000uu) and confirm
NOTHING hits the StarDome (0 collision geometry => the hero can't penetrate it => no respawn loop)."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity")

ps = next((a for a in eas.get_all_level_actors() if isinstance(a, unreal.PlayerStart)), None)
loc = ps.get_actor_location()
start = unreal.Vector(loc.x, loc.y, loc.z + 200.0)

dirs = {
    "up": unreal.Vector(0, 0, 1),
    "down": unreal.Vector(0, 0, -1),
    "east": unreal.Vector(1, 0, 0.1),
    "west": unreal.Vector(-1, 0, 0.1),
    "north": unreal.Vector(0, 1, 0.1),
}
dome_hits = 0
for name, d in dirs.items():
    end = unreal.Vector(start.x + d.x * 75000.0, start.y + d.y * 75000.0, start.z + d.z * 75000.0)
    ok, hit = unreal.SystemLibrary.line_trace_single(
        ps, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
        unreal.DrawDebugTrace.NONE, True)
    hit_actor = hit.get_editor_property("hit_actor") if ok else None
    label = hit_actor.get_actor_label() if hit_actor else ("(nothing)" if not ok else "?")
    is_dome = (label == "StarDome")
    if is_dome:
        dome_hits += 1
    print(f"TRACE {name}: hit={'YES' if ok else 'no'} actor={label}{'  <-- DOME BLOCKS!' if is_dome else ''}")

print(f"DOME_TRACE_RESULT: dome_blocks={dome_hits} (0 = fixed, hero can't penetrate the sky)")
print("TRACE_DOME_DONE")
