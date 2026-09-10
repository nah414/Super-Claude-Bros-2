// Super Claude Bros 2 — EMBER DRIFT (the WOW pass, Adam 2026-07-21).
// A volume of tiny amber motes that rise and wander like sparks off the city's
// kept-fire: the Color Law made ambient. Asset-free (engine sphere + plasma MID),
// one instanced mesh component per volume — hundreds of motes for pennies.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EmberDrift.generated.h"

class UInstancedStaticMeshComponent;

UCLASS()
class AEmberDrift : public AActor
{
	GENERATED_BODY()

public:
	AEmberDrift();

	/** Motes in this volume. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	int32 NumMotes = 60;

	/** Half-extents of the drift volume around the actor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	FVector Extent = FVector(1800.f, 1800.f, 700.f);

	/** Upward drift, uu/sec (each mote gets a personal 0.7-1.4x multiplier). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	float RiseSpeed = 26.f;

	/** Sideways sine-wander amplitude. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	float WanderAmp = 55.f;

	/** Base sphere scale (engine sphere is 100uu — 0.05 = a 5uu spark). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	float MoteScale = 0.05f;

	/** Amber, per the Color Law: kept-fire only. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	FLinearColor Tint = FLinearColor(3.0f, 1.35f, 0.35f);

	UPROPERTY(VisibleAnywhere, Category = "Ember")
	TObjectPtr<UInstancedStaticMeshComponent> Motes;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	TArray<FVector> Anchors;   // per-mote rest position (local)
	TArray<float> Phases;      // per-mote wander phase
	TArray<float> RiseMul;     // per-mote rise multiplier
	float Now() const;
};
