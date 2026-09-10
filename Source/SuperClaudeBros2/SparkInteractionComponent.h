// Super Claude Bros 2 — USparkInteractionComponent: the hero's ONE interaction brain.
// Each tick it asks the world registry for the nearest interactable it can act on and
// brightens that thing's own seams (the diegetic prompt — no floating UI). On the E
// press it routes by kind: Tap fires immediately; Hold begins a flame-climb that the
// component advances to completion (or the release interrupts it). Carry/Rotate fall
// through to the hero's existing grab path. The relight rite is a Hold.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SparkInteractionComponent.generated.h"

class ASparkHeroCharacter;

UCLASS(ClassGroup = (SCB2), meta = (BlueprintSpawnableComponent))
class USparkInteractionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USparkInteractionComponent();

	/** E pressed. Returns true if a focused interactable consumed the press (so the hero
	    only falls back to grab/drop when nothing interactable is focused). */
	bool OnInteractPressed();

	/** E released: completes-or-interrupts an in-progress hold (the flame-climb). */
	void OnInteractReleased();

	UFUNCTION(BlueprintPure, Category = "Interaction")
	bool IsHolding() const { return bHolding; }

	UFUNCTION(BlueprintPure, Category = "Interaction")
	float GetHoldProgress() const;

	/** The thing currently in focus (for HUD/debug), or nullptr. */
	AActor* GetFocusedActor() const { return Focused.Get(); }

protected:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
	                           FActorComponentTickFunction* ThisTickFunction) override;

private:
	ASparkHeroCharacter* Hero() const;
	void SetFocus(AActor* NewFocus);

	TWeakObjectPtr<AActor> Focused;
	bool bHolding = false;
	float HoldElapsed = 0.f;
	float HoldSeconds = 1.2f;
};
