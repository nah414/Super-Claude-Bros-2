import unreal
DEST = "/Game/Art/HeroSkel"
skel = unreal.load_asset(f"{DEST}/SCB2Hero_Skeleton")
print(f"SKEL_ASSET: {skel.get_name() if skel else 'MISSING'}")
reg = unreal.AssetRegistryHelpers.get_asset_registry()
assets = reg.get_assets_by_path(DEST, recursive=False)
for ad in sorted(assets, key=lambda x: str(x.asset_name)):
    name = str(ad.asset_name)
    cls = str(ad.asset_class_path.asset_name)
    line = f"ASSET {name}: {cls}"
    if cls == "AnimSequence":
        a = unreal.load_asset(f"{DEST}/{name}")
        s = a.get_editor_property("skeleton") if a else None
        line += f" len={a.get_play_length():.2f}s skeleton={s.get_name() if s else 'NONE'}"
    print(line)
print("STATE_DONE")
