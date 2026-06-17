"""Cap IndustrialKit texture resolution (2048 color/normal, 1024 others) for VRAM/cook size."""
import unreal

EAL = unreal.EditorAssetLibrary
n = 0
for ap in EAL.list_assets("/Game/Art/IndustrialKit", recursive=True):
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
print(f"INDUSTRIALKIT_TEX_OPT_DONE: {n} textures capped")
