"""Build /Game/Maps/RosterHall — the deduplicated ASSET CATALOG + boss testing range.

Adam's law (June 13): the Roster Hall holds EVERY digital asset for the game, and it
holds exactly ONE copy of each character and each environment item. The 15 bosses each
get their own LIVE testing STATION — a clean 5x3 grid, well spaced so only the one you
walk up to ever wakes. The non-combat cast (both heroes, the moth, the glimmer, the
lamplighter) stands once each in the front welcome row. Environment items are single
catalog samples (one lantern, one crate). The City Kit lines the back as a one-of-each
skyline. No statues, no skin-clones, no lantern-fields — one of everything.
"""
import json
import unreal

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def spawn_class(path, loc, yaw=-90.0, label=None):
    """Spawn a C++ actor by class path; soft-skip if the class isn't built yet."""
    try:
        cls = unreal.load_class(None, path)
        a = eas.spawn_actor_from_class(cls, unreal.Vector(*loc))
        a.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
        if label:
            a.set_actor_label(label)
        return a
    except Exception as e:
        print(f"SPAWN_SKIPPED {label or path}: {e}")
        return None


# THE SCRATCH DANCE (hard lesson, twice): new_level() over an EXISTING map fails
# silently, leaving the startup map loaded; every spawn then contaminates THAT level
# and save bakes the damage. Hop to a scratch level, delete the old hall, make it fresh.
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
assert les.new_level("/Game/Maps/_Scratch"), "SCRATCH_LEVEL_FAILED"
if EAL.does_asset_exist("/Game/Maps/RosterHall"):
    assert EAL.delete_asset("/Game/Maps/RosterHall"), "DELETE_OLD_HALL_FAILED"
assert les.new_level("/Game/Maps/RosterHall"), "NEW_HALL_FAILED"

# ---- stage: floor + clear catalog daylight ----
# A catalog must READ, so this is clear warm daylight (the old dusk relied on a field
# of 25 lanterns to light the room — gone now, one lantern is a catalog sample).
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
floor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -50))
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(280.0, 200.0, 1.0))   # 28000 x 20000 uu
floor.set_actor_label("HallFloor")

sun = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 800))
sun.set_actor_rotation(unreal.Rotator(0.0, -34.0, 26.0), False)
sun.light_component.set_intensity(3.6)
sun.light_component.set_light_color(unreal.LinearColor(1.0, 0.86, 0.7))
sun.set_actor_label("Sun")

sky_atm = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
sky_atm.set_actor_label("SkyAtmosphere")
skylight = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 600))
skylight.light_component.set_editor_property("real_time_capture", True)
skylight.light_component.set_intensity(1.3)
skylight.set_actor_label("SkyLight")

live = {}

# ============================================================================
# THE 15 BOSS TESTING STATIONS — one per boss, a clean 5x3 grid. 3000uu apart so
# only the boss you walk up to ever wakes (2x the 900 duel-start ring, clear of the
# 1500 disengage ring). Front row = the sparring tier, back row = the finals.
# ============================================================================
STATIONS = [
    # row 1 (front, y=2000): the sparring tier
    ("SleekKnight",     "Sleek Knight"),
    ("HeroicTank",      "Heroic Tank"),
    ("Powerhouse",      "Powerhouse"),
    ("ClassicSpark",    "Classic Spark"),
    ("RolyShellback",   "Roly Shellback"),
    # row 2 (mid, y=5000): the rivals + the W-bosses
    ("KrakenBoss",      "Iron Kraken"),
    ("EmberReaver",     "Ember Reaver"),
    ("VoidStalker",     "Void Stalker"),
    ("RustWarlord",     "Rust Warlord"),
    ("ShellbackAlpha",  "Shellback Alpha"),
    # row 3 (back, y=8000): the heavies + the finals
    ("Bramblehulk",     "Bramblehulk"),
    ("HollowWarden",    "Hollow Warden"),
    ("FoundryKing",     "Foundry King"),
    ("LumenDragonlord", "Lumen Dragonlord"),
    ("Unlight",         "The Unlight"),
]
COLS = [-6000, -3000, 0, 3000, 6000]
ROWS = [2000, 5000, 8000]

