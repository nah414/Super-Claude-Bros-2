"""Build the Moonlit Glade — SCB2's first immersive area — entirely from code.

A 3D homage to v1's moonlit World 1: a ~120m x 120m night clearing ringed by
pines and boulders, a winding S-curve of stone steps climbing to a 12m vista
knoll crowned by the Monument, ember-glow crystals lighting the way, and three
floating island chunks teasing the double-jump+dash to come.

Kit meshes are expected at /Game/Art/Kit/* (imported before this runs). Any
missing kit asset logs a warning and is skipped — this script never crashes
on a missing mesh.

Run via:  Scripts\\run_pyscript.ps1 -Script PyScripts\\build_moonlit_glade.py
Saves to: /Game/Maps/MoonlitGlade
"""
import math
import random

import unreal

# Fixed seed so every rebuild scatters grass/rocks identically (reproducible).
random.seed(414)

CUBE = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Overwrite the previous glade cleanly. NEVER delete the currently-loaded level
# (the editor asserts if we saw off the branch we're sitting on) — step onto a
# scratch level first, exactly like build_feel_gym.py does.
if unreal.EditorAssetLibrary.does_asset_exist("/Game/Maps/MoonlitGlade"):
    les.new_level("/Game/Maps/_Scratch")
    unreal.EditorAssetLibrary.delete_asset("/Game/Maps/MoonlitGlade")
les.new_level("/Game/Maps/MoonlitGlade")


# ---- Kit assets (contract: imported before this script runs) ----
KIT_NAMES = [
    "Rock_Small", "Rock_Medium", "Rock_Large",
    "Pine_Small", "Pine_Tall",
    "Crystal_Small", "Crystal_Tall",
    "Column", "Arch", "GrassTuft", "Monument", "IslandChunk",
]
KIT = {}
for _name in KIT_NAMES:
    # Interchange nests imports as /Game/Art/Kit/<Name>/StaticMeshes/<Name>; try that
    # first, fall back to the flat path.
    KIT[_name] = None
    for _path in (f"/Game/Art/Kit/{_name}/StaticMeshes/{_name}", f"/Game/Art/Kit/{_name}"):
        if unreal.EditorAssetLibrary.does_asset_exist(_path):
            KIT[_name] = unreal.EditorAssetLibrary.load_asset(_path)
            break
    if KIT[_name] is None:
        unreal.log_warning(f"MoonlitGlade: kit mesh missing, skipping all placements of: {_name}")


def block(x, y, z, sx, sy, sz, label):
    """A scaled engine-cube StaticMeshActor (cube asset is 100uu => scale = size/100)."""
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z))
    actor.set_actor_label(label)
    mesh = actor.static_mesh_component
    mesh.set_static_mesh(CUBE)
    actor.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    actor.set_mobility(unreal.ComponentMobility.STATIC)
    return actor


def prop(kit_name, x, y, z, label, yaw=0.0, scale=1.0):
    """A kit-mesh StaticMeshActor with yaw + uniform scale. Skips silently if the
    kit asset is missing (the warning already fired once at load time)."""
    mesh = KIT.get(kit_name)
    if mesh is None:
        return None
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z))
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)  # (roll, pitch, yaw)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    actor.set_mobility(unreal.ComponentMobility.STATIC)
    return actor


# Hero-orange ember glow (#d97757) used by every crystal + the Monument.
EMBER = unreal.LinearColor(217 / 255.0, 119 / 255.0, 87 / 255.0, 1.0)


def glow_light(x, y, z, label, intensity=2500.0, radius=900.0):
    """Warm point light. Shadows ON: MegaLights (UE 5.7) renders many shadowed
    dynamic lights at near-constant cost — this glade is its poster child."""
    light = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, z))
    light.set_actor_label(label)
    lc = light.light_component
    lc.set_light_color(EMBER)
    lc.set_intensity(intensity)  # cd
    lc.set_editor_property("attenuation_radius", radius)
    lc.set_editor_property("cast_shadows", True)
    return light


