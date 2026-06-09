// Super Claude Bros 2 — game mode: spawns the Spark Hero, and powers the automated
// screenshot capture mode (-SCB2Shot=<path>) that lets Claude SEE builds headlessly.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SparkHeroGameMode.generated.h"

UCLASS()
class ASparkHeroGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASparkHeroGameMode();

protected:
	virtual void BeginPlay() override;
};
