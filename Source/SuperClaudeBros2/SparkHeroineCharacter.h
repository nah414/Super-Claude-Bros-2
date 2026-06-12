// Super Claude Bros 2 — SONNET, the Spark Heroine. Keeper of the First Lantern.
// Full parity with Claude by inheritance: every verb, the combo, the climb, the
// crouch, the Spark Surge kit L1–10 — same class, her body and clips. The only
// overrides are assets (HeroineSkelV2). Press P in game to switch heroes.

#pragma once

#include "CoreMinimal.h"
#include "SparkHeroCharacter.h"
#include "SparkHeroineCharacter.generated.h"

UCLASS()
class ASparkHeroineCharacter : public ASparkHeroCharacter
{
	GENERATED_BODY()

public:
	ASparkHeroineCharacter();
};