stations_placed = 0
for i, (cls_name, nice) in enumerate(STATIONS):
    loc = (COLS[i % 5], ROWS[i // 5], 200)
    a = spawn_class(f"/Script/SuperClaudeBros2.{cls_name}", loc, yaw=-90.0,
                    label=f"Live{cls_name}")
    live[cls_name.lower()] = a is not None
    if a is not None:
        stations_placed += 1
        print(f"STATION_PLACED {i+1:02d}/15: Live{cls_name}  ({nice}) @ {loc}")
print(f"STATIONS_PLACED: {stations_placed}/15")

# ============================================================================
# THE FRONT WELCOME ROW — the non-combat cast, one copy each, greeting the visitor.
# ============================================================================
# Lumen the Lamplighter (NPC — his true form, the Dragonlord, is a back-row station).
lp = spawn_class("/Script/SuperClaudeBros2.LumenLamplighter", (0, 100, 210),
                 label="LiveLumenLamplighter")
live["lamplighter"] = lp is not None
if lp is not None:
    print("LAMPLIGHTER_PLACED")

# Flit Moth (the no-HP Lightlove critter) — one, hovering to the right.
fm = spawn_class("/Script/SuperClaudeBros2.FlitMoth", (2200, 250, 170),
                 label="LiveFlitMoth")
live["flitmoth"] = fm is not None
if fm is not None:
    print("FLITMOTH_PLACED")

# Glimmer (the basic crystal enemy) — one, front-left, far enough off the spawn that
# it doesn't aggro on step one (walk over to test it).
gl = spawn_class("/Script/SuperClaudeBros2.GlimmerEnemy", (-2200, 250, 60),
                 label="LiveGlimmer")
live["glimmer"] = gl is not None
if gl is not None:
    print("GLIMMER_PLACED")

# The two playable heroes — animated skeletal exhibits, one each (the Hall is the
# living asset profile of every rig — Rule 2).
HEROES = [
    ("Exhibit_ClaudeSpark", "/Game/Art/HeroSkelV4/SCB2Hero",
     "/Game/Art/HeroSkelV4/A_Hero_Idle_Anim", -900.0),
    ("Exhibit_Sonnet", "/Game/Art/HeroineSkelV2/SCB2Heroine",
     "/Game/Art/HeroineSkelV2/A_Heroine_Idle_Anim", 900.0),
]
heroes_placed = 0
for label, mesh_path, idle_path, x in HEROES:
    mesh = EAL.load_asset(mesh_path)
    idle = EAL.load_asset(idle_path)
    if not isinstance(mesh, unreal.SkeletalMesh):
        print(f"HERO_EXHIBIT_SKIPPED: {mesh_path}")
        continue
    actor = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(x, 100.0, 0.0))
    comp = actor.skeletal_mesh_component
    comp.set_editor_property("skeletal_mesh_asset", mesh)
    comp.set_editor_property("visibility_based_anim_tick_option",
                             unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    comp.set_editor_property("bounds_scale", 1.4)
    if isinstance(idle, unreal.AnimSequence):
        comp.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.override_animation_data(idle, is_looping=True, is_playing=True)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, -90.0), False)
    actor.set_actor_label(label)
    heroes_placed += 1
    print(f"HERO_EXHIBIT_PLACED: {label}")

# ============================================================================
# ENVIRONMENT CATALOG — one copy of each environment item.
# ============================================================================
# One lantern (the light-system atom — the Warden eats it, the hero relights it).
lant = spawn_class("/Script/SuperClaudeBros2.Lantern", (1400, 700, 0), yaw=0.0,
                   label="HallLantern")
print("LANTERN_PLACED" if lant is not None else "LANTERN_SKIPPED")

# One grabbable crate (E grabs, LMB hurls).
crate = spawn_class("/Script/SuperClaudeBros2.GrabbableProp", (-1400, 700, 60), yaw=0.0,
                    label="GrabCrate")
props_placed = 1 if crate is not None else 0
print("CRATE_PLACED" if crate is not None else "CRATE_SKIPPED")

# ---- THE CITY KIT — one of each environment building, a back-row skyline (Anthropica
#      backdrop). Tucked behind the back station row so it frames, never crowds. ----
city = sorted(a for a in EAL.list_assets("/Game/Art/CityKit", recursive=True) if "/SM_" in a)
small_x, big_x = -13000.0, -13000.0
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
        big_x += width + 300.0
        y = 9700.0
    else:
        x = small_x + width / 2.0
        small_x += width + 200.0
        y = 9100.0
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, 0.0))
    actor.static_mesh_component.set_static_mesh(sm)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, -90.0), False)
    actor.set_actor_label(sm.get_name())
    city_placed += 1
print(f"CITY_PLACED: {city_placed}")

# ---- RAY-TRACING BUDGET (Adam hit the RT instance threshold — the window-shrink).
#      Pull the STATIC geometry (floor + city kit + crate) off RT; the LIVE skeletal
#      cast stays ray-traced so reflections/GI still read. ----
rt_off = 0
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor):
        smc = a.static_mesh_component
        if smc:
            smc.set_editor_property("visible_in_ray_tracing", False)
            rt_off += 1
print(f"RT_OFF: {rt_off} static meshes pulled off ray tracing")

# ---- the visitor ----
start = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -700, 100))
start.set_actor_rotation(unreal.Rotator(0.0, 0.0, 90.0), False)   # look down the range
start.set_actor_label("PlayerStart")

saved = les.save_current_level()
print(f"SAVE_RESULT: {saved}")
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
save_ok = bool(saved)
if not saved:
    ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
        save_map_packages=True, save_content_packages=True)
    save_ok = bool(ok)
    print(f"SAVE_DIRTY_FALLBACK: {ok}")
assert save_ok, "SAVE_FAILED: RosterHall not persisted (level save + fallback both false)"

manifest = {
    "stations_expected": len(STATIONS),
    "stations_placed": stations_placed,
    "heroes_placed": heroes_placed,
    "props_placed": props_placed,
    "city_placed": city_placed,
    "live": live,
    "saved": save_ok,
}
print("MANIFEST: " + json.dumps(manifest, sort_keys=True))
print("ROSTER_HALL_DONE")
