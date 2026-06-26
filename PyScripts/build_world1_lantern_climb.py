"""WORLD 1 — THE LANTERN CLIMB (Emberwell Canyon). Builds the vertical canyon: a switchback
up the west cliff, a gondola crossing, a spire spiral to the FIRST LANTERN at the crown.

Two ways to run:
 * STANDALONE (default): `-run=pythonscript` on this file rebuilds /Game/Maps/LanternClimb.
 * MERGED: another script sets `builtins._LC_SUPPRESS_AUTORUN=True`, imports this module, and
   calls `build_canyon(into_existing=True, origin=(OX,OY,OZ), spawn=False, add_atmosphere=False)`
   to append the canyon into an already-loaded map (e.g. NeonCity) at a world offset.

Design rules learned the hard way:
 * Critical path = WALKABLE RAMPS (<=~21deg) + flat landings; no blind-jump tuning.
 * SOLID wet floor across the canyon bottom — falling is a setback, never a death pit.
 * M2 fix: switchback FLIGHTS step laterally in X as they rise (WX0 + i*WX_STEP) so each flight
   is parallel to and OFFSET from the one below — a real fire-escape staircase, not a vertical
   stack at one X.
 * Meshy props: bbox-grounded, NO Nanite, decoratives no-collision + RT off; skip-if-missing.
"""
import builtins
import math
import unreal
from collections import Counter

_AUTORUN = not getattr(builtins, "_LC_SUPPRESS_AUTORUN", False)

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MAP = "/Game/Maps/LanternClimb"
KIT = "/Game/Art/LanternClimbKit"

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")


def mat(name):
    return EAL.load_asset(f"/Game/Art/CityMat/{name}")


# M1 gritty-industrial skins: concrete walkways/cliffs, rusted metal accents.
M_ASPHALT = mat("M_WetAsphalt")
M_SIDEWALK = mat("M_Concrete") or mat("M_Sidewalk")
M_BUILD = mat("M_Concrete") or M_SIDEWALK
M_BUILD2 = mat("M_RustMetal") or M_SIDEWALK
M_WINDOW = mat("M_IndustrialWindow") or M_BUILD
M_WATER = mat("M_HoloBillboard") or M_ASPHALT

LANTERN_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.Lantern")
NETMGR_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.LightNetworkManager")
FLAGPOLE_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.FlagpoleGoal")

# World offset applied by build_canyon() to every placed actor (0,0,0 = standalone).
OX = OY = OZ = 0.0
P = Counter()


def setp(actor, names, value):
    for nm in names:
        try:
            actor.set_editor_property(nm, value)
            return True
        except Exception:
            continue
    return False


def block(x, y, z, sx, sy, sz, label, material=M_BUILD, solid=True, rt=False, hidden=False):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x + OX, y + OY, z + OZ))
    a.static_mesh_component.set_static_mesh(CUBE)
    a.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    if material:
        a.static_mesh_component.set_material(0, material)
    if not rt:
        a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    if hidden:
        a.set_actor_hidden_in_game(True)
    if not solid:
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.set_actor_label(f"LC_{label}")
    P[label.split('_')[0]] += 1
    return a


def ramp(p0, p1, width, label, material=M_SIDEWALK):
    """A walkable tilted slab from p0 (low) to p1 (high), in canyon-local coords (offset applied)."""
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    R = math.hypot(dx, dy)
    L = math.hypot(R, dz)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, R))
    mid = ((x0 + x1) / 2 + OX, (y0 + y1) / 2 + OY, (z0 + z1) / 2 - 18.0 + OZ)
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*mid))
    a.static_mesh_component.set_static_mesh(CUBE)
    a.set_actor_rotation(unreal.Rotator(0.0, pitch, yaw), False)  # (roll, pitch, yaw)
    a.set_actor_scale3d(unreal.Vector(L / 100.0, width / 100.0, 0.36))
    if material:
        a.static_mesh_component.set_material(0, material)
    a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    a.set_actor_label(f"LC_{label}")
    P["ramp"] += 1
    return a


