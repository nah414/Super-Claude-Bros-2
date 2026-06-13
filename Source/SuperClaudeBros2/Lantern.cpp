// The Lantern — the smallest unit of the war between light and dark.

#include "Lantern.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ALantern::ALantern()
{
	PrimaryActorTick.bCanEverTick = true;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	SetRootComponent(VisualRoot);

	PostMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PostMesh"));
	PostMesh->SetupAttachment(VisualRoot);
	PostMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	FlameMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FlameMesh"));
	FlameMesh->SetupAttachment(VisualRoot);
	FlameMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(VisualRoot);
	Light->SetCastShadows(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cyl(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (Cyl.Succeeded()) { PostMesh->SetStaticMesh(Cyl.Object); }
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (Sphere.Succeeded()) { FlameMesh->SetStaticMesh(Sphere.Object); }
}

void ALantern::BeginPlay()
{
	Super::BeginPlay();

	const float TopZ = PostHeight * 100.f;   // engine cylinder is 100uu tall
	PostMesh->SetRelativeLocation(FVector(0.f, 0.f, TopZ * 0.5f));
	PostMesh->SetRelativeScale3D(FVector(0.12f, 0.12f, PostHeight));
	FlameMesh->SetRelativeLocation(FVector(0.f, 0.f, TopZ + 6.f));
	FlameMesh->SetRelativeScale3D(FVector(0.22f));
	Light->SetRelativeLocation(FVector(0.f, 0.f, TopZ + 10.f));
	Light->SetAttenuationRadius(LitRadius);
	Light->SetLightColor(FlameColor);
	Light->SetIntensity(LitIntensity);

	// The flame GLOWS via the plasma material (additive); MID at BeginPlay (CDO law).
	if (UMaterialInterface* Plasma = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma")))
	{
		FlameMID = UMaterialInstanceDynamic::Create(Plasma, this);
		FlameMID->SetVectorParameterValue(TEXT("Tint"), FlameColor * 2.4f);
		FlameMesh->SetMaterial(0, FlameMID);
	}
}

float ALantern::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void ALantern::Snuff()
{
	if (!bLit) { return; }
	bLit = false;
	Light->SetIntensity(0.f);
	FlameMesh->SetVisibility(false);
	RelightAt = Now() + AutoRelightSeconds;
}

void ALantern::Relight()
{
	if (bLit) { return; }
	bLit = true;
	Light->SetIntensity(LitIntensity);
	FlameMesh->SetVisibility(true);
}

void ALantern::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (bLit)
	{
		// A small living flicker — desynced per lantern by its position.
		const float Phase = GetActorLocation().X * 0.01f + GetActorLocation().Y * 0.013f;
		Light->SetIntensity(LitIntensity * (0.9f + 0.1f * FMath::Sin(Now() * 6.f + Phase)));
		return;
	}

	// Snuffed. The hero's own light rekindles it the moment he comes near — the
	// relight verb, and the live counter to the Warden's spreading dark. (Only
	// snuffed lanterns ever run this proximity check, so it stays cheap.)
	if (RelightByHeroRadius > 0.f)
	{
		if (APawn* Hero = UGameplayStatics::GetPlayerPawn(this, 0))
		{
			if (FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= RelightByHeroRadius)
			{
				Relight();
				return;
			}
		}
	}
	if (AutoRelightSeconds > 0.f && Now() >= RelightAt)
	{
		Relight();   // otherwise the world slowly re-warms on its own
	}
}
