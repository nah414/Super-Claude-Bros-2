// Super Claude Bros 2 — THE GLASSWING (Adam, July 23: "small flying animals for
// background animations"). A palm-sized bio-mech glider that rides lazy circles
// over the crystal canopy — chrome body, translucent shard wings, a firefly-faint
// glow. Pure ambience in the Flit Moth tradition: no HP, no collision, no AI —
// just sky made alive. LOAD LAW: pure-math tick, no world queries, no shadows.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GlassWing.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;

UCLASS()
class AGlassWing : public AActor
{
	GENERATED_BODY()

public:
	AGlassWing();

	/** The circle it rides, centered on its spawn point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GlassWing")
	float OrbitRadius = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GlassWing")
	float OrbitSpeed = 320.f;   // uu/sec along the circle

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GlassWing")
	float BobAmplitude = 70.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GlassWing")
	float BobHz = 0.35f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GlassWing")
	float FlapHz = 5.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GlassWing")
	FLinearColor GlowTint = FLinearColor(0.7f, 1.5f, 1.7f);

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, Category = "GlassWing")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "GlassWing")
	UStaticMeshComponent* Body;

	UPROPERTY(VisibleAnywhere, Category = "GlassWing")
	UStaticMeshComponent* WingL;

	UPROPERTY(VisibleAnywhere, Category = "GlassWing")
	UStaticMeshComponent* WingR;

	UPROPERTY(VisibleAnywhere, Category = "GlassWing")
	UPointLightComponent* Glow;

private:
	FVector Home = FVector::ZeroVector;
	float OrbitAngle = 0.f;
	float Phase = 0.f;   // per-instance desync so a flock never beats in lockstep
};
