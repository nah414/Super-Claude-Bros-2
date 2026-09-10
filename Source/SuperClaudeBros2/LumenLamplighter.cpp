// Lumen the Lamplighter — he keeps the light, and he waits, and he watches.

#include "LumenLamplighter.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "SparkHeroCharacter.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	const FLinearColor LampAmber(1.5f, 1.0f, 0.45f);
}

ALumenLamplighter::ALumenLamplighter()
{
	PrimaryActorTick.bCanEverTick = true;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	SetRootComponent(VisualRoot);

	LampMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LampMesh"));
	LampMesh->SetupAttachment(VisualRoot);
	LampMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);   // a presence, not an obstacle

	Lantern = CreateDefaultSubobject<UPointLightComponent>(TEXT("Lantern"));
	Lantern->SetupAttachment(VisualRoot);
	Lantern->SetRelativeLocation(FVector(0.f, 0.f, -10.f));   // the light-tail hangs below
	Lantern->SetIntensity(360.f);
	Lantern->SetAttenuationRadius(340.f);
	Lantern->SetLightColor(LampAmber);
	Lantern->SetCastShadows(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Model(TEXT("/Game/Art/Roster/lumen_lamplighter/SM_lumen_lamplighter.SM_lumen_lamplighter"));
	if (Model.Succeeded())
	{
		LampMesh->SetStaticMesh(Model.Object);
		bHasModel = true;
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (Sphere.Succeeded()) { LampMesh->SetStaticMesh(Sphere.Object); }
	}
}

void ALumenLamplighter::BeginPlay()
{
	Super::BeginPlay();
	HomeLoc = GetActorLocation();
	LampMesh->SetRelativeScale3D(FVector(BodyScale));
	LampMesh->SetRelativeRotation(FRotator(0.f, MeshYaw, 0.f));
	Lantern->SetIntensity(LanternIntensity);
	Lantern->SetAttenuationRadius(LanternRadius);
	Phase = FMath::Frac(HomeLoc.X * 0.011f + HomeLoc.Y * 0.019f) * 6.2832f;
	WanderAngle = Phase;
}

ASparkHeroCharacter* ALumenLamplighter::ResolveHero() const
{
	return Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
}

float ALumenLamplighter::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void ALumenLamplighter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float T = Now() + Phase;

	// A serene wander around his post — he never leaves the light untended.
	WanderAngle += FMath::DegreesToRadians(WanderSpeed) * DeltaSeconds;
	FVector Pos = HomeLoc + FVector(FMath::Cos(WanderAngle), FMath::Sin(WanderAngle), 0.f) * WanderRadius;
	Pos.Z = HomeLoc.Z + HoverAmplitude * FMath::Sin(T * HoverHz);
	SetActorLocation(Pos);

	// He turns to regard the visitor when they come near; otherwise drifts calmly.
	FRotator Want(0.f, MeshYaw, 0.f);
	ASparkHeroCharacter* Hero = ResolveHero();
	if (Hero && FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= NoticeRadius)
	{
		const FVector To = (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
		Want = FRotator(0.f, To.Rotation().Yaw + MeshYaw, 0.f);
	}
	const float Beat = 1.f + 0.08f * FMath::Sin(T * FlutterHz);
	LampMesh->SetWorldRotation(FMath::RInterpTo(LampMesh->GetComponentRotation(), Want, DeltaSeconds, 3.f));
	LampMesh->SetRelativeScale3D(FVector(BodyScale * Beat, BodyScale, BodyScale * Beat));

	// The lantern breathes, always amber.
	Lantern->SetIntensity(LanternIntensity + 60.f * FMath::Sin(T * 1.5f));
}