def landing(cx, cy, ztop, w, d, label, material=M_SIDEWALK):
    """Flat platform whose TOP surface sits at ztop (offset applied via block)."""
    return block(cx, cy, ztop - 20.0, w, d, 40.0, label, material=material, rt=False)


def lantern(x, y, label, *, z, checkpoint=False, goal=False, dark=False, guttering=False,
            relight_radius=320.0, auto=9.0, scale=1.0, intensity=1100.0, radius=620.0):
    a = eas.spawn_actor_from_class(LANTERN_CLASS, unreal.Vector(x + OX, y + OY, z + OZ))
    setp(a, ["lit_intensity", "LitIntensity"], intensity)
    setp(a, ["lit_radius", "LitRadius"], radius)
    setp(a, ["relight_by_hero_radius", "RelightByHeroRadius"], relight_radius)
    setp(a, ["auto_relight_seconds", "AutoRelightSeconds"], auto)
    setp(a, ["is_checkpoint", "b_is_checkpoint", "bIsCheckpoint"], checkpoint)
    setp(a, ["is_world_goal", "b_is_world_goal", "bIsWorldGoal"], goal)
    setp(a, ["start_dark", "b_start_dark", "bStartDark"], dark)
    setp(a, ["start_guttering", "b_start_guttering", "bStartGuttering"], guttering)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_label(f"LC_Lantern_{label}")
    P["lantern"] += 1
    return a


def flagpole(x, y, label, *, z, pole_height=14.0, raise_seconds=1.5, scale=1.0):
    """The crown VICTORY POLE — the Mario flag finish. Touching it (or pressing E) raises the
    banner up the mast and wins the world via the same idempotent hook as the lantern relight.
    Rides the OX/OY/OZ merge offset like lantern(), so co-locates with the goal lantern."""
    a = eas.spawn_actor_from_class(FLAGPOLE_CLASS, unreal.Vector(x + OX, y + OY, z + OZ))
    setp(a, ["pole_height", "PoleHeight"], pole_height)
    setp(a, ["raise_seconds", "RaiseSeconds"], raise_seconds)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_label(f"LC_Flagpole_{label}")
    P["flagpole"] += 1
    return a


def fprop(name, x, y, scale, yaw=0.0, z=None, solid=False, kit=None, tag=None):
    """A Meshy kit prop (LanternClimbKit by default, or `kit` path); bbox-grounded unless z given.
    Skips (logs) if the kit isn't imported yet. `tag` stamps an actor tag (e.g. "Climbable")."""
    base = kit or KIT
    sm = EAL.load_asset(f"{base}/{name}/SM_{name}")
    if not sm:
        unreal.log_warning(f"KIT_MISSING {name} (skipped)")
        return None
    bb = sm.get_bounding_box()
    zz = (0.0 - bb.min.z * scale) if z is None else z
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(x + OX, y + OY, zz + OZ))
    a.static_mesh_component.set_static_mesh(sm)
    a.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    if not solid:
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    if tag:
        try:
            a.set_editor_property("tags", [unreal.Name(tag)])
        except Exception as e:
            unreal.log_warning(f"tag {tag} skip: {e}")
    a.set_actor_label(f"LC_Prop_{name}_{P['prop']}")
    P["prop"] += 1
    return a


