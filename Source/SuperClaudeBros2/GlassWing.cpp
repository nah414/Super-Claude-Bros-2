#include "GlassWing.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

AGlassWing::AGlassWing()
{
	PrimaryActorTick.bCanEverTick = true;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	SetRootComponent(VisualRoot);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> Plasma(TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma"));

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(VisualRoot);
	if (Sphere.Succeeded()) { Body->SetStaticMesh(Sphere.Object.Get()); }
	if (Plasma.Succeeded()) { Body->SetMaterial(0, Plasma.Object.Get()); }
	Body->SetRelativeScale3D(FVector(0.34f, 0.16f, 0.14f));   // a swallow-sized dart
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetCastShadow(false);

	auto MakeWing = [&](const TCHAR* Name, float SideY) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* Wing = CreateDefaultSubobject<UStaticMeshComponent>(Name);
		Wing->SetupAttachment(VisualRoot);
		if (Cone.Succeeded()) { Wing->SetStaticMesh(Cone.Object.Get()); }
		if (Plasma.Succeeded()) { Wing->SetMaterial(0, Plasma.Object.Get()); }
		Wing->SetRelativeLocation(FVector(0.f, SideY, 2.f));
		Wing->SetRelativeScale3D(FVector(0.30f, 0.03f, 0.42f));   // a thin shard blade
		Wing->SetRelativeRotation(FRotator(0.f, 0.f, SideY > 0.f ? 88.f : -88.f));
		Wing->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Wing->SetCastShadow(false);
		return Wing;
	};
	WingL = MakeWing(TEXT("WingL"), -16.f);
	WingR = MakeWing(TEXT("WingR"), 16.f);

	Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
	Glow->SetupAttachment(VisualRoot);
	Glow->SetIntensity(160.f);   // firefly-faint (the Brightness War holds in the sky too)
	Glow->SetAttenuationRadius(220.f);
	Glow->SetCastShadows(false);
}

void AGlassWing::BeginPlay()
{
	Super::BeginPlay();
	Home = GetActorLocation();
	Phase = (Home.X + Home.Y) * 0.007f;
	OrbitAngle = Phase;
	if (Glow) { Glow->SetLightColor(GlowTint); }

	// Placed actor: tint MIDs are born HERE (the unsavable-level law).
	if (Body)
	{
		if (UMaterialInstanceDynamic* MID = Body->CreateDynamicMaterialInstance(0))
		{
			MID->SetVectorParameterValue(TEXT("Tint"), GlowTint * 0.9f);
		}
	}
	for (UStaticMeshComponent* Wing : { WingL, WingR })
	{
		if (Wing)
		{
			if (UMaterialInstanceDynamic* MID = Wing->CreateDynamicMaterialInstance(0))
			{
				MID->SetVectorParameterValue(TEXT("Tint"), GlowTint * 0.45f);
			}
		}
	}
}

void AGlassWing::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// The lazy circle: constant arc speed, a slow breathing bob, nose on the tangent.
	OrbitAngle += (OrbitSpeed / FMath::Max(OrbitRadius, 50.f)) * DeltaSeconds;
	const float Bob = BobAmplitude * FMath::Sin(GetWorld()->GetTimeSeconds() * BobHz * 2.f * PI + Phase);
	const FVector Pos = Home + FVector(FMath::Cos(OrbitAngle) * OrbitRadius,
	                                   FMath::Sin(OrbitAngle) * OrbitRadius, Bob);
	SetActorLocation(Pos);
	SetActorRotation(FRotator(0.f, FMath::RadiansToDegrees(OrbitAngle) + 90.f, 0.f));

	// The flap: shard wings rock in opposition; the body rides the beat.
	const float Flap = FMath::Sin(GetWorld()->GetTimeSeconds() * FlapHz * 2.f * PI + Phase) * 32.f;
	if (WingL) { WingL->SetRelativeRotation(FRotator(0.f, 0.f, -88.f - Flap)); }
	if (WingR) { WingR->SetRelativeRotation(FRotator(0.f, 0.f, 88.f + Flap)); }
}
