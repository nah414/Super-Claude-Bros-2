#include "BarkSkitter.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ABarkSkitter::ABarkSkitter()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.05f;   // 20 Hz; one short trace each — Load-Law trivial

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Root);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetCastShadow(false);
	Body->SetCanEverAffectNavigation(false);
	if (Sphere.Succeeded()) { Body->SetStaticMesh(Sphere.Object); }
	Body->SetRelativeScale3D(FVector(0.45f, 0.34f, 0.18f));

	const FVector LegOffsets[4] = {
		FVector(26.f, 18.f, -8.f), FVector(26.f, -18.f, -8.f),
		FVector(-26.f, 18.f, -8.f), FVector(-26.f, -18.f, -8.f) };
	for (int32 i = 0; i < 4; ++i)
	{
		UStaticMeshComponent* Leg = CreateDefaultSubobject<UStaticMeshComponent>(
			*FString::Printf(TEXT("Leg%d"), i));
		Leg->SetupAttachment(Root);
		Leg->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Leg->SetCastShadow(false);
		Leg->SetCanEverAffectNavigation(false);
		if (Cone.Succeeded()) { Leg->SetStaticMesh(Cone.Object); }
		Leg->SetRelativeLocation(LegOffsets[i]);
		Leg->SetRelativeRotation(FRotator(180.f, 0.f, 0.f));   // point down
		Leg->SetRelativeScale3D(FVector(0.06f, 0.06f, 0.22f));
	}
}

void ABarkSkitter::BeginPlay()
{
	Super::BeginPlay();
	Phase = FMath::FRandRange(0.f, 6.28318f);
	Theta = FMath::FRandRange(0.f, 6.28318f);

	UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
		nullptr, TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma"));
	if (!BaseMat)
	{
		BaseMat = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	}
	if (BaseMat)
	{
		UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
		MID->SetVectorParameterValue(TEXT("Tint"), GlowTint);
		MID->SetVectorParameterValue(TEXT("Color"), GlowTint);
		for (UActorComponent* C : GetComponents())
		{
			if (UStaticMeshComponent* SM = Cast<UStaticMeshComponent>(C))
			{
				SM->SetMaterial(0, MID);
			}
		}
	}
}

void ABarkSkitter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float T = GetWorld() ? static_cast<float>(GetWorld()->GetTimeSeconds()) : 0.f;
	Theta += FMath::DegreesToRadians(ThetaSpeed) * DeltaSeconds;
	const float Z = ZMid + ZAmp * FMath::Sin(T * 0.18f + Phase);

	// The raycast-stick: from outside the bark, trace toward the axis; whatever
	// bark answers (taper, buttress, all of it) is where the skitter stands.
	const FVector Dir(FMath::Cos(Theta), FMath::Sin(Theta), 0.f);
	const FVector Start(AxisX + Dir.X * TraceFrom, AxisY + Dir.Y * TraceFrom, Z);
	FHitResult Hit;
	FCollisionQueryParams Params(TEXT("SkitterStick"), false, this);
	if (GetWorld()->LineTraceSingleByChannel(Hit, Start,
			FVector(AxisX, AxisY, Z), ECC_Visibility, Params))
	{
		SetActorLocation(Hit.ImpactPoint + Hit.ImpactNormal * 12.f);
		// Stand on the bark: up = the surface normal, travel = the tangent.
		const FVector Tangent = FVector::CrossProduct(FVector::UpVector, Hit.ImpactNormal)
			.GetSafeNormal() * FMath::Sign(ThetaSpeed);
		SetActorRotation(FRotationMatrix::MakeFromXZ(Tangent, Hit.ImpactNormal).Rotator());
	}
}
