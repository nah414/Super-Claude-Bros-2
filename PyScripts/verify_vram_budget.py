"""Read-only check that the 8 GB-safe render budget is actually set in the project config.
Pure Python (no Unreal needed) — run it directly:
    python PyScripts/verify_vram_budget.py
It parses Config/DefaultDeviceProfiles.ini (authoritative) + Config/DefaultEngine.ini and asserts
the cvars that keep World 1 inside the RTX 5070 Laptop's 8 GB. Prints VRAM_BUDGET_VERIFY: PASS/FAIL.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "..", "Config")
DEVPROF = os.path.join(CONFIG, "DefaultDeviceProfiles.ini")
ENGINE = os.path.join(CONFIG, "DefaultEngine.ini")


def cvars(path):
    """Return {cvar_lower: value_str} from +CVars=Name=Val and bare Name=Val render lines."""
    out = {}
    if not os.path.isfile(path):
        return out
    for raw in open(path, encoding="utf-8", errors="ignore"):
        line = raw.strip()
        if line.startswith(";") or not line:
            continue
        m = re.match(r"\+?CVars=([\w.]+)=([^\s;]+)", line)
        if not m:
            m = re.match(r"(r\.[\w.]+)=([^\s;]+)", line)
        if m:
            out[m.group(1).lower()] = m.group(2)
    return out


dp = cvars(DEVPROF)
en = cvars(ENGINE)


def eff(name):
    """DeviceProfile is authoritative; fall back to DefaultEngine.ini."""
    k = name.lower()
    return dp.get(k, en.get(k))


def as_num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


fails, warns = [], []


def need(name, ok, why):
    v = eff(name)
    if v is None:
        fails.append(f"{name} not set ({why})")
    elif not ok(v):
        fails.append(f"{name}={v} ({why})")
    else:
        print(f"  OK  {name}={v}")


truthy = lambda v: str(v).lower() in ("1", "true")

need("r.Streaming.LimitPoolSizeToVRAM", truthy, "must clamp the texture pool to VRAM")
need("r.Streaming.PoolSize", lambda v: (as_num(v) or 9999) <= 1400, "pool <= 1400 MB on 8 GB")
need("r.RayTracing.ResidentGeometryMemoryPoolSizeInMB",
     lambda v: (as_num(v) or 9999) <= 640, "RT reflection-BVH pool <= 640 MB (was 1800)")
need("r.Lumen.FinalGather.SampleResolutionScale", lambda v: (as_num(v) or 9) <= 1.0, "<= 1.0")
need("r.Lumen.Reflections.SampleResolutionScale", lambda v: (as_num(v) or 9) <= 1.0, "<= 1.0")
need("r.Shadow.Virtual.SMRT.RayCountLocal", lambda v: (as_num(v) or 99) <= 8, "<= 8 local SMRT rays")

# Hybrid Lumen intent: GI software-cache + hardware-RT reflections.
if not truthy(eff("r.Lumen.Reflections.HardwareRayTracing") or "0"):
    warns.append("r.Lumen.Reflections.HardwareRayTracing not True (Adam picked HW reflections)")
if eff("r.Lumen.HardwareRayTracing.LightingMode") not in ("1", None):
    warns.append(f"r.Lumen.HardwareRayTracing.LightingMode={eff('r.Lumen.HardwareRayTracing.LightingMode')} (want 1 = Hit Lighting for Reflections)")

# Sanity: the DeviceProfile must exist and declare the Windows profile.
if not os.path.isfile(DEVPROF):
    fails.append("Config/DefaultDeviceProfiles.ini missing (the authoritative home)")
elif "Windows DeviceProfile" not in open(DEVPROF, encoding="utf-8", errors="ignore").read():
    fails.append("[Windows DeviceProfile] section missing — profile won't apply")

for w in warns:
    print(f"  WARN {w}")

if fails:
    print("VRAM_BUDGET_VERIFY: FAIL")
    for f in fails:
        print(f"  - {f}")
    print("VRAM_BUDGET_VERIFY_DONE")
    sys.exit(1)
print("VRAM_BUDGET_VERIFY: PASS")
print("VRAM_BUDGET_VERIFY_DONE")
