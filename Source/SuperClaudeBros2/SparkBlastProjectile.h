// Super Claude Bros 2 — the Spark Blast.
// The hero's hand-fired power shot (Adam's round-6 redesign of the Prism Burst):
// a glowing amber orb that flies flat, kills Motes on contact, and lights the
// street as it goes. Asset-free: engine sphere + dynamic material + point light.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SparkBlastProjectile.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UProjectileMovementComponent;

UCLASS()
class ASparkBlastProjectile : public AActor
{
	GENERATED_BODY()

public:
	ASparkBlastProjectile();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<USphereComponent> Collision;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UStaticMeshComponent> Ball;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UPointLightComponent> Light;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UProjectileMovementComponent> Movement;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Blast")
	float BlastSpeed = 1500.f;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> PlasmaMaterial;

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnBlastOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
	                    UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
	                    bool bFromSweep, const FHitResult& SweepResult);
};
