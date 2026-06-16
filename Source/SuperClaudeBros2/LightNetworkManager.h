// Super Claude Bros 2 — ALightNetworkManager: the city's nervous system of light.
// "Built once, fired seven times." It sequences whole GROUPS of lamps to a target
// state over time — forward to Dark is THE NIGHT (the catastrophe cascading the city
// dark), reverse to Lit is every relight FINALE. A spatial wave cascades the change by
// distance from the manager, so the dark (or the dawn) visibly rolls across the city.
// One per world; it reads the lamps from the CheckpointSubsystem registry at fire time
// (so every lamp has finished BeginPlay), no fragile spawn-order coupling.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LightStateComponent.h"
#include "LightNetworkManager.generated.h"

class ULightStateComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnLightGroupComplete, FName, Group, ELightState, Reached);

UCLASS()
class ALightNetworkManager : public AActor
{
	GENERATED_BODY()

public:
	ALightNetworkManager();

	/** Sequence a group to Target over TotalSeconds. NAME_None = the whole city.
	    bSpatialWave cascades by distance from this actor (the dark/dawn rolls outward). */
	UFUNCTION(BlueprintCallable, Category = "Light")
	void PlayGroupSequence(FName Group, ELightState Target, float TotalSeconds, bool bSpatialWave = true);

	/** Forward: snuff a group in a wave — THE NIGHT. */
	UFUNCTION(BlueprintCallable, Category = "Light")
	void DarkenGroup(FName Group, float Seconds) { PlayGroupSequence(Group, ELightState::Dark, Seconds, true); }

	/** Reverse: kindle a group in a wave — a relight FINALE. */
	UFUNCTION(BlueprintCallable, Category = "Light")
	void KindleGroup(FName Group, float Seconds) { PlayGroupSequence(Group, ELightState::Lit, Seconds, true); }

	/** Fired when a sequence finishes (the win-state / next-beat listens here). */
	UPROPERTY(BlueprintAssignable, Category = "Light")
	FOnLightGroupComplete OnGroupComplete;

protected:
	virtual void Tick(float DeltaSeconds) override;

private:
	struct FLightSeq
	{
		FName Group = NAME_None;
		ELightState Target = ELightState::Dark;
		float Elapsed = 0.f;
		float Total = 1.f;
		TArray<TWeakObjectPtr<ULightStateComponent>> Ordered;
		TArray<bool> Fired;
	};
	TArray<FLightSeq> Active;
};
