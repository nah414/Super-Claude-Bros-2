// Super Claude Bros 2 — VERDANT BREATH (World 3, the Reach's lungs).
// One invisible actor that IS the wind: a 10Hz driver (Load Law — ambience never
// per-frame) summing two slow sines + scheduled gust swells into the
// MPC_VerdantBreath collection (canopy WPO sway, moss pulse, water shimmer) and
// the wind-bed / gust audio volumes. The forest breathes from one diaphragm.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "VerdantBreath.generated.h"

class UAudioComponent;
class UMaterialParameterCollection;
class USoundBase;

UCLASS()
class AVerdantBreath : public AActor
{
	GENERATED_BODY()

public:
	AVerdantBreath();

	/** Slow inhale period, seconds (first sine). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breath")
	float BreathPeriodA = 11.f;

	/** Second, incommensurate period — the sum never quite repeats. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breath")
	float BreathPeriodB = 17.f;

	/** Seconds between gusts (min..max, uniform). Cluster or calm lives here. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breath")
	float GustMinInterval = 18.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breath")
	float GustMaxInterval = 45.f;

	/** One gust's rise-and-fall, seconds (sin envelope, no hard edges). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breath")
	float GustDuration = 6.f;

	/** How hard a gust leans on the canopy (adds to Breath, drives Gust scalar). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breath")
	float GustStrength = 1.f;

	/** Wind-bed loudness ceiling (the bed swells with the base breath). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breath")
	float WindBedVolume = 0.6f;

	UPROPERTY(VisibleAnywhere, Category = "Breath")
	TObjectPtr<UAudioComponent> WindBed;

	UPROPERTY(VisibleAnywhere, Category = "Breath")
	TObjectPtr<UAudioComponent> GustLayer;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY()
	TObjectPtr<UMaterialParameterCollection> BreathMPC;

	UPROPERTY()
	TArray<TObjectPtr<USoundBase>> GustSwells;

	float NextGustTime = 0.f;
	float GustT0 = -1000.f;
	int32 TickCount = 0;
};
