// Super Claude Bros 2 — the interaction vocabulary. "The world reacts to light, and
// the player's one gift is to give it." ONE interact input (E) forever, disambiguated
// by the focused thing's kind: Tap = use/pickup/talk; Hold = the RELIGHT rite (a
// diegetic flame climbs the wick, interruptible, no progress bar); Carry/Rotate are
// contextual grips. The eight world archetypes all map onto these four kinds.

#pragma once

#include "CoreMinimal.h"
#include "InteractTypes.generated.h"

UENUM(BlueprintType)
enum class EInteractKind : uint8
{
	Tap     UMETA(DisplayName = "Tap"),     // instantaneous: lever, pickup, talk
	Hold    UMETA(DisplayName = "Hold"),    // the relight rite: a flame climbs the wick
	Carry   UMETA(DisplayName = "Carry"),   // lift + carry (brass fitting, crates)
	Rotate  UMETA(DisplayName = "Rotate")   // crystals / prism arrays (W2+)
};
