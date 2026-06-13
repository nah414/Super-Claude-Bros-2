"""Build /Game/Maps/RosterHall — a daylight gallery of the whole character bank.

Every SM_ asset under /Game/Art/Roster stands in a row at true design height.
The hero spawns facing the line: walk past your cast, Adam.
"""
import json
import unreal

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# THE SCRATCH DANCE (hard lesson, twice now): new_level() over an EXISTING map
# fails silently, leaving the startup map (MoonlitGlade!) loaded — every spawn
# then contaminates the GAME LEVEL and save_current_level() saves the damage.
# So: hop to a scratch level, delete the old hall, create it fresh, verify.
# (new_level also refuses to overwrite the SCRATCH itself — delete it first.)
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
assert les.new_level("/Game/Maps/_Scratch"), "SCRATCH_LEVEL_FAILED"
if EAL.does_asset_exist("/Game/Maps/RosterHall"):
    assert EAL.delete_asset("/Game/Maps/RosterHall"), "DELETE_OLD_HALL_FAILED"
assert les.new_level("/Game/Maps/RosterHall"), "NEW_HALL_FAILED"

# ---- stage: floor + daylight ----
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
floor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -50))
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(220.0, 90.0, 1.0))
floor.set_actor_label("HallFloor")

sun = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 800))
sun.set_actor_rotation(unreal.Rotator(0.0, -55.0, 35.0), False)
sun.light_component.set_intensity(8.0)
sun.set_actor_label("Sun")

sky_atm = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
sky_atm.set_actor_label("SkyAtmosphere")
skylight = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 600))
skylight.light_component.set_editor_property("real_time_capture", True)
skylight.set_actor_label("SkyLight")

# ---- the cast, in a row ----
assets = [a for a in EAL.list_assets("/Game/Art/Roster", recursive=True)
          if "/SM_" in a]
assets.sort()
# INVARIANT: never build the gallery against an empty bank. The whole point of
# the Hall is to show the cast; a zero-asset source means the bank moved or the
# scratch-dance left us on the wrong content root. Fail LOUD before we spawn an
# empty room and save_current_level() bakes the emptiness in.
assert assets, "ROSTER_SOURCE_EMPTY: no /SM_ assets under /Game/Art/Roster"
n = len(assets)
roster_seen = n  # SM_ paths discovered (some may not load as StaticMesh)
spacing = 260.0
x0 = -spacing * (n - 1) / 2.0
count = 0
for i, path in enumerate(assets):
    sm = EAL.load_asset(path)
    if not isinstance(sm, unreal.StaticMesh):
        continue
    actor = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(x0 + i * spacing, 500.0, 0.0))
    actor.static_mesh_component.set_static_mesh(sm)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, -90.0), False)  # face the visitor
    actor.set_actor_label(sm.get_name())
    count += 1
roster_count = count  # characters actually placed (count is roster-only here)
print(f"PLACED: {count} characters")
# INVARIANT: the source bank was non-empty (asserted above), so at least one
# StaticMesh must have loaded and placed. Zero here means every SM_ failed to
# load as a StaticMesh — a real-asset regression, not an empty room. Fail loud.
assert roster_count > 0, "HALL_EMPTY: 0 roster characters placed from non-empty bank"

# ---- second wing: the CITY KIT (review gate for stage objects) ----
city = sorted(a for a in EAL.list_assets("/Game/Art/CityKit", recursive=True) if "/SM_" in a)
small_x, big_x = -4500.0, -9000.0
city_placed = 0
for path in city:
    sm = EAL.load_asset(path)
    if not isinstance(sm, unreal.StaticMesh):
        continue
    b = sm.get_bounding_box()
    width = max(b.max.x - b.min.x, b.max.y - b.min.y)
    tall = (b.max.z - b.min.z) > 800.0
    if tall:
        x = big_x + width / 2.0
        big_x += width + 260.0
        y = 3800.0
    else:
        x = small_x + width / 2.0
        small_x += width + 180.0
        y = 1800.0
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, 0.0))
    actor.static_mesh_component.set_static_mesh(sm)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, -90.0), False)
    actor.set_actor_label(sm.get_name())
    count += 1
    city_placed += 1
