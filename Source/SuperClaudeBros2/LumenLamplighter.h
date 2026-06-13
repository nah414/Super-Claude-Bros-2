// Super Claude Bros 2 — LUMEN THE LAMPLIGHTER (Story Bible). The cute firefly who
// keeps every lantern lit — and who is, in truth, the Dragonlord. As an NPC he is
// the checkpoint-keeper: a serene, glowing presence that hovers at his post,
// turning to regard the visitor. (The full checkpoint/relight SYSTEM and the
// Festival Streets hub are a larger build that waits for Adam's direction; this
// is his living presence.)

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LumenLamplighter.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class ASparkHeroCharacter;

UCLASS()
class ALumenLamplighter : public AActor
{
	GENERATED_BODY()

public:
	ALumenLamplighter();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lamplighter")
	float BodyScale = 0.7f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lamplighter")
	float HoverAmplitude = 14.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lamplighter")
	float HoverHz = 1.4f;            // a slow, serene bob (he is unhurried)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lamplighter")
	float FlutterHz = 9.f;

	/** He wanders a small circle around his post — he does NOT chase you. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lamplighter")
	float WanderRadius = 70.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lamplighter")
	float WanderSpeed = 18.f;        // degrees/sec around the post

	/** When the visitor comes near, he turns to regard them. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lamplighter")
	float NoticeRadius = 900.f;

	/** The lantern he carries — a warm, candle-soft glow (not a floodlight). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lamplighter")
	float LanternIntensity = 360.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lamplighter")
	float LanternRadius = 340.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lamplighter")
	float MeshYaw = -90.f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, Category = "Lamplighter")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "Lamplighter")
	UStaticMeshComponent* LampMesh;

	UPROPERTY(VisibleAnywhere, Category = "Lamplighter")
	UPointLightComponent* Lantern;

private:
	ASparkHeroCharacter* ResolveHero() const;
	float Now() const;

	FVector HomeLoc = FVector::ZeroVector;
	float Phase = 0.f;
	float WanderAngle = 0.f;
	bool bHasModel = false;
};
