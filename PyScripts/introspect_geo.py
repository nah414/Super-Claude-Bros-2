import unreal
libs = [n for n in dir(unreal) if n.startswith("GeometryScript_")]
for n in sorted(libs):
    cls = getattr(unreal, n)
    if any("append_buffers" in m for m in dir(cls)):
        print(f"GEOFOUND: {n} has append_buffers_to_mesh")
print("GEOLIBS: " + ", ".join(sorted(libs)[:40]))
