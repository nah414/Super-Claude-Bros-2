# ============================================================================
# synth_audio.py -- Super Claude Bros 2 procedural audio pack (FREE, stdlib only)
# ----------------------------------------------------------------------------
# Generates the NEW audio for the World audio upgrade WITHOUT any paid service:
# pure Python standard library (wave / struct / math / random) -- no numpy, no
# Unreal. Run as plain CPython:
#
#     python PyScripts/synth_audio.py
#
# It writes 16-bit stereo WAVs into ArtSource/audio/, where import_art.py picks
# them up (files named *_loop get SoundWave.looping = True on import):
#
#     music_city_loop_v2   -- upgraded NeonCity synthwave loop (seamless)
#     music_victory_sting  -- the flag-capture / world-win fanfare (one-shot)
#     sfx_flag_raise       -- rising flourish as the banner climbs (one-shot)
#     sfx_capture          -- the claim hit on contact (one-shot)
#     sfx_enemy_defeat     -- the stomp/defeat "bwop" (one-shot)
#
# Design notes (the things that make synth audio not sound broken):
#  * Seamless loops: integer number of bars + an ~8 ms boundary crossfade that
#    folds an overflow tail back over the head, so the wrap point is continuous.
#  * DC removal (subtract the mean) + peak-normalize so nothing clips or thumps.
#  * Short attack/release on every note + fades on one-shots kill click.
#  * Fixed random.seed per asset -> byte-for-byte reproducible.
#
# Honest tradeoff: this is chiptune/synthwave synthesis -- free, reproducible,
# on-aesthetic for a retro platformer, but NOT pro-recorded fidelity. To go
# higher-fi, drop your own royalty-free WAVs into ArtSource/audio/ with these
# same names (zero code change) -- a paid audio service is the only other route
# and is halt-listed.
# ============================================================================

import math
import os
import random
import struct
import wave

SR = 44100  # sample rate

# ArtSource/audio next to this script's project (PyScripts/.. == project dir).
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), "ArtSource", "audio")


# ----------------------------------------------------------------------------
# Core DSP primitives
# ----------------------------------------------------------------------------

def midi_freq(n):
    """MIDI note number -> frequency in Hz (A4 = 69 = 440 Hz)."""
    return 440.0 * 2.0 ** ((n - 69) / 12.0)


def osc(kind, phase, duty=0.5):
    """One oscillator sample. `phase` is in CYCLES (float); we take its fraction."""
    p = phase - math.floor(phase)
    if kind == "sine":
        return math.sin(2.0 * math.pi * p)
    if kind == "square":
        return 1.0 if p < duty else -1.0
    if kind == "tri":
        return 4.0 * abs(p - 0.5) - 1.0
    if kind == "saw":
        return 2.0 * p - 1.0
    return 0.0


def adsr(i, n, a, d, s, r):
    """Attack/Decay/Sustain/Release envelope value (0..1) at sample i of an n-sample note."""
    at = max(int(a * SR), 1)
    dt = max(int(d * SR), 1)
    rt = max(int(r * SR), 1)
    if i < at:
        return i / at
    if i < at + dt:
        return 1.0 + (s - 1.0) * ((i - at) / dt)
    if i < n - rt:
        return s
    return s * max(0.0, (n - i) / rt)


def loop_samples(bars, beats_per_bar, bpm):
    """Exact sample count for an integer number of bars (so the loop tiles cleanly)."""
    return int(round(bars * beats_per_bar * (60.0 / bpm) * SR))


def render_voice(L, R, notes, kind, gain, bpm, pan=0.5, detune=0.0,
                 duty=0.5, env=(0.01, 0.05, 0.7, 0.08)):
    """Render a monophonic note list into stereo float buffers L/R (in place).
    `notes` is a list of (midi_or_None, beats); None = a rest. Stops at buffer end."""
    spb = 60.0 / bpm            # seconds per beat
    n = len(L)
    pos = 0
    for midi, beats in notes:
        nsamp = int(round(beats * spb * SR))
        if midi is not None:
            f = midi_freq(midi)
            for i in range(nsamp):
                idx = pos + i
                if idx >= n:
                    return
                t = i / SR
                e = adsr(i, nsamp, *env)
                s = osc(kind, f * t, duty)
                if detune > 0.0:
                    s = 0.6 * s + 0.4 * osc(kind, f * (1.0 + detune) * t, duty)
                v = s * e * gain
                L[idx] += v * (1.0 - pan)
                R[idx] += v * pan
        pos += nsamp


