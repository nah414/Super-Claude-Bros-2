// Super Claude Bros 2 — RESCUE NET (W3 round 4: the seal law's last brace).
// An invisible catch volume over a residual void: hero overlap -> teleport to
// the builder-set target, or to the active checkpoint lantern if none is set.
// Adam's law, learned the hard way: every space a hero can enter must have
// light, a way out, and a net underneath.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RescueNet.generated.h"

class UBoxComponent;

UCLASS()
class ARescueNet : public AActor
{
	GENERATED_BODY()

public:
	ARescueNet();

	/** Where the rescued hero lands. ZeroVector = ask the checkpoint subsystem. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rescue")
	FVector RescueTarget = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rescue")
	float RescueYaw = 0.f;

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnNetOverlap(UPrimitiveComponent* Overlapped, AActor* Other,
	                  UPrimitiveComponent* OtherComp, int32 BodyIndex,
	                  bool bFromSweep, const FHitResult& Sweep);

	UPROPERTY(VisibleAnywhere, Category = "Rescue")
	TObjectPtr<UBoxComponent> Net;
};