def crystal(kit_name, x, y, z, label, yaw=0.0, scale=1.0,
            intensity=2500.0, radius=900.0):
    """A crystal mesh + its ember glow at +0.8m. Light only spawns if the mesh did."""
    actor = prop(kit_name, x, y, z, label, yaw, scale)
    if actor is not None:
        glow_light(x, y, z + 80, label + "_Glow", intensity, radius)
    return actor


# =====================================================================
# GROUND — 128m x 128m slab, top surface at z=0
# =====================================================================
HALF = 6400                       # floor half-extent
block(0, 0, -50, 2 * HALF, 2 * HALF, 100, "Floor")

# Landmarks the scatter must keep clear of:
CLEARING = (-4200.0, 0.0)         # hero spawn clearing (west end)
KNOLL = (4600.0, 0.0)             # vista knoll center (east end)


def scatter_point():
    """Random ground point inside the tree ring, rerolled out of the clearing
    and knoll footprints (max 20 tries — worst case we accept the last roll)."""
    for _ in range(20):
        x = random.uniform(-5200, 5200)
        y = random.uniform(-5200, 5200)
        if math.hypot(x - CLEARING[0], y - CLEARING[1]) < 1000:
            continue
        if math.hypot(x - KNOLL[0], y - KNOLL[1]) < 1700:
            continue
        return x, y
    return x, y


# ---- Dressing: ~80 grass tufts + ~25 mixed rocks, jittered yaw + scale ----
for i in range(80):
    x, y = scatter_point()
    prop("GrassTuft", x, y, 0,
         f"Grass_{i+1:02d}", yaw=random.uniform(0, 360), scale=random.uniform(0.7, 1.4))

ROCK_MIX = ["Rock_Small", "Rock_Small", "Rock_Small",
            "Rock_Medium", "Rock_Medium", "Rock_Large"]   # biased toward small
for i in range(25):
    x, y = scatter_point()
    prop(random.choice(ROCK_MIX), x, y, 0,
         f"ScatterRock_{i+1:02d}", yaw=random.uniform(0, 360), scale=random.uniform(0.7, 1.4))


