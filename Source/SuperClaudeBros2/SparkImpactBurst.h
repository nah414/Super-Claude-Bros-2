// Super Claude Bros 2 — the universal IMPACT BURST (Adam's contact pass, June 12):
// every landed hit in the game — fist, kick, bolt, slam, grip, stomp — spawns
// one of these at the point of contact. A plasma flash that swells and dies in
// a quarter second + a light pop. Asset-free (M_SparkPlasma family); in ADDITIVE
// the fade to black IS the fade out. One graphic language for all contact.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SparkImpactBurst.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInstanceDynamic;

UCLASS()
class ASparkImpactBurst : public AActor
{
	GENERATED_BODY()

public:
	ASparkImpactBurst();

	/** Fire-and-forget. Tint examples: hero strike (4,1.8,0.5) · hero hurt
	    (3,0.5,0.2) · Iron Grip violet (1.6,0.4,3.2) · slam shock (3,1.2,0.3). */
	static void Burst(UObject* WorldContext, const FVector& Location,
	                  const FLinearColor& Tint, float Scale = 1.f,
	                  float LightIntensity = 3500.f, float Life = 0.28f);

	virtual void Tick(float DeltaSeconds) override;

protected:
	UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Core;
	UPROPERTY(VisibleAnywhere) UPointLightComponent* Flash;
	UPROPERTY() UMaterialInstanceDynamic* CoreMID;

	/** LOAD LAW: past the soft cap, cosmetic bursts (dust, wisps — scale <0.8)
	    are skipped; past the hard cap the oldest burst is culled. Important
	    hits always show. */
	UPROPERTY(EditAnywhere, Category = "LoadLaw")
	int32 MaxLiveBurstsSoft = 14;

	UPROPERTY(EditAnywhere, Category = "LoadLaw")
	int32 MaxLiveBurstsHard = 20;

	FLinearColor BaseTint = FLinearColor(4.f, 1.8f, 0.5f);
	float BaseScale = 1.f;
	float BaseLight = 3500.f;
	float LifeSeconds = 0.28f;
	float Age = 0.f;

	friend class UWorld;
};
