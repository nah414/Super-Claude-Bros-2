// Super Claude Bros 2 — EMBER TRAIL: the Reaver's signature power made ground.
// Every dash he takes paints the floor with these — flickering ember flames
// (cones; flames are cones — house lore) that burn for ~1.6s. Touch one and
// the flame bites: small ember cost + an upward pop. The arena itself becomes
// his weapon; respecting the ground is the lesson of his duel.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EmberTrailPatch.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInstanceDynamic;

UCLASS()
class AEmberTrailPatch : public AActor
{
	GENERATED_BODY()

public:
	AEmberTrailPatch();

	static void Plant(UObject* WorldContext, const FVector& GroundLocation);

	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "EmberTrail")
	float LifeSeconds = 1.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "EmberTrail")
	float BurnRadius = 72.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "EmberTrail")
	float BurnEmbers = 5.f;

protected:
	UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Flame;
	UPROPERTY(VisibleAnywhere) UPointLightComponent* Glow;
	UPROPERTY() UMaterialInstanceDynamic* FlameMID;

	float Age = 0.f;
	float FlickerPhase = 0.f;
};
