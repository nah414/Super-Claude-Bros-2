#include "MoonCrystal.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

AMoonCrystal::AMoonCrystal()
{
	// The base already dressed itself as a crystal shard; the crystal's whole
	// identity is one fact: the player may turn it.
	bPlayerRotatable = true;
}

AMoonPrism::AMoonPrism()
{
	static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshyPrism(TEXT("/Game/Art/Moonworks/moon_prism.moon_prism"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));

	if (BodyMesh && MeshyPrism.Succeeded())
	{
		// The Meshy lens ships with its own plinth: identity transform, garden-sized.
		BodyMesh->SetStaticMesh(MeshyPrism.Object.Get());
	}
	else if (BodyMesh && Sphere.Succeeded())
	{
		BodyMesh->SetStaticMesh(Sphere.Object.Get());
		// The bare lens floats at beam height so shafts strike its heart.
		BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, 150.f));
		BodyMesh->SetRelativeScale3D(FVector(1.35f, 1.35f, 1.35f));
	}
	bPlayerRotatable = true;
}

void AMoonPrism::GetOutDirections(TArray<FVector>& Out) const
{
	const FVector Fwd = GetActorForwardVector();
	Out.Add(Fwd.RotateAngleAxis(-SplitAngleDeg, FVector::UpVector));
	Out.Add(Fwd.RotateAngleAxis(SplitAngleDeg, FVector::UpVector));
}
