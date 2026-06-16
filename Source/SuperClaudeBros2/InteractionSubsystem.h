// Super Claude Bros 2 — UInteractionSubsystem: a tiny per-world registry of every
// IInteractable actor, so the hero's interaction component can find the nearest thing
// it can act on by distance — no per-frame actor iteration, no collision setup on the
// (collision-less) lanterns. Interactables register on BeginPlay; entries are weak, so
// no unregister is needed (stale ones are compacted out on query).

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "InteractionSubsystem.generated.h"

class ASparkHeroCharacter;

UCLASS()
class UInteractionSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** Every IInteractable actor registers here on BeginPlay (weak — no unregister). */
	void Register(AActor* Interactable);

	/** The nearest registered interactable the hero can currently act on (within its own
	    focus radius and passing CanInteract), or nullptr. */
	AActor* FindFocus(const FVector& From, const ASparkHeroCharacter* Hero) const;

private:
	mutable TArray<TWeakObjectPtr<AActor>> Registered;
};
