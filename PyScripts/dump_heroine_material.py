"""Read-only dump of SCB2Heroine material setup. Prints HMAT: prefixed lines."""
import unreal

def log(msg):
    unreal.log("HMAT: " + str(msg))

# --- 1. Skeletal mesh material slots ---
mesh_path = "/Game/Art/HeroineSkelV2/SCB2Heroine"
mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
if mesh is None:
    log("ERROR: could not load mesh " + mesh_path)
else:
    log("MESH loaded: " + mesh.get_path_name())
    try:
        mats = mesh.get_editor_property("materials")
        log("MESH material slot count: %d" % len(mats))
        for i, sm in enumerate(mats):
            mi = sm.get_editor_property("material_interface")
            slot = sm.get_editor_property("material_slot_name")
            mi_path = mi.get_path_name() if mi else "<None>"
            log("SLOT %d name=%s material=%s" % (i, slot, mi_path))
    except Exception as e:
        log("ERROR reading mesh.materials: %r" % e)

# --- 2. Material editor properties ---
mat_path = "/Game/Art/HeroineSkelV2/Material_1"
mat = unreal.EditorAssetLibrary.load_asset(mat_path)
if mat is None:
    log("ERROR: could not load material " + mat_path)
else:
    log("MATERIAL loaded: " + mat.get_path_name())
    for prop in ["blend_mode", "shading_model", "two_sided", "used_with_skeletal_mesh"]:
        try:
            val = mat.get_editor_property(prop)
            log("MAT PROP %s = %s" % (prop, val))
        except Exception as e:
            log("MAT PROP %s ERROR: %r" % (prop, e))

    # --- 3. Material property input connections ---
    props = [
        ("MP_BASE_COLOR", unreal.MaterialProperty.MP_BASE_COLOR),
        ("MP_EMISSIVE_COLOR", unreal.MaterialProperty.MP_EMISSIVE_COLOR),
        ("MP_OPACITY", unreal.MaterialProperty.MP_OPACITY),
        ("MP_OPACITY_MASK", unreal.MaterialProperty.MP_OPACITY_MASK),
        ("MP_ROUGHNESS", unreal.MaterialProperty.MP_ROUGHNESS),
        ("MP_METALLIC", unreal.MaterialProperty.MP_METALLIC),
        ("MP_SPECULAR", unreal.MaterialProperty.MP_SPECULAR),
        ("MP_NORMAL", unreal.MaterialProperty.MP_NORMAL),
    ]
    for name, prop in props:
        try:
            node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, prop)
            if node is None:
                log("INPUT %s connected=False" % name)
            else:
                log("INPUT %s connected=True node_class=%s node=%s" % (
                    name, node.get_class().get_name(), node.get_name()))
        except Exception as e:
            log("INPUT %s ERROR: %r" % (name, e))

# --- 4. Texture inventory under /Game/Art/HeroineSkelV2 ---
try:
    assets = unreal.EditorAssetLibrary.list_assets("/Game/Art/HeroineSkelV2", recursive=True)
    log("ASSET LIST count=%d" % len(assets))
    for ap in assets:
        log("ASSET %s" % ap)
        obj = unreal.EditorAssetLibrary.load_asset(ap)
        if obj is None:
            log("  (failed to load)")
            continue
        if isinstance(obj, unreal.Texture2D):
            try:
                sx = obj.blueprint_get_size_x()
                sy = obj.blueprint_get_size_y()
            except Exception:
                sx = sy = -1
            try:
                srgb = obj.get_editor_property("srgb")
            except Exception as e:
                srgb = "ERR %r" % e
            try:
                comp = obj.get_editor_property("compression_settings")
            except Exception as e:
                comp = "ERR %r" % e
            log("TEX2D name=%s size=%dx%d srgb=%s compression=%s" % (
                obj.get_name(), sx, sy, srgb, comp))
except Exception as e:
    log("ERROR listing assets: %r" % e)

log("DONE")
