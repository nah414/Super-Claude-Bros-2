// Super Claude Bros 2 — THE LANTERN. The world's light made into an actor: a warm
// flame on a post that can be SNUFFED (the Hollow Warden eats it; the Unlight's
// void spreads from it) and RELIT (the Lamplighter's whole purpose; the hero's
// relight verb). The light-manager's atom — every world is lit by these, and the
// fight for the dark is fought over them.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Lantern.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UPointLightComponent;

UCLASS()
class ALantern : public AActor
{
	GENERATED_BODY()

public:
	ALantern();

	/** Put it out — dims to dark; the area it lit goes cold. */
	UFUNCTION(BlueprintCallable, Category = "Lantern")
	void Snuff();

	/** Light it again — the keeper's gift, the hero's verb. */
	UFUNCTION(BlueprintCallable, Category = "Lantern")
	void Relight();

	UFUNCTION(BlueprintPure, Category = "Lantern")
	bool IsLit() const { return bLit; }

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	float LitIntensity = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	float LitRadius = 520.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	FLinearColor FlameColor = FLinearColor(1.5f, 1.0f, 0.45f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	float PostHeight = 1.4f;   // cylinder scale-Z (engine cylinder is 100uu)

	/** A snuffed lantern re-warms on its own after this long (0 = stays dark
	    until something relights it). The world heals slowly; the keeper heals fast. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	float AutoRelightSeconds = 9.f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, Category = "Lantern")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "Lantern")
	UStaticMeshComponent* PostMesh;

	UPROPERTY(VisibleAnywhere, Category = "Lantern")
	UStaticMeshComponent* FlameMesh;

	UPROPERTY(VisibleAnywhere, Category = "Lantern")
	UPointLightComponent* Light;

private:
	float Now() const;
	bool bLit = true;
	float RelightAt = 0.f;
	UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> FlameMID;
};