def shell(cx, cy, ztop, w, d, h, label, door_yaw=0.0):
    """Enterable room: floor + roof + 3 walls + a front wall with a door gap + interior dressing."""
    T = 40.0
    block(cx, cy, ztop + h / 2, w, d, 30.0, f"{label}_roof")
    block(cx, cy, ztop - 20, w, d, 40.0, f"{label}_floor", material=M_SIDEWALK)
    sides = {0: ("fx", cx + w / 2, cy, T, d), 180: ("bx", cx - w / 2, cy, T, d),
             90: ("fy", cx, cy + d / 2, w, T), 270: ("by", cx, cy - d / 2, w, T)}
    dw, dh = 360.0, 520.0
    for ang, (tag, wx, wy, sx, sy) in sides.items():
        if ang == door_yaw:
            if sx > sy:
                seg = (sx - dw) / 2
                block(wx - (dw / 2 + seg / 2), wy, ztop + h / 2, seg, sy, h, f"{label}_dL")
                block(wx + (dw / 2 + seg / 2), wy, ztop + h / 2, seg, sy, h, f"{label}_dR")
                block(wx, wy, ztop + dh + (h - dh) / 2, dw, sy, h - dh, f"{label}_dT")
            else:
                seg = (sy - dw) / 2
                block(wx, wy - (dw / 2 + seg / 2), ztop + h / 2, sx, seg, h, f"{label}_dL")
                block(wx, wy + (dw / 2 + seg / 2), ztop + h / 2, sx, seg, h, f"{label}_dR")
                block(wx, wy, ztop + dh + (h - dh) / 2, sx, dw, h - dh, f"{label}_dT")
        else:
            block(wx, wy, ztop + h / 2, sx, sy, h, f"{label}_{tag}", material=M_WINDOW)
    lantern(cx, cy, f"in_{label}", z=ztop + 120, relight_radius=360.0, scale=0.9)
    fprop("cargo_crate_set", cx - w * 0.25, cy + d * 0.2, 1.0)
    P["shell"] += 1


# Canyon-local constants (shared by the body + verifier expectations).
FLOOR_TOP = 350.0
ZTOP_SWITCH = 6000.0
SPIRE_BASE_Z = 6000.0
CROWN_Z = 8650.0
# M2 switchback: flights step laterally in X as they climb (no vertical stacking).
WX0, WX_STEP = -1950.0, 155.0
Y_LO, Y_HI = -2200.0, 2200.0
RAMPS = 10
PATH_W = 500.0
SWITCH_TOP_X = WX0 + (RAMPS - 1) * WX_STEP   # X of the last (top) flight ~ -555


