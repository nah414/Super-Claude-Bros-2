"""Read-only check that the Festival Streets dressing is grounded + bounded.
Flags any prop whose WORLD base sits below the floor (sunk) or far above (floating)."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity")

props, sunk, floating = [], [], []
walls = lanterns = 0
ground = False
ROOF_Z = 2500.0

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if not lbl.startswith("Fest_"):
        continue
    if lbl.startswith("Fest_Lantern"):
        lanterns += 1
        continue
    if lbl.startswith("Fest_Ground"):
        ground = True
        continue
    if lbl.startswith("Fest_CanyonWall") or lbl.startswith("Fest_EndCap"):
        walls += 1
        continue
    if lbl.startswith("Fest_LightNetworkManager"):
        continue
    origin, ext = a.get_actor_bounds(False)
    base_z = origin.z - ext.z
    props.append((lbl, round(base_z)))
    # rooftop props are grounded near ROOF_Z; everything else near 0 or hung high
    on_roof = origin.z > 1800
    overhead = "festival_lanterns" in lbl or "paper_garland" in lbl or "cable_bundle" in lbl or "holo" in lbl
    if not on_roof and not overhead and base_z < -60:
        sunk.append((lbl, round(base_z)))
    if not on_roof and not overhead and base_z > 80:
        floating.append((lbl, round(base_z)))

print(f"VERIFY_FEST: {len(props)} ground-props, {walls} walls, ground_plane={ground}, {lanterns} lanterns")
print(f"SUNK (base z < -60): {sunk}")
print(f"FLOATING (base z > 80): {floating}")
print("VERIFY_FEST_DONE")