# =====================================================================
# PERIMETER — dense pine/boulder ring (~every 6m) + boundary walls outside it
# =====================================================================
RING = 5700                       # tree-ring half-extent (square perimeter walk)
RING_CYCLE = ["Pine_Tall", "Rock_Large", "Pine_Small"]
_corners = [(-RING, -RING), (RING, -RING), (RING, RING), (-RING, RING)]
_idx = 0
for c in range(4):
    (x0, y0), (x1, y1) = _corners[c], _corners[(c + 1) % 4]
    steps = int(math.hypot(x1 - x0, y1 - y0) // 600)      # one prop per ~6m
    for k in range(steps):                                # skip t=1: corner dedupe
        t = k / steps
        x = x0 + (x1 - x0) * t + random.uniform(-120, 120)
        y = y0 + (y1 - y0) * t + random.uniform(-120, 120)
        prop(RING_CYCLE[_idx % 3], x, y, 0,
             f"Ring_{_idx+1:02d}_{RING_CYCLE[_idx % 3]}",
             yaw=random.uniform(0, 360), scale=random.uniform(0.85, 1.25))
        _idx += 1

# Invisible-ish boundary: tall thin engine-cube walls just outside the trees,
# so the hero can never leave even with future movement upgrades.
WALL_H, WALL_T, WALL_D = 2200, 200, 6050   # height, thickness, distance from center
block(0, WALL_D + WALL_T / 2, WALL_H / 2, 2 * WALL_D + 2 * WALL_T, WALL_T, WALL_H, "Bound_North")
block(0, -(WALL_D + WALL_T / 2), WALL_H / 2, 2 * WALL_D + 2 * WALL_T, WALL_T, WALL_H, "Bound_South")
block(WALL_D + WALL_T / 2, 0, WALL_H / 2, WALL_T, 2 * WALL_D, WALL_H, "Bound_East")
block(-(WALL_D + WALL_T / 2), 0, WALL_H / 2, WALL_T, 2 * WALL_D, WALL_H, "Bound_West")


# =====================================================================
# THE PATH — winding S-curve of stone steps, clearing -> knoll, +0.5m each
# =====================================================================
N_STEPS = 10
PATH = []   # (x, y, top_z) per step, reused for crystals / columns / arch
for i in range(N_STEPS):
    x = -2800 + i * 700                                   # west -> east
    y = 1200 * math.sin(2 * math.pi * i / (N_STEPS - 1))  # full S sweep
    top = 50 * (i + 1)                                    # +0.5m per step
    PATH.append((x, y, top))
    # Solid pillar from the ground to the step top (no floating slabs).
    block(x, y, top / 2, 300, 300, top, f"PathStep_{i+1:02d}")

# Crystal_Small flanking every other step, alternating sides of the path.
for i in range(0, N_STEPS, 2):
    x, y, top = PATH[i]
    side = 1 if (i // 2) % 2 == 0 else -1
    crystal("Crystal_Small", x, y + side * 360, 0,
            f"PathCrystal_{i+1:02d}", yaw=random.uniform(0, 360))

# Column pair midway — a gateway where the S-curve crosses the centerline.
prop("Column", 350, 450, 0, "Gate_Column_L")
prop("Column", 350, -450, 0, "Gate_Column_R")

# Arch over step 5, yawed to the local path heading (step 4 -> step 6).
ax, ay, atop = PATH[4]
_dx, _dy = PATH[5][0] - PATH[3][0], PATH[5][1] - PATH[3][1]
arch_yaw = math.degrees(math.atan2(_dy, _dx))
prop("Arch", ax, ay, atop, "Path_Arch", yaw=arch_yaw)


# =====================================================================
# THE VISTA KNOLL — stacked stepped cubes up to 12m, Monument on top
# =====================================================================
KX, KY = KNOLL
# (size, top_z): four 3m risers — the last path step (top 500) lands beside tier 2.
for tier, (size, top) in enumerate([(2600, 300), (2000, 600), (1400, 900), (900, 1200)]):
    block(KX, KY, top - 150, size, size, 300, f"Knoll_Tier_{tier+1}")

# The Monument, with one bigger warm beacon light.
monument = prop("Monument", KX, KY, 1200, "Vista_Monument")
if monument is not None:
    glow_light(KX, KY, 1200 + 80, "Vista_Monument_Glow", intensity=8000.0, radius=2000.0)

# Ring of 4 Crystal_Tall on the summit corners (each gets its own glow).
for j, (ox, oy) in enumerate([(280, 280), (280, -280), (-280, -280), (-280, 280)]):
    crystal("Crystal_Tall", KX + ox, KY + oy, 1200,
            f"Vista_Crystal_{j+1}", yaw=random.uniform(0, 360))


# =====================================================================
# FLOATING ISLANDS — 3 IslandChunk at varied heights near the path
# (reachable later with double-jump + dash)
# =====================================================================
for j, (x, y, z, yaw) in enumerate([(-1500, 2300, 800, 20),
                                    (900, -2400, 1250, 140),
                                    (3000, 2400, 1700, 260)]):
    prop("IslandChunk", x, y, z, f"FloatIsland_{j+1}", yaw=yaw, scale=random.uniform(1.0, 1.2))


# =====================================================================
# LIGHTING — moonlit night (Lumen is on project-wide)
# =====================================================================
moon = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 1500))
moon.set_actor_label("MoonLight")
moon.set_actor_rotation(unreal.Rotator(0.0, -35.0, -60.0), False)  # (roll, pitch, yaw)
moon.light_component.set_intensity(2.5)                            # bright moonlight
moon.light_component.set_light_color(unreal.LinearColor(0.72, 0.80, 1.0, 1.0))  # cool blue
try:
    # Do NOT drive the SkyAtmosphere from this light: linked, the atmosphere renders
    # a bright DAYTIME sky (first-light screenshot proved it). Unlinked, the sky goes
    # deep night and the crystals carry the scene.
    moon.light_component.set_editor_property("atmosphere_sun_light", False)
