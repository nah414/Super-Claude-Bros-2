// Super Claude Bros 2 — LEAF GLIDER (W3 round 2: Adam's "new flying forest creatures").
// A code-built drifter: two crossed leaf-membrane cards riding a slow spiral —
// orbit + sink + relift, banked like a soarer. Asset-free (engine planes + the
// plasma MID), no collision, no HP: pure canopy weather, the GlassWing's cousin.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LeafGlider.generated.h"

class UStaticMeshComponent;

UCLASS()
class ALeafGlider : public AActor
{
	GENERATED_BODY()

public:
	ALeafGlider();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glider")
	float OrbitRadius = 1400.f;

	/** Degrees of orbit per second. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glider")
	float OrbitSpeed = 260.f;

	/** How far below Home the spiral sinks before the relift. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glider")
	float DropDepth = 1800.f;

	/** Seconds for one full sink-and-relift breath. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glider")
	float CyclePeriod = 22.f;

	/** Green-gold, per the palette law. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glider")
	FLinearColor GlowTint = FLinearColor(1.1f, 1.6f, 0.5f);

	UPROPERTY(VisibleAnywhere, Category = "Glider")
	TObjectPtr<UStaticMeshComponent> WingA;

	UPROPERTY(VisibleAnywhere, Category = "Glider")
	TObjectPtr<UStaticMeshComponent> WingB;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	FVector Home = FVector::ZeroVector;
	float Phase = 0.f;
};
