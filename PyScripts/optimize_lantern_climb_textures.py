"""Cap LanternClimbKit texture resolution so the premium 4K HD maps don't blow VRAM on an
8GB laptop GPU or bloat the cooked package. Base-color/normal -> 2048, the rest -> 1024.
The UE streamer already bounds in-VRAM size, but a hard cap keeps the cook lean + the
texture pool calm. Re-saves each texture."""
import unreal

EAL = unreal.EditorAssetLibrary
n = 0
for ap in EAL.list_assets("/Game/Art/LanternClimbKit", recursive=True):
    a = EAL.load_asset(ap)
    if isinstance(a, unreal.Texture2D):
        nm = a.get_name().lower()
        cap = 2048 if ("color" in nm or "normal" in nm or "albedo" in nm or "basecolor" in nm) else 1024
        try:
            a.set_editor_property("max_texture_size", cap)
            EAL.save_loaded_asset(a)
            n += 1
        except Exception as e:
            unreal.log_warning(f"TEX_CAP_SKIP {a.get_name()}: {e}")
print(f"TEX_OPT_DONE: {n} textures capped")
