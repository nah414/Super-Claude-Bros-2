// Super Claude Bros 2 — THE FLIT MOTH (Powers Codex critters). A plump, fuzzy
// moth with big glowing eyes. Its power is LIGHTLOVE: it is irresistibly drawn
// to the strongest light (the hero's ember), and HERDING it is the point. It has
// NO HP, ever — fists puff through it. Pure charm and a future puzzle piece.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "FlitMoth.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class ASparkHeroCharacter;

UCLASS()
class AFlitMoth : public AActor
{
	GENERATED_BODY()

public:
	AFlitMoth();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FlitMoth")
	float BodyScale = 0.35f;

	/** How high it bobs as it hovers, and how fast. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FlitMoth")
	float HoverAmplitude = 18.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FlitMoth")
	float HoverHz = 2.2f;

	/** Wing-beat: a fast scale flutter that reads as fluttering. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FlitMoth")
	float FlutterHz = 11.f;

	/** LIGHTLOVE: it drifts toward the hero and circles at this distance. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FlitMoth")
	float OrbitRadius = 240.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FlitMoth")
	float DriftSpeed = 150.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FlitMoth")
	float OrbitSpeed = 55.f;     // degrees/sec around the light
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FlitMoth")
	float LoveRadius = 1400.f;   // beyond this it just idles at home

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FlitMoth")
	float MeshYaw = -90.f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, Category = "FlitMoth")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "FlitMoth")
	UStaticMeshComponent* MothMesh;

	UPROPERTY(VisibleAnywhere, Category = "FlitMoth")
	UPointLightComponent* Glow;

private:
	ASparkHeroCharacter* ResolveHero() const;
	float Now() const;

	FVector HomeLoc = FVector::ZeroVector;   // its anchor when no light is near
	float Phase = 0.f;                        // per-instance desync
	float OrbitAngle = 0.f;
	bool bHasModel = false;
};
