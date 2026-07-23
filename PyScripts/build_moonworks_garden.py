"""THE MOONWORKS TEST GARDEN — first light on the World Stage (M1.2, both halves).

Lays a solvable beam chain on /Game/Maps/WorldStageTesting:

  Source ──> Crystal A ──(default: aimed +Y)──> Prism ──split──> two Moonflowers BLOOM
                └─(rotate 4 stops to 0)──> Crystal B ──> the dormant BRAMBLEHULK (calm fills)

So the DEFAULT state screenshots the flower branch lit, and Adam's first playtest
act is turning Crystal A four E-taps to pour the light onto the sleeping hill —
the Moonworks beam kit MVP and the soothe channel MVP in one garden.

Runs AFTER import_moonworks_props.py, in its OWN session (FObjectFinder law).
Probes every Meshy body's bounds at spawn: grounds each prop (Meshy pivots are
centered) and applies corrective scale if the import-time build scale lied.
"""
import math

import unreal

MAP = "/Game/Maps/WorldStageTesting"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary

# name: (axis, target_uu) — mirrors the import spec; the garden re-checks the work.
TARGETS = {
    "moon_crystal": ("z", 340.0),
    "moon_prism": ("z", 230.0),
    "crystal_tree": ("z", 900.0),
}


def cls(name):
    c = unreal.load_class(None, f"/Script/SuperClaudeBros2.{name}")
    assert c, f"CLASS_MISSING: {name}"
    return c


assert les.load_level(MAP), "LOAD_STAGE_FAILED"

# Rerun-safe: clear any previous garden (tagged by label prefix).
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith("MW_"):
        eas.destroy_actor(a)


def ground_body(actor, mesh_name, axis, target):
    """Meshy pivots are centered: sit the body's base on the stage, at canon size."""
    body = actor.get_editor_property("body_mesh")
    sm = body.get_editor_property("static_mesh") if body else None
    if not sm or mesh_name not in sm.get_name():
        return   # placeholder primitive: constructor offsets already tuned
    b = sm.get_bounding_box()
    size = {"x": b.max.x - b.min.x, "z": b.max.z - b.min.z}[axis]
    f = 1.0
    if size > 1.0 and abs(1.0 - target / size) > 0.15:
        f = target / size   # the import-time build scale lied — correct it here
    body.set_editor_property("relative_scale3d", unreal.Vector(f, f, f))
    body.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, -b.min.z * f))
    print(f"GARDEN_PROBE: {actor.get_actor_label()} {sm.get_name()} {size:.0f}uu -> x{f:.2f}")


def spawn(class_name, label, x, y, yaw, mesh_key=None):
    a = eas.spawn_actor_from_class(cls(class_name), unreal.Vector(x, y, 0.0),
                                   unreal.Rotator(0.0, 0.0, yaw))
    a.set_actor_label(label)
    if mesh_key:
        axis, target = TARGETS[mesh_key]
        ground_body(a, mesh_key, axis, target)
    return a


# ---- the chain ----
spawn("MoonBeamSource", "MW_Source", -2500, 0, 0, "moon_crystal")
spawn("MoonCrystal", "MW_CrystalA", -500, 0, 90, "moon_crystal")
spawn("MoonPrism", "MW_Prism", -500, 1500, 90, "moon_prism")
spawn("MoonCrystal", "MW_CrystalB", 1500, 0, math.degrees(math.atan2(1200, 2500)), "moon_crystal")

f1 = eas.spawn_actor_from_class(cls("MoonflowerPlatform"), unreal.Vector(400, 3059, 0), unreal.Rotator())
f1.set_actor_label("MW_Flower1")
f2 = eas.spawn_actor_from_class(cls("MoonflowerPlatform"), unreal.Vector(-1400, 3059, 0), unreal.Rotator())
f2.set_actor_label("MW_Flower2")

# ---- the big friend (dormant; the light will find him) ----
hulk = eas.spawn_actor_from_class(cls("Bramblehulk"), unreal.Vector(4000, 1200, 250), unreal.Rotator(0, 0, 200))
hulk.set_actor_label("MW_Bramblehulk")

# ---- the first whisper of Glade: crystal trees as dressing ----
tree_sm = EAL.load_asset("/Game/Art/Moonworks/crystal_tree")
if tree_sm:
    b = tree_sm.get_bounding_box()
    h = b.max.z - b.min.z
    f = TARGETS["crystal_tree"][1] / h if h > 1.0 and abs(1.0 - TARGETS["crystal_tree"][1] / h) > 0.15 else 1.0
    for i, (tx, ty, tyaw) in enumerate([(-3500, 2600, 15), (2600, 3700, 140),
                                        (-2900, -2500, 260), (3700, -1600, 80)]):
        t = eas.spawn_actor_from_object(tree_sm, unreal.Vector(tx, ty, -b.min.z * f))
        t.set_actor_label(f"MW_Tree{i}")
        t.set_actor_rotation(unreal.Rotator(0.0, 0.0, tyaw), False)
        t.set_actor_scale3d(unreal.Vector(f, f, f))
    print(f"GARDEN_PROBE: crystal_tree {h:.0f}uu -> x{f:.2f}")
else:
    print("GARDEN_WARN: crystal_tree asset missing; stage stays bare")

assert les.save_current_level(), "SAVE_GARDEN_FAILED"
print("GARDEN_MARKER: Moonworks test garden saved on WorldStageTesting")
print("GARDEN_MARKER: DONE")
