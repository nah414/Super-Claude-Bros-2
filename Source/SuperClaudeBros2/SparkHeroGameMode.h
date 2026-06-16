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

	virtual UClass* GetDefaultPawnClassForController_Implementation(AController* InController) override;

	/** The First Lantern (the world-goal lantern) calls this when relit — the world is
	    won: the whole city kindles back to amber, and (if wired) the Road opens to the
	    next world. */
	void OnWorldGoalLit();

	/** Travel here on win (the next world's map name). None = stay — just the celebration
	    (so World 1 ships standalone until World 2 exists). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCB2")
	FName NextWorldMap = NAME_None;

protected:
	virtual void BeginPlay() override;

private:
	bool bWorldWon = false;
	FTimerHandle WinTravelTimer;
};
