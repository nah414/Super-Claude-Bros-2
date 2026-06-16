// Super Claude Bros 2 — UCheckpointSubsystem: the world's light services for the hero.
// It remembers the last lantern the hero deliberately relit (the respawn anchor — the
// canon "Lumen keeps your lantern lit, so death costs seconds not minutes"), and it
// answers the ember-refill query ("is the hero standing in a lit lantern's warmth?").
// Lanterns' ULightStateComponents register on BeginPlay; entries are weak.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CheckpointSubsystem.generated.h"

class ALantern;
class ULightStateComponent;

UCLASS()
class UCheckpointSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** A deliberately-relit checkpoint lantern becomes the respawn anchor. */
	void SetActiveCheckpoint(ALantern* Lantern);
	bool HasActiveCheckpoint() const { return ActiveCheckpoint.IsValid(); }
	/** Where the hero re-kindles after a flame-out (lantern base + a small stand offset). */
	FTransform GetRespawnTransform() const;

	/** Every lamp's light-state registers here so the refill query is cheap. */
	void RegisterLight(ULightStateComponent* Light);
	/** True if the location is inside any LIT, refill-flagged lantern's radius. */
	bool IsInsideRefillZone(const FVector& Location) const;

private:
	TWeakObjectPtr<ALantern> ActiveCheckpoint;
	mutable TArray<TWeakObjectPtr<ULightStateComponent>> Lights;
};
