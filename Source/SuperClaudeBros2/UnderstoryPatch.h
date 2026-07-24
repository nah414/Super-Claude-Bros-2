// Super Claude Bros 2 — UNDERSTORY PATCH (W3 round 3: Adam's dense forest floor).
// One actor = one plant species as a HISM: hundreds of walk-through instances
// for the cost of a single draw batch. The Instances array is the saved truth
// (a UPROPERTY on the actor); the HISM is rebuilt from it on construction and
// BeginPlay — persistence by construction. Editor Python fills the properties
// (AddComponentByClass isn't exposed to the python layer — learned 2026-07-23).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UnderstoryPatch.generated.h"

class UHierarchicalInstancedStaticMeshComponent;
class UMaterialInterface;
class UStaticMesh;

UCLASS()
class AUnderstoryPatch : public AActor
{
	GENERATED_BODY()

public:
	AUnderstoryPatch();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Understory")
	TObjectPtr<UStaticMesh> PlantMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Understory")
	TObjectPtr<UMaterialInterface> PlantMaterial;

	/** World-space transforms — the saved truth the HISM rebuilds from. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Understory")
	TArray<FTransform> Instances;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Understory")
	bool bCastShadows = false;

	UPROPERTY(VisibleAnywhere, Category = "Understory")
	TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Plants;

protected:
	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;

private:
	void RebuildInstances();
};
