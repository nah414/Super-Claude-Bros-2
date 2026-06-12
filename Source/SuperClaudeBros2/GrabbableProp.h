// Super Claude Bros 2 — GRABBABLE PROPS (Adam's RPG round, June 12): the world
// becomes hands-on. E grabs the nearest prop, E drops it gently, LMB HURLS it —
// thrown stone meets Glimmer, Glimmer loses. Mote-weight only in v1; lanterns
// and heavier RPG objects join through this same class.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GrabbableProp.generated.h"

class UStaticMeshComponent;

UCLASS()
class AGrabbableProp : public AActor
{
	GENERATED_BODY()

public:
	AGrabbableProp();

	void OnGrabbed();
	void OnDropped();
	void OnThrown(const FVector& Velocity, AActor* InThrower);

	bool IsHeld() const { return bHeld; }

	/** Thrown props hit like a hero light strike. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GrabbableProp")
	float ThrowImpactSpeed = 600.f;   // below this, landings are harmless

	/** Shatter on a damaging hit (burst + destroy) or survive and roll on. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GrabbableProp")
	bool bShatterOnImpact = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GrabbableProp")
	FLinearColor Tint = FLinearColor(0.45f, 0.32f, 0.2f);

	UPROPERTY(VisibleAnywhere, Category = "GrabbableProp")
	UStaticMeshComponent* PropMesh;

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void HandleHit(UPrimitiveComponent* HitComp, AActor* OtherActor,
	               UPrimitiveComponent* OtherComp, FVector NormalImpulse,
	               const FHitResult& Hit);

private:
	bool bHeld = false;
	bool bThrown = false;
	TWeakObjectPtr<AActor> Thrower;
};