print(f"PLACED_CITY: {city_placed}")

# Live actors are OPTIONAL review props: their classes only exist after a C++
# build, so a soft skip (not an assert) is correct — the manifest records which
# ones made it so the headless log self-reports the cast that shipped.
live = {}

# ---- a LIVE Glimmer (the real enemy, crystal-sprite body) for behavior review ----
try:
    glimmer_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.GlimmerEnemy")
    g = eas.spawn_actor_from_class(glimmer_cls, unreal.Vector(350, -400, 60))
    g.set_actor_label("LiveGlimmer")
    live["glimmer"] = True
    print("LIVE_GLIMMER_PLACED")
except Exception as e:
    live["glimmer"] = False
    print(f"LIVE_GLIMMER_SKIPPED: {e}")

# ---- a LIVE IRON KRAKEN (Rule 1: the new boss faces Adam's review HERE) ----
# Placed beyond his 900uu duel-start ring: walk toward him and the duel begins.
try:
    kraken_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.KrakenBoss")
    k = eas.spawn_actor_from_class(kraken_cls, unreal.Vector(1500, -700, 90))
    k.set_actor_rotation(unreal.Rotator(0.0, 0.0, 180.0), False)
    k.set_actor_label("LiveIronKraken")
    live["kraken"] = True
    print("LIVE_KRAKEN_PLACED")
except Exception as e:
    live["kraken"] = False
    print(f"LIVE_KRAKEN_SKIPPED: {e}")

# ---- a LIVE EMBER REAVER (rival #2, opposite wing — pick your duel) ----
try:
    reaver_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.EmberReaver")
    rv = eas.spawn_actor_from_class(reaver_cls, unreal.Vector(-1500, -700, 90))
    rv.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
    rv.set_actor_label("LiveEmberReaver")
    live["reaver"] = True
    print("LIVE_REAVER_PLACED")
except Exception as e:
    live["reaver"] = False
    print(f"LIVE_REAVER_SKIPPED: {e}")

# ---- a LIVE VOID STALKER (rival #3, the south wing — three duels now) ----
try:
    stalker_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.VoidStalker")
    vs = eas.spawn_actor_from_class(stalker_cls, unreal.Vector(0, -2400, 90))
    vs.set_actor_rotation(unreal.Rotator(0.0, 0.0, 90.0), False)
    vs.set_actor_label("LiveVoidStalker")
    live["stalker"] = True
    print("LIVE_STALKER_PLACED")
except Exception as e:
    live["stalker"] = False
    print(f"LIVE_STALKER_SKIPPED: {e}")

# ---- a LIVE BRAMBLEHULK (the SOOTHE boss — asleep in the SE corner) ----
try:
    hulk_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.Bramblehulk")
    bh = eas.spawn_actor_from_class(hulk_cls, unreal.Vector(2500, -2400, 120))
    bh.set_actor_rotation(unreal.Rotator(0.0, 0.0, 135.0), False)
    bh.set_actor_label("LiveBramblehulk")
    live["bramblehulk"] = True
    print("LIVE_BRAMBLE_PLACED")
except Exception as e:
    live["bramblehulk"] = False
    print(f"LIVE_BRAMBLE_SKIPPED: {e}")

# ---- a LIVE RUST WARLORD (rival #4, SW corner — first ASparkRivalBase subclass) ----
# Walk into his 900uu ring and the duel begins; break his armor to see the vent.
try:
    warlord_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.RustWarlord")
    wl = eas.spawn_actor_from_class(warlord_cls, unreal.Vector(-2500, -2400, 100))
    wl.set_actor_rotation(unreal.Rotator(0.0, 0.0, 45.0), False)
    wl.set_actor_label("LiveRustWarlord")
    live["warlord"] = True
    print("LIVE_WARLORD_PLACED")
