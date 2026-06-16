"""Dress NeonCity into the warm-cyberpunk FESTIVAL STREETS (World 1 / ANTHROPICA).

Loads the existing cold neon boulevard and layers on: the Meshy Festival + Edge props
(scaled per piece — Meshy normalizes everything to ~190uu), the relight lanterns (warm
ambient + dark checkpoints + the dark First Lantern GOAL), the LightNetworkManager (the
Night / the finale), and volumetric fog for neon light-shafts. Idempotent: clears prior
"Fest_" actors first, so it can be re-run as the look is tuned.
"""
import unreal

EAL = unreal.EditorAssetLibrary
ELSS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_NEONCITY_FAILED"

# ---- idempotent: clear any prior festival dressing ----
removed = 0
for a in eas.get_all_level_actors():
    try:
        if a.get_actor_label().startswith("Fest_"):
            eas.destroy_actor(a)
            removed += 1
    except Exception:
        pass
print(f"CLEARED {removed} prior Fest_ actors")

LANTERN_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.Lantern")
NETMGR_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.LightNetworkManager")

placed = {"prop": 0, "lantern": 0}


def setp(actor, names, value):
    for nm in names:
        try:
            actor.set_editor_property(nm, value)
            return True
        except Exception:
            continue
    return False


def fprop(name, x, y, z, scale, yaw=0.0):
    sm = EAL.load_asset(f"/Game/Art/FestivalKit/{name}/SM_{name}")
    if not sm:
        unreal.log_warning(f"FESTIVAL_MISSING: {name}")
        return None
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z),
                                   unreal.Rotator(0.0, 0.0, yaw))
    a.static_mesh_component.set_static_mesh(sm)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_label(f"Fest_{name}_{placed['prop']}")
    placed["prop"] += 1
    return a


def lantern(x, y, label, *, z=0.0, checkpoint=False, goal=False, dark=False,
            relight_radius=300.0, auto=9.0, scale=1.0, intensity=900.0, radius=520.0):
    a = eas.spawn_actor_from_class(LANTERN_CLASS, unreal.Vector(x, y, z))
    setp(a, ["lit_intensity", "LitIntensity"], intensity)
    setp(a, ["lit_radius", "LitRadius"], radius)
    setp(a, ["relight_by_hero_radius", "RelightByHeroRadius"], relight_radius)
    setp(a, ["auto_relight_seconds", "AutoRelightSeconds"], auto)
    setp(a, ["is_checkpoint", "b_is_checkpoint", "bIsCheckpoint"], checkpoint)
    setp(a, ["is_world_goal", "b_is_world_goal", "bIsWorldGoal"], goal)
    setp(a, ["start_dark", "b_start_dark", "bStartDark"], dark)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_label(f"Fest_Lantern_{label}")
    placed["lantern"] += 1
    return a


# ========================= THE WARM FESTIVAL LAYER =========================
# Boulevard runs +X from the spawn (~-4500). Sidewalks at y=+-1050, facades +-1300.

# The grand entrance + arches you walk under
fprop("neon_torii", -4000, 0, 0, 3.6)
for ax in (-2200, 1200, 4600):
    fprop("festival_arch", ax, 0, 0, 4.4)

# Lantern poles lining both sidewalks
px = -3400
while px <= 7000:
    fprop("lantern_pole", px, 1080, 0, 2.2)
    fprop("lantern_pole", px + 600, -1080, 0, 2.2)
    px += 1500

# Food stalls, shrines, braziers, planters along the sidewalks
fprop("ramen_cart", -3000, 1050, 0, 1.6, yaw=180)
fprop("produce_stall", -1000, -1050, 0, 1.6, yaw=0)
fprop("tea_stall", 2000, 1050, 0, 1.7, yaw=180)
fprop("grill_barrel", 4000, -1050, 0, 1.5, yaw=0)
fprop("brazier_bowl", -2000, -1000, 0, 1.3)
fprop("brazier_bowl", 5400, 1000, 0, 1.3)
fprop("street_shrine", 600, 1050, 0, 1.4, yaw=180)
fprop("flower_planter", 3000, -1000, 0, 1.3)
fprop("flower_planter", -3400, 1000, 0, 1.3)
fprop("market_crates", -2500, 880, 0, 1.5)
fprop("market_crates", 3600, -880, 0, 1.5)

# Garlands + lantern strings overhead (between the poles)
for gx in (-1500, 1800, 4200, 6200):
    fprop("festival_lanterns", gx, 0, 360, 2.6)
for gx in (-2800, 700, 3300):
    fprop("paper_garland", gx, 0, 380, 2.4)

# ========================= THE COLD CYBERPUNK EDGE LAYER =========================
fprop("holo_billboard", 1200, 2600, 1350, 6.0, yaw=-90)      # koi-dragon hologram over the rooftops
fprop("mega_sign_tower", -1600, 2400, 250, 5.0)
fprop("mega_sign_tower", 5200, -2400, 250, 5.0)
fprop("neon_storefront", -900, 1320, 0, 3.0, yaw=180)
fprop("neon_storefront", 2600, -1320, 0, 3.0, yaw=0)
fprop("neon_storefront", 5600, 1320, 0, 3.0, yaw=180)
fprop("steam_vent", -1700, 300, 0, 1.6)
fprop("steam_vent", 3100, -300, 0, 1.6)
fprop("cable_bundle", 200, 1250, 520, 1.8)
fprop("cable_bundle", 4400, -1250, 520, 1.8)
fprop("conduit_machinery", 6400, 900, 0, 1.5)

# ========================= THE LANTERNS (the interactive heart) =========================
# Warm ambient lanterns (lit) — the festival glow.
ax = -3800
while ax <= 7200:
    lantern(ax, 820, f"amb_{ax}_L", relight_radius=300.0, scale=1.0)
    lantern(ax + 700, -820, f"amb_{ax}_R", relight_radius=300.0, scale=1.0)
    ax += 1600

# Dark CHECKPOINT lamps along the route — the maintenance worker relights them (hold E).
for i, cx in enumerate((-2600, 600, 3400, 6400)):
    lantern(cx, 0, f"cp_{i}", checkpoint=True, dark=True, relight_radius=0.0, auto=0.0,
            scale=1.15, intensity=1400.0, radius=620.0)

# THE FIRST LANTERN — the dark GOAL at the city's crown (relight it to win).
fprop("first_lantern", 11000, 0, 2500, 12.0)
lantern(11000, 0, "FIRST", z=2520, goal=True, dark=True, relight_radius=0.0, auto=0.0,
        scale=3.0, intensity=6000.0, radius=2600.0)

# ========================= THE LIGHT-NETWORK MANAGER =========================
mgr = eas.spawn_actor_from_class(NETMGR_CLASS, unreal.Vector(1500, 0, 800))
mgr.set_actor_label("Fest_LightNetworkManager")

# ========================= ATMOSPHERE: volumetric fog for neon light-shafts =========================
fog_on = False
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.ExponentialHeightFog):
        comp = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
        if comp:
            setp(comp, ["volumetric_fog", "VolumetricFog"], True)
            setp(comp, ["volumetric_fog_scattering_distribution", "VolumetricFogScatteringDistribution"], 0.4)
            setp(comp, ["volumetric_fog_extinction_scale", "VolumetricFogExtinctionScale"], 1.4)
            fog_on = True
print(f"VOLUMETRIC_FOG: {fog_on}")

saved = ELSS.save_current_level()
print(f"FEST_DRESS_DONE: {placed['prop']} props, {placed['lantern']} lanterns, mgr=1, saved={saved}")