def build_canyon(origin=(0.0, 0.0, 0.0), into_existing=False, spawn=True,
                 add_atmosphere=True, save=True, entry_gap_y=None):
    """Build the canyon. origin offsets every actor; into_existing appends into the loaded map.
    entry_gap_y (canyon-local Y) cuts a walk-through doorway in the WEST cliff so the merged
    boulevard can lead into the canyon floor (None = sealed shaft, the standalone)."""
    global OX, OY, OZ, P
    OX, OY, OZ = origin
    P = Counter()

    if not into_existing:
        if EAL.does_asset_exist("/Game/Maps/_Scratch"):
            EAL.delete_asset("/Game/Maps/_Scratch")
        assert les.new_level("/Game/Maps/_Scratch"), "SCRATCH_FAILED"
        if EAL.does_asset_exist(MAP):
            assert EAL.delete_asset(MAP), "DELETE_OLD_FAILED"
        assert les.new_level(MAP), "NEW_MAP_FAILED"

    # ---- canyon shell: solid wet floor + cosmetic water + cliffs + end caps ----
    block(0, 0, FLOOR_TOP - 150, 5200, 6000, 300, "Floor", material=M_ASPHALT)
    block(0, 0, FLOOR_TOP + 6, 4600, 5400, 12, "Water", material=M_WATER, solid=False)
    if entry_gap_y is None:
        block(-2300, 0, 4600, 360, 6000, 9200, "CliffW", material=M_BUILD)
    else:                                            # doorway in the west cliff for the merge entry
        gw, gh = 900.0, 1000.0
        y_s, y_n = entry_gap_y - gw / 2, entry_gap_y + gw / 2
        block(-2300, (-3000 + y_s) / 2, 4600, 360, y_s + 3000, 9200, "CliffW_S", material=M_BUILD)
        block(-2300, (y_n + 3000) / 2, 4600, 360, 3000 - y_n, 9200, "CliffW_N", material=M_BUILD)
        block(-2300, entry_gap_y, (gh + 9200) / 2, 360, gw, 9200 - gh, "CliffW_lintel", material=M_BUILD)
    block(2300, 0, 4600, 360, 6000, 9200, "CliffE", material=M_BUILD2)
    block(0, -2950, 4600, 5200, 360, 9200, "CapS", material=M_BUILD)
    block(0, 2950, 4600, 5200, 360, 9200, "CapN", material=M_BUILD2)

    # ---- THE WALKABLE CLIMB: laterally-stepped switchback (M2 fix) ----
    z = FLOOR_TOP
    wp = [(0.0, -2600.0, z), (WX0, Y_LO, z)]   # spawn slot -> base of flight 0
    dz = (ZTOP_SWITCH - z) / RAMPS
    ydir = 1
    for i in range(RAMPS):
        wx_i = WX0 + i * WX_STEP
        yn = Y_HI if ydir > 0 else Y_LO
        zn = z + dz
        wp.append((wx_i, yn, zn))                              # climbing flight i (at wx_i)
        if i < RAMPS - 1:
            wp.append((WX0 + (i + 1) * WX_STEP, yn, zn))       # flat balcony turn -> next flight's X
        z = zn
        ydir = -ydir
    wp.append((SWITCH_TOP_X, 0.0, ZTOP_SWITCH))                # last flight -> centre for the gondola
    for i in range(len(wp) - 1):
        ramp(wp[i], wp[i + 1], PATH_W, f"Ramp_{i:02d}")
    for i, (px, py, pz) in enumerate(wp):
        landing(px, py, pz, PATH_W + 160, PATH_W + 160, f"Land_{i:02d}")
        if 1 < i < len(wp) - 1 and i % 3 == 1:                 # a checkpoint lantern every few turns
            gutter = (i % 6 == 1)                              # half guttering (relight to claim), half lit
            lantern(px + (120 if px < 0 else -120), py, f"cp_{i:02d}", z=pz + 60,
                    checkpoint=True, guttering=gutter, relight_radius=0.0 if gutter else 320.0,
                    auto=0.0 if gutter else 9.0, intensity=1400.0, radius=640.0)

    # ---- gondola crossing -> spire ----
    ramp((SWITCH_TOP_X, 0.0, ZTOP_SWITCH), (-650.0, 0.0, SPIRE_BASE_Z), PATH_W, "GondApproach")
    block(-325.0, 0.0, SPIRE_BASE_Z - 20, 760, 460, 40, "GondDeck", material=M_SIDEWALK)
    fprop("cable_car_gondola", -325.0, 0.0, 2.4, yaw=90.0, z=SPIRE_BASE_Z - 10, solid=False)

    # ---- the spire + crown goal ----
    block(0, 0, (SPIRE_BASE_Z + CROWN_Z) / 2, 460, 460, CROWN_Z - SPIRE_BASE_Z, "SpireCore",
          material=M_BUILD2)   # the hero tower in rusted industrial metal
    SR = 760.0
    SEGS = 6
    spire_wp = [(-650.0, 0.0, SPIRE_BASE_Z)]
    for i in range(SEGS + 1):
        ang = math.radians(180 + 90 * i)
        spire_wp.append((SR * math.cos(ang), SR * math.sin(ang),
                         SPIRE_BASE_Z + (CROWN_Z - 130 - SPIRE_BASE_Z) * i / SEGS))
    spire_wp.append((0.0, 0.0, CROWN_Z - 90))
    for i in range(len(spire_wp) - 1):
        ramp(spire_wp[i], spire_wp[i + 1], 440, f"Spiral_{i:02d}")
    for i, (px, py, pz) in enumerate(spire_wp):
        landing(px, py, pz, 500, 500, f"SpiralLand_{i:02d}")
    # warm lanterns ALL the way up the spiral staircase: one at every landing AND one between
    # each pair, brighter (Adam: "we still need more lights along our spiral staircase").
    for i in range(1, len(spire_wp)):
        px, py, pz = spire_wp[i]
        for off in (270.0, -270.0):                    # a torch on BOTH sides of every intersection
            lantern(px + off, py, f"spire_{i:02d}_{int(off)}", z=pz + 50, relight_radius=300.0,
                    auto=9.0, scale=0.85, intensity=1500.0, radius=760.0)
    for i in range(len(spire_wp) - 1):
        ax, ay, az = spire_wp[i]
        bx, by, bz = spire_wp[i + 1]
        lantern((ax + bx) / 2, (ay + by) / 2, f"spiremid_{i:02d}", z=(az + bz) / 2 + 50,
                relight_radius=300.0, auto=9.0, scale=0.7, intensity=1200.0, radius=660.0)

    fprop("first_lantern_spire", 0.0, 0.0, 14.0, z=SPIRE_BASE_Z, solid=False)
    fprop("waygate_arch", 0.0, 560.0, 4.0, yaw=0.0, z=CROWN_Z - 120, solid=False)
    # The crown goal is a GUTTERING beacon (dim, dying flame) — visible from the climb so the
    # player can aim for it, but not Lit, so the hold-E rite to fully kindle it is the win.
    lantern(0.0, 0.0, "FIRST", z=CROWN_Z, goal=True, guttering=True, relight_radius=0.0, auto=0.0,
            scale=3.0, intensity=7000.0, radius=3000.0)
    # Mario-style FLAG CAPTURE, standing on the crown landing beside the beacon. Base is flush
    # with the final landing (CROWN_Z-90) so the hero overlaps the capture trigger on arrival;
    # walk into it (or press E) to raise the banner and win.
    flagpole(0.0, 0.0, "CROWN", z=CROWN_Z - 90.0, pole_height=14.0, raise_seconds=1.5)

    # ---- 8 enterable shells ----
    shell(-1850, -1400, 900, 900, 760, 560, "S1_basement", door_yaw=0)
    shell(-1850, -200, 950, 900, 760, 560, "S2_noodle", door_yaw=0)
    shell(-1700, 1500, 2600, 900, 760, 560, "S3_workshop", door_yaw=90)
    shell(-1100, 1500, 2600, 900, 760, 560, "S4_pawn", door_yaw=0)
    shell(1700, 700, 4000, 900, 760, 560, "S5_arcade", door_yaw=180)
    shell(1500, -700, 4800, 900, 760, 560, "S6_fixer", door_yaw=180)
    shell(950, -1500, 5300, 900, 760, 560, "S7_bunk", door_yaw=270)
    shell(700, 600, 5600, 820, 720, 540, "S8_pumproom", door_yaw=90)

    # ---- Meshy dressing (ground clutter on the FLOOR/landings only; M5 adds wall climb-architecture) ----
    fprop("hover_car_textured", 700, -1800, 2.2, yaw=28, z=FLOOR_TOP + 10)
    fprop("sunken_shopfront", -700, -1500, 2.6, yaw=12, z=FLOOR_TOP - 30)
    fprop("sunken_shopfront", 900, 900, 2.6, yaw=-100, z=FLOOR_TOP - 30)
    fprop("wet_street_shrine", -1900, -2300, 1.5, yaw=40, z=FLOOR_TOP + 8)
    fprop("food_cart_ramen", -1500, -700, 1.7, yaw=0, z=FLOOR_TOP + 4)      # on the floor, not the wall
    fprop("food_cart_ramen", 1200, 500, 1.7, yaw=180, z=FLOOR_TOP + 4)      # was z=4400 on the cliff (M5 fix)
    # decorative neon sign clusters high on the cliffs (non-solid; the SOLID climb-architecture lands in M5)
    for k, (cx, sgn) in enumerate(((-2050, 1), (2050, -1))):
        for j in range(4):
            fprop("neon_sign_cluster", cx, -1400 + j * 1000, 1.8, yaw=90 * sgn, z=900 + j * 1500)
    for zz in (2200, 4200, 6200):
        fprop("overhead_cables", 0, -600 + (zz % 900), 2.4, yaw=0, z=zz)
    for (lx, ly, lz) in ((WX0 + 200, -1400, FLOOR_TOP), (-900, 1400, 1700), (1600, 0, 4000)):
        fprop("street_lantern", lx, ly, 1.8, z=lz)

    # ---- M5: SOLID climbable wall architecture (tagged "Climbable" for the M7 gate) ----
    # Replaces the old food-cart-on-the-wall clutter with proper city architecture you can climb.
    CLIMB_KIT = "/Game/Art/ClimbKit"
    facade = ["fire_escape_run", "tenement_balcony_climb", "brick_ledge_stack", "scaffold_run",
              "pipe_rung_ladder", "vent_duct_ledges", "drainpipe_climb", "rebar_handholds"]
    # a tall climbable facade up the EAST cliff (the free wall) -> a real alternate climb route
    for j in range(7):
        fprop(facade[j % len(facade)], 2080, -1700 + (j % 3) * 1500, 8.0, yaw=180,
              z=FLOOR_TOP + j * 1250, solid=True, kit=CLIMB_KIT, tag="Climbable")
    # climbable city facade on the south end cap
    for j, nm in enumerate(("tenement_balcony_climb", "fire_escape_run", "brick_ledge_stack")):
        fprop(nm, -1200 + j * 1400, -2740, 7.0, yaw=90, z=FLOOR_TOP + 400 + j * 1500,
              solid=True, kit=CLIMB_KIT, tag="Climbable")

    # ---- ambient warm lanterns along the climb ----
    for (lx, ly, lz) in ((WX0, -1600, FLOOR_TOP + 60), (-1500, 1600, 2200), (-1100, -600, 3400),
                         (-700, 800, 4600), (0, 0, SPIRE_BASE_Z + 80), (700, -1400, 5360)):
        lantern(lx, ly, f"amb_{int(lz)}", z=lz)

    # ---- atmosphere + lighting (skipped in merge mode; the host map already has it) ----
    if add_atmosphere:
        fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0))
        fc = fog.component
        fc.set_editor_property("enable_volumetric_fog", True)
        fc.set_editor_property("fog_density", 0.018)
        fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.012, 0.008, 0.018, 1.0))
        fog.set_actor_label("LC_Fog")
        eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0)).set_actor_label("LC_SkyAtm")
        sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 4000))
        sky.light_component.set_editor_property("real_time_capture", True)
        sky.light_component.set_intensity(0.06)
        sky.set_actor_label("LC_SkyLight")
        moon = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 9000))
        moon.set_actor_rotation(unreal.Rotator(0.0, -52.0, -35.0), False)
        moon.light_component.set_intensity(0.55)
        moon.light_component.set_light_color(unreal.LinearColor(1.0, 0.82, 0.6, 1.0))
        moon.set_actor_label("LC_Moon")
        ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
        ppv.set_editor_property("unbound", True)
        pps = ppv.get_editor_property("settings")

        def pp(name, value):
            try:
                pps.set_editor_property(f"override_{name}", True)
                pps.set_editor_property(name, value)
            except Exception as e:
                unreal.log_warning(f"pp skip {name}: {e}")

        pp("bloom_method", unreal.BloomMethod.BM_FFT)
        pp("bloom_intensity", 0.5)      # toned down — over-bright lights were glaring
        pp("auto_exposure_min_brightness", -1.5)
        pp("auto_exposure_max_brightness", -1.5)
        pp("film_grain_intensity", 0.12)
        pp("vignette_intensity", 0.4)
        pp("color_gain_shadows", unreal.Vector4(1.02, 0.95, 1.16, 1.0))
        pp("color_gain_highlights", unreal.Vector4(1.1, 1.02, 0.92, 1.0))
        ppv.set_editor_property("settings", pps)
        ppv.set_actor_label("LC_Post")

    # ---- spawn + systems ----
    if spawn:
        start = eas.spawn_actor_from_class(unreal.PlayerStart,
                                           unreal.Vector(0 + OX, -2600 + OY, FLOOR_TOP + 120 + OZ))
        start.set_actor_rotation(unreal.Rotator(0.0, 0.0, 90.0), False)
        start.set_actor_label("LC_PlayerStart")
    mgr = eas.spawn_actor_from_class(NETMGR_CLASS, unreal.Vector(0 + OX, 0 + OY, SPIRE_BASE_Z + OZ))
    mgr.set_actor_label("LC_LightNetworkManager")

    saved = les.save_current_level() if save else None
    if not into_existing and EAL.does_asset_exist("/Game/Maps/_Scratch"):
        EAL.delete_asset("/Game/Maps/_Scratch")
    print(f"LANTERN_CLIMB_BUILT: {dict(P)} origin={origin} merge={into_existing} saved={saved}")
    return P


if _AUTORUN:
    build_canyon()