except Exception as e:
    live["warlord"] = False
    print(f"LIVE_WARLORD_SKIPPED: {e}")

# ---- GRABBABLE PROPS (the RPG round: E grabs, LMB hurls) ----
props_placed = 0
try:
    prop_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.GrabbableProp")
    spots = [(180, -550), (-220, -480), (420, -780), (-450, -850), (90, -950), (-120, -350)]
    for i, (px, py) in enumerate(spots):
        pr = eas.spawn_actor_from_class(prop_cls, unreal.Vector(px, py, 60))
        pr.set_actor_label(f"GrabCrate_{i}")
        props_placed += 1
    print(f"PROPS_PLACED: {props_placed}")
except Exception as e:
    print(f"PROPS_SKIPPED: {e}")

# ---- THE LIVING HEROES wing (Rule 2: the Hall IS the asset profile/backup) ----
# Both playable heroes stand front-center, breathing their idle clips, so a
# walk through the Hall always shows the true current state of every rig.
HEROES = [
    ("Exhibit_ClaudeSpark", "/Game/Art/HeroSkelV4/SCB2Hero",
     "/Game/Art/HeroSkelV4/A_Hero_Idle_Anim", -200.0),
    ("Exhibit_Sonnet", "/Game/Art/HeroineSkelV2/SCB2Heroine",
     "/Game/Art/HeroineSkelV2/A_Heroine_Idle_Anim", 200.0),
]
heroes_placed = 0
for label, mesh_path, idle_path, x in HEROES:
    mesh = EAL.load_asset(mesh_path)
    idle = EAL.load_asset(idle_path)
    if not isinstance(mesh, unreal.SkeletalMesh):
        print(f"HERO_EXHIBIT_SKIPPED: {mesh_path}")
        continue
    actor = eas.spawn_actor_from_class(
        unreal.SkeletalMeshActor, unreal.Vector(x, 150.0, 0.0))
    comp = actor.skeletal_mesh_component
    comp.set_editor_property("skeletal_mesh_asset", mesh)
    if isinstance(idle, unreal.AnimSequence):
        comp.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.override_animation_data(idle, is_looping=True, is_playing=True)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, -90.0), False)
    actor.set_actor_label(label)
    heroes_placed += 1
    print(f"HERO_EXHIBIT_PLACED: {label}")

# ---- the visitor ----
start = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -700, 100))
start.set_actor_rotation(unreal.Rotator(0.0, 0.0, 90.0), False)  # look at the line
start.set_actor_label("PlayerStart")

saved = les.save_current_level()
print(f"SAVE_RESULT: {saved}")
# Leave no scratch behind (we're on RosterHall now, so the asset is deletable).
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
save_ok = bool(saved)
if not saved:
    # Belt and braces: save every dirty package the unattended path might hold back.
    ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
        save_map_packages=True, save_content_packages=True)
    save_ok = bool(ok)
    print(f"SAVE_DIRTY_FALLBACK: {ok}")

# INVARIANT: a headless build that does not persist is the worst failure mode —
# it prints success, exits 0, and leaves RosterHall.umap untouched on disk. If
# neither the level save nor the dirty-package fallback took, fail LOUD so the
# unattended run returns non-zero instead of silently shipping a stale map.
assert save_ok, "SAVE_FAILED: RosterHall not persisted (level save + fallback both false)"

# ---- self-reporting MANIFEST: one machine-parseable line the headless log and
#      verify_roster_hall.py both key off. roster_seen vs roster_count surfaces
#      any SM_ that failed to load as a StaticMesh without aborting the build. ----
manifest = {
    "roster_seen": roster_seen,
    "roster_count": roster_count,
    "city_placed": city_placed,
    "heroes_placed": heroes_placed,
    "props_placed": props_placed,
    "live": live,
    "saved": save_ok,
}
print("MANIFEST: " + json.dumps(manifest, sort_keys=True))
print("ROSTER_HALL_DONE")
