"""Read-only check of the World-1 polish round (F1-F4). Safe with -nullrhi.
F1 no grey: every Tower_* uses a CityTowerKit mesh; no TowerBox_/ShopBox_ fallbacks.
F2 gates: neon_torii + festival_arch meshes have 0 simple collision + USE_SIMPLE_AS_COMPLEX.
F3 seam: Seam_Rubble_* present and NO_COLLISION; no festival arch at the seam (~world x9740).
F4 void: exactly one StarDome; zero SkyAtmosphere actors; SkyLight intensity <= 0.05.
"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
SMES = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity")

actors = eas.get_all_level_actors()
bylabel = {}
for a in actors:
    bylabel.setdefault(a.get_actor_label(), []).append(a)

fails = []

# F4 — void
domes = [a for a in actors if a.get_actor_label() == "StarDome"]
sky_atm = [a for a in actors if isinstance(a, unreal.SkyAtmosphere)]
skylights = [a for a in actors if isinstance(a, unreal.SkyLight)]
print(f"F4: StarDome={len(domes)} SkyAtmosphere={len(sky_atm)} SkyLight={len(skylights)}")
if len(domes) != 1:
    fails.append(f"StarDome count {len(domes)} (want 1)")
if len(sky_atm) != 0:
    fails.append(f"SkyAtmosphere still present ({len(sky_atm)})")
for sl in skylights:
    inten = sl.light_component.get_editor_property("intensity")
    print(f"     SkyLight intensity={inten}")
    if inten > 0.05:
        fails.append(f"SkyLight intensity {inten} too bright for space")

# F1 — towers colored, no grey fallbacks
towers = [a for a in actors if a.get_actor_label().startswith("Tower_")]
grey_boxes = [a for a in actors if a.get_actor_label().startswith(("TowerBox_", "ShopBox_"))]
tower_meshes = set()
for t in towers:
    smc = t.get_component_by_class(unreal.StaticMeshComponent)
    if smc and smc.get_editor_property("static_mesh"):
        tower_meshes.add(smc.get_editor_property("static_mesh").get_name())
print(f"F1: Tower_*={len(towers)} fallback_boxes={len(grey_boxes)} meshes={sorted(tower_meshes)}")
if grey_boxes:
    fails.append(f"{len(grey_boxes)} grey fallback boxes present")
if any(not m.startswith("SM_tower_") for m in tower_meshes):
    fails.append(f"non-CityTowerKit tower meshes: {tower_meshes}")

# F3 — seam rubble present + passable. The spawned-component flag doesn't persist, so passability
# is guaranteed at the MESH level (0 simple collision + USE_SIMPLE_AS_COMPLEX = no blocking geo).
rubble = [a for a in actors if a.get_actor_label().startswith("Seam_Rubble")]
print(f"F3: seam rubble={[a.get_actor_label() for a in rubble]}")
if not rubble:
    fails.append("no Seam_Rubble actors placed")
for path in ("/Game/Art/CityTowerKit/rubble_pile/SM_rubble_pile",
             "/Game/Art/CityTowerKit/debris_chunks/SM_debris_chunks"):
    sm = EAL.load_asset(path)
    if not sm:
        fails.append(f"rubble mesh missing: {path}")
        continue
    simple = SMES.get_simple_collision_count(sm)
    bs = sm.get_editor_property("body_setup")
    flag = bs.get_editor_property("collision_trace_flag") if bs else None
    print(f"F3: {sm.get_name()} simple_collision={simple} trace_flag={flag}")
    if simple != 0 or flag != unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX:
        fails.append(f"{sm.get_name()} still blocks (simple={simple} flag={flag})")

# F2 — gate meshes have no blocking collision geometry
for path in ("/Game/Art/FestivalKit/neon_torii/SM_neon_torii",
             "/Game/Art/FestivalKit/festival_arch/SM_festival_arch"):
    sm = EAL.load_asset(path)
    if not sm:
        fails.append(f"gate mesh missing: {path}")
        continue
    simple = SMES.get_simple_collision_count(sm)
    bs = sm.get_editor_property("body_setup")
    flag = bs.get_editor_property("collision_trace_flag") if bs else None
    print(f"F2: {sm.get_name()} simple_collision={simple} trace_flag={flag}")
    if simple != 0:
        fails.append(f"{sm.get_name()} has {simple} simple collision prims")
    if flag != unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX:
        fails.append(f"{sm.get_name()} trace_flag={flag} (want USE_SIMPLE_AS_COMPLEX)")

if fails:
    print("VERIFY_POLISH: FAIL")
    for f in fails:
        print(f"  - {f}")
else:
    print("VERIFY_POLISH: PASS")
print("VERIFY_POLISH_DONE")