except Exception as e:
    unreal.log_warning(f"MoonlitGlade: could not set atmosphere_sun_light: {e}")

sky_light = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 1200))
sky_light.set_actor_label("SkyLight")
sky_light.light_component.set_editor_property("real_time_capture", True)

eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0)).set_actor_label("SkyAtmosphere")

fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0))
fog.set_actor_label("MoonFog")
try:
    fc = fog.component
    fc.set_editor_property("volumetric_fog", True)
    fc.set_editor_property("fog_density", 0.035)                 # modest, not soupy
    # Deep blue inscattering (UE5 name; was fog_inscattering_color pre-4.26).
    fc.set_editor_property("fog_inscattering_luminance",
                           unreal.LinearColor(0.015, 0.035, 0.09, 1.0))
except Exception as e:
    unreal.log_warning(f"MoonlitGlade: fog tuning failed (property names may have shifted): {e}")

# Unbound post-process volume: lift the bloom so crystal embers shimmer.
ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
ppv.set_actor_label("PP_MoonlitGlade")
try:
    ppv.set_editor_property("unbound", True)
    pps = ppv.get_editor_property("settings")        # FPostProcessSettings
    pps.set_editor_property("override_bloom_intensity", True)
    pps.set_editor_property("bloom_intensity", 1.2)
    # LOCK the eye: auto-exposure would re-brighten the night back into day.
    pps.set_editor_property("override_auto_exposure_min_brightness", True)
    pps.set_editor_property("auto_exposure_min_brightness", -1.2)
    pps.set_editor_property("override_auto_exposure_max_brightness", True)
    pps.set_editor_property("auto_exposure_max_brightness", -1.2)
    # ---- Cinematic stack (Phase 0.7) — each guarded; property names can shift ----
    for prop, val in (
        ("override_bloom_method", True),
        ("bloom_method", unreal.BloomMethod.BM_FFT),          # convolution bloom: real halos
        ("override_bloom_threshold", True),
        ("bloom_threshold", 1.5),                              # only hot pixels bloom
        ("override_film_grain_intensity", True),
        ("film_grain_intensity", 0.12),                        # subtle film texture
        ("override_vignette_intensity", True),
        ("vignette_intensity", 0.3),
        ("override_scene_fringe_intensity", True),
        ("scene_fringe_intensity", 0.25),                      # whisper of chromatic aberration
        ("override_local_exposure_shadow_contrast_scale", True),
        ("local_exposure_shadow_contrast_scale", 0.8),         # lift night shadows readably
        ("override_color_saturation", True),
        ("color_saturation", unreal.Vector4(0.95, 0.95, 0.95, 1.0)),
        ("override_color_gain_shadows", True),
        ("color_gain_shadows", unreal.Vector4(0.92, 1.0, 1.12, 1.0)),   # teal shadows
        ("override_color_gain_highlights", True),
        ("color_gain_highlights", unreal.Vector4(1.10, 1.02, 0.92, 1.0)),  # warm highlights
    ):
        try:
            pps.set_editor_property(prop, val)
        except Exception as e:
            unreal.log_warning(f"MoonlitGlade: post prop {prop} skipped: {e}")
    ppv.set_editor_property("settings", pps)         # write the struct back
except Exception as e:
    unreal.log_warning(f"MoonlitGlade: post-process tuning failed: {e}")


# =====================================================================
# THE MOON + FIREFLIES — the v1 homage touches
# =====================================================================
SPHERE = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere")
GLOW_MAT = None
if unreal.EditorAssetLibrary.does_asset_exist("/Game/Art/M_VertexLitEmissive"):
    GLOW_MAT = unreal.EditorAssetLibrary.load_asset("/Game/Art/M_VertexLitEmissive")


def glow_sphere(x, y, z, scale, label):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z))
    a.set_actor_label(label)
    a.static_mesh_component.set_static_mesh(SPHERE)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    if GLOW_MAT:
        a.static_mesh_component.set_material(0, GLOW_MAT)
    a.set_mobility(unreal.ComponentMobility.STATIC)
    return a


