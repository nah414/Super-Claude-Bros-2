// Super Claude Bros 2 — BARK SKITTER (W3 round 2: Adam's "new ground forest creatures").
// A trunk-surface scuttler: circles the Heartwood's bark by RAYCAST-STICK — each
// tick it advances around the axis, traces toward the trunk, and plants itself on
// whatever bark it finds (buttresses included, no field math needed). Asset-free
// (flattened sphere + cone legs, plasma MID bronze), no collision, no HP.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BarkSkitter.generated.h"

class UStaticMeshComponent;

UCLASS()
class ABarkSkitter : public AActor
{
	GENERATED_BODY()

public:
	ABarkSkitter();

	/** The trunk axis this skitter circles (the builder sets the Heartwood's). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skitter")
	float AxisX = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skitter")
	float AxisY = 9000.f;

	/** Degrees around the trunk per second (sign = direction). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skitter")
	float ThetaSpeed = 9.f;

	/** Mid-height of the wander band and its half-height. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skitter")
	float ZMid = 1500.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skitter")
	float ZAmp = 600.f;

	/** Trace starts this far from the axis (outside any bark radius). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skitter")
	float TraceFrom = 3600.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skitter")
	FLinearColor GlowTint = FLinearColor(2.0f, 1.1f, 0.4f);

	UPROPERTY(VisibleAnywhere, Category = "Skitter")
	TObjectPtr<UStaticMeshComponent> Body;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	float Theta = 0.f;
	float Phase = 0.f;
};
