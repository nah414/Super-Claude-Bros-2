// Super Claude Bros 2 — the Spark Blast, reforged as THE SPARK LANCE (Adam's
// July 23 ruling: "a ball of light" no more). A spinning crystalline DART of
// kept-fire: a white-hot needle core with shard tip and tail, two crackle-sparks
// orbiting it, and a ribbon of light streaks left hanging in its wake. Still
// asset-free: engine primitives + the plasma family + pooled trail pieces
// (LOAD LAW: the trail is a fixed ring buffer ON the projectile — no actor spam).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SparkBlastProjectile.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UProjectileMovementComponent;
class UMaterialInstanceDynamic;

UCLASS()
class ASparkBlastProjectile : public AActor
{
	GENERATED_BODY()

public:
	ASparkBlastProjectile();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<USphereComponent> Collision;

	/** The dart assembly spins around the flight axis as one piece. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<USceneComponent> ShardRoot;

	/** The white-hot needle core. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UStaticMeshComponent> Ball;

	/** The crystalline point and the long shard tail. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UStaticMeshComponent> TipShard;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UStaticMeshComponent> TailShard;

	/** Faint outer energy shell — the glow VOLUME around the hot core. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UStaticMeshComponent> Halo;

	/** Two crackle-sparks orbiting the dart — the electric feel. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UStaticMeshComponent> OrbiterA;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UStaticMeshComponent> OrbiterB;

	/** The ribbon: a fixed ring buffer of light streaks dropped along the wake. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TArray<TObjectPtr<UStaticMeshComponent>> TrailStreaks;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UPointLightComponent> Light;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Blast")
	TObjectPtr<UProjectileMovementComponent> Movement;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Blast")
	float BlastSpeed = 1500.f;

	/** POWER TIER (1–3): size, heat, speed, and bite all climb. The caster sets
	    it right after spawn via ApplyTier (the tier fan in DoPrismBurst). */
	UPROPERTY(BlueprintReadOnly, Category = "Blast")
	int32 Tier = 1;

	void ApplyTier(int32 InTier);

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> PlasmaMaterial;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION()
	void OnBlastOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
	                    UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
	                    bool bFromSweep, const FHitResult& SweepResult);

private:
	static constexpr int32 NumStreaks = 6;

	float SizeScale = 1.f;                 // the tier's growth
	float NextStreakAt = 0.f;              // ring-buffer cadence clock
	int32 StreakIdx = 0;
	float StreakBorn[NumStreaks] = {};
	FVector LastStreakPos = FVector::ZeroVector;

	UPROPERTY() TArray<TObjectPtr<UMaterialInstanceDynamic>> StreakMIDs;
};
