#include "UnderstoryPatch.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"

AUnderstoryPatch::AUnderstoryPatch()
{
	PrimaryActorTick.bCanEverTick = false;

	Plants = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("Plants"));
	SetRootComponent(Plants);
	Plants->SetCollisionEnabled(ECollisionEnabled::NoCollision);   // walk-through, always
	Plants->SetCanEverAffectNavigation(false);
	Plants->SetMobility(EComponentMobility::Static);
}

void AUnderstoryPatch::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	RebuildInstances();
}

void AUnderstoryPatch::BeginPlay()
{
	Super::BeginPlay();
	RebuildInstances();
}

void AUnderstoryPatch::RebuildInstances()
{
	if (!Plants) { return; }
	Plants->ClearInstances();
	if (PlantMesh)
	{
		Plants->SetStaticMesh(PlantMesh);
	}
	if (PlantMaterial)
	{
		Plants->SetMaterial(0, PlantMaterial);
	}
	Plants->SetCastShadow(bCastShadows);
	for (const FTransform& T : Instances)
	{
		Plants->AddInstance(T, /*bWorldSpace*/ true);
	}
}
