"""READ-ONLY audit of the per-clip mesh/physics duplication in /Game/Art/*SkelV*.

The anim FBX importer (import_*_native.py, FBXIT_ANIMATION) leaves a full SkeletalMesh
copy ("A_<Char>_<Clip>") and its PhysicsAsset next to every real AnimSequence
("A_<Char>_<Clip>_Anim"). The game loads only SCB2<Char> + the *_Anim sequences, so the
mesh/physics copies are dead weight (~4.6 GB).

This script NEVER deletes or edits anything. It uses the AssetRegistry to:
  1. classify every asset in each *SkelV* folder,
  2. mark the dup meshes (SkeletalMesh that has a sibling <name>_Anim) and dup physics,
  3. prove no *external* asset (outside the dup's own clip-family) references a dup, AND
  4. the decisive check: prove no KEPT asset (SCB2 mesh / skeleton / _Anim / material /
     texture) depends on a dup — i.e. deleting the dups leaves zero dangling references.

Output contract (grep these from the headless log):
  AUDIT_FOLDER: <folder> dups=<n> physics=<n> keep=<n>
  AUDIT_EXTERNAL_REF: <dup> <- <referencer>          (a problem if printed)
  AUDIT_KEEP_DEPENDS_ON_DUP: <keep> -> <dup>          (a problem if printed)
  AUDIT_RESULT: SAFE_TO_DELETE | UNSAFE
Full machine-readable report is written to _prep/mesh_dup_audit.json.
"""
import json
import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
ar.scan_paths_synchronous(["/Game/Art"], force_rescan=True)
ar.wait_for_completion()

DEP_OPTS = unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=True,
    include_hard_package_references=True,
    include_searchable_names=False,
    include_soft_management_references=False,
    include_hard_management_references=False,
)


def class_of(ad):
    try:
        return str(ad.asset_class_path.asset_name)
    except Exception:
        return str(getattr(ad, "asset_class", ""))


def referencers(pkg):
    return [str(x) for x in ar.get_referencers(unreal.Name(pkg), DEP_OPTS)]


def dependencies(pkg):
    return [str(x) for x in ar.get_dependencies(unreal.Name(pkg), DEP_OPTS)]


# Discover the *SkelV* folders under /Game/Art.
folders = [str(p) for p in ar.get_sub_paths("/Game/Art", recurse=False) if "SkelV" in str(p)]
folders.sort()

delete_set = set()          # package names slated for deletion (mesh dups + dup physics)
keep_set = set()            # package names we keep
report = {"folders": {}, "external_refs": [], "keep_depends_on_dup": []}

for folder in folders:
    assets = ar.get_assets_by_path(unreal.Name(folder), recursive=False,
                                   include_only_on_disk_assets=False)
    by_name = {}            # asset_name -> (class, package_name)
    for ad in assets:
        by_name[str(ad.asset_name)] = (class_of(ad), str(ad.package_name))
    anim_bases = {n[:-5] for n in by_name if n.endswith("_Anim")}  # strip "_Anim"

    dup_meshes, dup_physics, keep = [], [], []
    for name, (cls, pkg) in by_name.items():
        is_dup_mesh = cls == "SkeletalMesh" and name in anim_bases and not name.startswith("SCB2")
        is_dup_phys = (cls == "PhysicsAsset" and name.endswith("_PhysicsAsset")
                       and name[:-13] in anim_bases and name.startswith("A_"))
        if is_dup_mesh:
            dup_meshes.append(pkg); delete_set.add(pkg)
        elif is_dup_phys:
            dup_physics.append(pkg); delete_set.add(pkg)
        else:
            keep.append(pkg); keep_set.add(pkg)
    report["folders"][folder] = {
        "dup_meshes": sorted(dup_meshes),
        "dup_physics": sorted(dup_physics),
        "keep": sorted(keep),
    }
    print(f"AUDIT_FOLDER: {folder} dups={len(dup_meshes)} physics={len(dup_physics)} keep={len(keep)}")

# (3) external referencers: any referencer of a dup that is NOT itself slated for deletion.
for pkg in sorted(delete_set):
    ext = [r for r in referencers(pkg) if r not in delete_set]
    for r in ext:
        report["external_refs"].append({"dup": pkg, "referenced_by": r})
        print(f"AUDIT_EXTERNAL_REF: {pkg} <- {r}")

# (4) the decisive direction: any KEPT asset that depends on a dup.
for pkg in sorted(keep_set):
    bad = [d for d in dependencies(pkg) if d in delete_set]
    for d in bad:
        report["keep_depends_on_dup"].append({"keep": pkg, "depends_on": d})
        print(f"AUDIT_KEEP_DEPENDS_ON_DUP: {pkg} -> {d}")

safe = not report["external_refs"] and not report["keep_depends_on_dup"]
report["summary"] = {
    "folders": len(folders),
    "dup_meshes_total": sum(len(v["dup_meshes"]) for v in report["folders"].values()),
    "dup_physics_total": sum(len(v["dup_physics"]) for v in report["folders"].values()),
    "external_refs": len(report["external_refs"]),
    "keep_depends_on_dup": len(report["keep_depends_on_dup"]),
    "safe_to_delete": safe,
}
out = r"C:\Users\Atomn\mario2\_prep\mesh_dup_audit.json"
try:
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"AUDIT_REPORT_WRITTEN: {out}")
except Exception as e:
    print(f"AUDIT_WRITE_SKIPPED: {e}")

print("AUDIT_SUMMARY: " + json.dumps(report["summary"], sort_keys=True))
print("AUDIT_RESULT: " + ("SAFE_TO_DELETE" if safe else "UNSAFE"))
