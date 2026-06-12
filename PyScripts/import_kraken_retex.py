"""Swap the Kraken's clay coat for the canon paint (retexture, original UVs).
Same asset names -> M_KrakenPBR picks the new maps up without a single rewire.
"""
import os
import unreal

EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
SRC = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\kraken\retex"
DEST = "/Game/Art/KrakenSkelV1"
TEXTURES = {
    "T_Kraken_BaseColor": ("kraken_retex_tex0_base_color.png", True),
    "T_Kraken_Normal": ("kraken_retex_tex0_normal.png", False),
    "T_Kraken_Roughness": ("kraken_retex_tex0_roughness.png", False),
    "T_Kraken_Metallic": ("kraken_retex_tex0_metallic.png", False),
}

for name, (rel, srgb) in TEXTURES.items():
    f = os.path.join(SRC, rel)
    if not os.path.isfile(f):
        print(f"KRKRETEX {name}: MISSING {f}")
        continue
    t = unreal.AssetImportTask()
    t.filename = f
    t.destination_path = DEST
    t.destination_name = name
    t.automated = True
    t.save = True
    t.replace_existing = True
    tools.import_asset_tasks([t])
    tex = unreal.load_asset(f"{DEST}/{name}")
    if tex:
        tex.set_editor_property("srgb", srgb)
        if "Normal" in name:
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        EAL.save_loaded_asset(tex)
        print(f"KRKRETEX {name}: swapped (srgb={srgb})")
print("KRKRETEX_DONE")