# A big low moon hanging over the vista (engine sphere verts are white -> glows pale).
glow_sphere(14000, 5000, 7000, 14.0, "TheMoon")

# Fireflies: tiny glowing motes drifting 1-3m above the glade floor.
for i in range(28):
    fx = random.uniform(-5000, 5000)
    fy = random.uniform(-5000, 5000)
    fz = random.uniform(100, 320)
    glow_sphere(fx, fy, fz, 0.045, f"Firefly_{i+1}")

# =====================================================================
# NIGHT DRESSING PASS — hide the boundary walls (collision stays; the black sky
# and tree silhouettes become the backdrop) and give level geometry night materials.
# =====================================================================
M_GROUND = (unreal.EditorAssetLibrary.load_asset("/Game/Art/M_NightGround")
            if unreal.EditorAssetLibrary.does_asset_exist("/Game/Art/M_NightGround") else None)
M_STONE = (unreal.EditorAssetLibrary.load_asset("/Game/Art/M_Stone")
           if unreal.EditorAssetLibrary.does_asset_exist("/Game/Art/M_Stone") else None)
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl.startswith("Bound"):
        a.set_actor_hidden_in_game(True)          # invisible fence
    elif lbl == "Floor" and M_GROUND:
        a.static_mesh_component.set_material(0, M_GROUND)
    elif M_STONE and (lbl.startswith("PathStep") or lbl.startswith("Knoll")
                      or lbl.startswith("Vista") or lbl.startswith("Gate")):
        try:
            a.static_mesh_component.set_material(0, M_STONE)
        except Exception:
            pass

# =====================================================================
# GLIMMER ENEMIES — three patrol foes in the clearing and along the path
# =====================================================================
try:
    glimmer_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.GlimmerEnemy")
    for i, (gx, gy) in enumerate(((-2200, 600), (-800, -900), (1500, 1400))):
        g = eas.spawn_actor_from_class(glimmer_cls, unreal.Vector(gx, gy, 60))
        g.set_actor_label(f"Glimmer_{i+1}")
    unreal.log("GLIMMERS_PLACED: 3")
except Exception as e:
    unreal.log_warning(f"could not place Glimmers: {e}")

# =====================================================================
# PLACEMENT AUDIT — counts in the log so missing assets are obvious
# =====================================================================
try:
    from collections import Counter
    counts = Counter()
    for a in eas.get_all_level_actors():
        lbl = a.get_actor_label()
        counts[lbl.split("_")[0]] += 1
    unreal.log(f"GLADE_AUDIT: {dict(counts)}")
    print(f"GLADE_AUDIT: {dict(counts)}")
except Exception as e:
    unreal.log_warning(f"audit failed: {e}")

# =====================================================================
# PLAYER START — in the clearing, facing east toward the path
# =====================================================================
start = eas.spawn_actor_from_class(
    unreal.PlayerStart, unreal.Vector(CLEARING[0], CLEARING[1], 120))
start.set_actor_label("PlayerStart")
start.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)  # +X = toward the path

# Pin OUR game mode on the map itself (belt & suspenders: PIE honors this even
# if project/user settings drift), so Play always spawns the Spark Hero.
try:
    hero_gm = unreal.load_class(None, "/Script/SuperClaudeBros2.SparkHeroGameMode")
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.WorldSettings):
            a.set_editor_property("default_game_mode", hero_gm)
            unreal.log("WorldSettings: game mode pinned to SparkHeroGameMode")
            break
except Exception as e:  # never let the pin break the glade build
    unreal.log_warning(f"could not pin game mode on WorldSettings: {e}")

# Save, and sweep up the scratch level if we used one.
les.save_current_level()
if unreal.EditorAssetLibrary.does_asset_exist("/Game/Maps/_Scratch"):
    unreal.EditorAssetLibrary.delete_asset("/Game/Maps/_Scratch")
unreal.log("MOONLIT_GLADE_BUILT: /Game/Maps/MoonlitGlade")
print("MOONLIT_GLADE_BUILT: /Game/Maps/MoonlitGlade")