def render_sweep(L, R, f0, f1, dur, kind="square", gain=0.5, env=(0.005, 0.02, 0.7, 0.05)):
    """A single tone that glides exponentially from f0 to f1 over `dur` seconds."""
    n = int(dur * SR)
    phase = 0.0
    for i in range(n):
        if i >= len(L):
            break
        a = i / n
        f = f0 * (f1 / f0) ** a
        phase += f / SR
        e = adsr(i, n, *env)
        v = osc(kind, phase) * e * gain
        L[i] += v
        R[i] += v


def add_noise_sweep(L, R, dur, gain=0.25, rise=True):
    """Lowpassed white-noise whoosh, amplitude rising (or falling) across `dur`."""
    n = int(dur * SR)
    prev = 0.0
    for i in range(n):
        if i >= len(L):
            break
        a = i / n
        amp = a if rise else (1.0 - a)
        white = random.uniform(-1.0, 1.0)
        prev = 0.85 * prev + 0.15 * white      # one-pole lowpass -> a softer "wind"
        v = prev * amp * amp * gain
        L[i] += v
        R[i] += v


# ----------------------------------------------------------------------------
# Mix finishing
# ----------------------------------------------------------------------------

def finalize(L, R, target=0.89, soft=True):
    """DC-remove, optional soft-clip, peak-normalize to `target`. In place."""
    n = len(L)
    if n == 0:
        return
    mL = sum(L) / n
    mR = sum(R) / n
    for i in range(n):
        L[i] -= mL
        R[i] -= mR
    if soft:
        for i in range(n):
            L[i] = math.tanh(L[i])
            R[i] = math.tanh(R[i])
    peak = 1e-9
    for i in range(n):
        peak = max(peak, abs(L[i]), abs(R[i]))
    g = target / peak
    for i in range(n):
        L[i] *= g
        R[i] *= g


def seamless(L, R, total, xf_ms=8.0):
    """Fold the overflow tail (samples total..total+xf) back over the head with a crossfade,
    then return exactly `total` samples -- so end->start wraps with no click."""
    xf = int(xf_ms / 1000.0 * SR)
    for i in range(xf):
        if total + i >= len(L):
            break
        w = i / xf                              # 0 -> natural head, 1-w -> overflow tail
        L[i] = L[i] * w + L[total + i] * (1.0 - w)
        R[i] = R[i] * w + R[total + i] * (1.0 - w)
    return L[:total], R[:total]


def edge_fade(L, R, ms=4.0):
    """Tiny fade-in/out on a one-shot so the first/last sample can't click."""
    k = int(ms / 1000.0 * SR)
    n = len(L)
    for i in range(min(k, n)):
        f = i / k
        L[i] *= f
        R[i] *= f
        L[n - 1 - i] *= f
        R[n - 1 - i] *= f


