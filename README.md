# Super Claude Bros 2 — *The Last Lamplighter*

A 3D RPG / narrative action-platformer inspired by Anthropic fantasy, built in
**Unreal Engine 5.7 (C++)**. Two squid-blooded Spark heroes carry the old hero-fire
down the **Lamplighter's Road** — an ancient gate-network linking six worlds — to
relight the great lanterns, one world at a time.

The sequel to [Super-Claude-Bros](https://github.com/nah414/Super-Claude-Bros).

## The six worlds

| # | World | Theme |
|---|---|---|
| 1 | **Anthropica** (Volthaven, the neon capital) | city-wide blackout, the relight ritual |
| 2 | **The Moonlit Glade** | moonlight duels and light-puzzles |
| 3 | **The Verdant Reach** | the vertical climb of the Heartwood |
| 4 | **Forgefall** | hazard platforming in the foundry |
| 5 | **Everbright** | the drained golden homeland |
| 6 | **The Verge** | the dark between worlds |

## Where things stand

- **`main`** is the stable v1.x line (the "GO-ALL-OUT" round, June 2026): Worlds 1–2
  built and playable in succession on the World Road, with throwable props, bosses,
  and the dashboard.
- Active work happens on branches and stops at the gate — the current one is
  **`feat/w3-verdant-stage`**: World 3, the Verdant Reach, built in walk-and-answer
  rounds (the Heartwood, the sunken river, the hybrid climb, real water flow).
- Worlds are built and verified **headlessly** via Unreal Python
  (`PyScripts/build_*.py` + read-only verifiers) — the walk decides, the round answers.

## Cloning

This repo stores all `Content/` assets and source art through **Git LFS**
(~13 GiB on the active branch), so:

```
git lfs install
git clone https://github.com/nah414/Super-Claude-Bros-2.git
```

Open `SuperClaudeBros2.uproject` with Unreal Engine 5.7 (Visual Studio 2022 C++
toolchain required).

## Credits

- **Adam (nah414)** — creator and director: the design canon, every walk, every verdict.
- **Claude (Anthropic)** — the build seats: world construction, C++/Python
  implementation, rigs, and the recipe laws learned round by round.

The design canon (story bible, world roadmaps, build recipes) is maintained
separately from this code repository.