def write_wav(name, L, R):
    """Write stereo 16-bit PCM to ArtSource/audio/<name>.wav."""
    path = os.path.join(OUT_DIR, name + ".wav")
    inter = []
    for i in range(len(L)):
        inter.append(int(max(-32768, min(32767, round(L[i] * 32767)))))
        inter.append(int(max(-32768, min(32767, round(R[i] * 32767)))))
    data = struct.pack("<%dh" % len(inter), *inter)
    with wave.open(path, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    print("  wrote {}  ({:.2f}s, {} frames)".format(name, len(L) / SR, len(L)))
    return path


# ----------------------------------------------------------------------------
# The five assets
# ----------------------------------------------------------------------------

def build_city_loop_v2():
    """Upgraded NeonCity track: a moody synthwave loop -- saw bass + square arp + tri pad
    over an Am - F - C - G progression. 4 bars, seamless."""
    random.seed(20240626)
    bpm = 112
    bars, bpb = 4, 4
    total = loop_samples(bars, bpb, bpm)
    xf = int(8.0 / 1000.0 * SR)
    size = total + xf + 8
    L = [0.0] * size
    R = [0.0] * size

    # Chord roots per bar (Am, F, C, G) -> bass notes (one per beat, root-fifth walk).
    roots = [45, 41, 48, 43]   # A2, F2, C3, G2
    bass = []
    for r in roots:
        bass += [(r, 1.0), (r + 7, 1.0), (r, 1.0), (r + 12, 1.0)]
    render_voice(L, R, bass * 2, "saw", 0.32, bpm, pan=0.5, detune=0.004,
                 env=(0.005, 0.08, 0.75, 0.10))

    # Arp: a bright square line, 8th notes climbing each chord's triad.
    triads = [[57, 60, 64, 67], [53, 57, 60, 65], [60, 64, 67, 72], [55, 59, 62, 67]]
    arp = []
    for tri in triads:
        seq = tri + tri[::-1]                  # up then down = 8 eighths per bar
        for nidx in seq:
            arp.append((nidx, 0.5))
    render_voice(L, R, arp * 2, "square", 0.18, bpm, pan=0.62, duty=0.4,
                 env=(0.004, 0.04, 0.5, 0.06))

    # Pad: soft triangle, a held chord-root + third per bar (whole notes), wide.
    pad = []
    for r in roots:
        pad += [(r + 12, 4.0)]
    render_voice(L, R, pad * 2, "tri", 0.16, bpm, pan=0.38, detune=0.006,
                 env=(0.12, 0.20, 0.85, 0.40))

    L, R = seamless(L, R, total, xf_ms=8.0)
    finalize(L, R, target=0.82)
    return write_wav("music_city_loop_v2", L, R)


def build_victory_sting():
    """The flag-capture fanfare: a rising C-major flourish into a held triad. One-shot."""
    random.seed(7)
    bpm = 150
    total = int(3.6 * SR)
    L = [0.0] * total
    R = [0.0] * total

    # Lead brass-y line: quick ascending run, then the triumphant top note held.
    lead = [(60, 0.5), (64, 0.5), (67, 0.5), (72, 0.5),
            (76, 0.5), (79, 1.0), (84, 2.0)]
    render_voice(L, R, lead, "saw", 0.34, bpm, pan=0.5, detune=0.005,
                 env=(0.008, 0.05, 0.8, 0.18))
    # Harmony a third below, softer.
    harm = [(None, 2.0), (None, 0.5), (72, 1.0), (76, 2.0)]
    render_voice(L, R, harm, "square", 0.16, bpm, pan=0.42, duty=0.5,
                 env=(0.01, 0.06, 0.8, 0.25))
    # Bass root pulses underneath.
    bass = [(36, 0.5), (43, 0.5), (48, 0.5), (43, 0.5), (36, 1.0), (48, 2.0)]
    render_voice(L, R, bass, "saw", 0.28, bpm, pan=0.5, detune=0.004,
                 env=(0.005, 0.08, 0.7, 0.2))

    edge_fade(L, R, ms=4.0)
    finalize(L, R, target=0.9)
    return write_wav("music_victory_sting", L, R)


def build_sfx_flag_raise():
    """Rising flourish as the banner climbs the mast: ascending arp + a noise whoosh."""
    random.seed(11)
    total = int(1.5 * SR)
    L = [0.0] * total
    R = [0.0] * total
    bpm = 240
    arp = [(60, 0.5), (64, 0.5), (67, 0.5), (72, 0.5), (76, 0.5), (79, 1.0)]
    render_voice(L, R, arp, "square", 0.30, bpm, pan=0.5, duty=0.45,
                 env=(0.004, 0.03, 0.5, 0.05))
    add_noise_sweep(L, R, 1.3, gain=0.16, rise=True)
    edge_fade(L, R, ms=4.0)
    finalize(L, R, target=0.85)
    return write_wav("sfx_flag_raise", L, R)


def build_sfx_capture():
    """The claim hit: a bright major-chord stab with a tiny transient click."""
    random.seed(3)
    total = int(0.5 * SR)
    L = [0.0] * total
    R = [0.0] * total
    bpm = 120
    for nidx in (60, 64, 67, 72):              # C major stacked, all struck together
        render_voice(L, R, [(nidx, 0.5)], "square", 0.16, bpm, pan=0.5, duty=0.5,
                     env=(0.002, 0.06, 0.0, 0.12))
    # transient click for "snap"
    for i in range(int(0.004 * SR)):
        if i < total:
            c = random.uniform(-1.0, 1.0) * (1.0 - i / (0.004 * SR)) * 0.5
            L[i] += c
            R[i] += c
    edge_fade(L, R, ms=3.0)
    finalize(L, R, target=0.88)
    return write_wav("sfx_capture", L, R)


def build_sfx_enemy_defeat():
    """The stomp/defeat 'bwop': a fast downward pitch glide."""
    random.seed(5)
    total = int(0.32 * SR)
    L = [0.0] * total
    R = [0.0] * total
    render_sweep(L, R, midi_freq(74), midi_freq(48), 0.30, kind="square",
                 gain=0.5, env=(0.003, 0.02, 0.6, 0.06))
    edge_fade(L, R, ms=3.0)
    finalize(L, R, target=0.85)
    return write_wav("sfx_enemy_defeat", L, R)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("[synth_audio] writing to {}".format(OUT_DIR))
    build_city_loop_v2()
    build_victory_sting()
    build_sfx_flag_raise()
    build_sfx_capture()
    build_sfx_enemy_defeat()
    print("[synth_audio] done -- 5 WAVs generated. Re-run import_art.py to bring them into UE.")


if __name__ == "__main__":
    main()
