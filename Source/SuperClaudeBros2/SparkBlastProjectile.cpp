#include "SparkBlastProjectile.h"

#include "Components/PointLightComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "GlimmerEnemy.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

ASparkBlastProjectile::ASparkBlastProjectile()
{
	PrimaryActorTick.bCanEverTick = false;
	InitialLifeSpan = 1.4f;   // flies ~21 m, then fades — no stray orbs forever

	Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
	Collision->InitSphereRadius(16.f);
	Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Collision->SetCollisionObjectType(ECC_WorldDynamic);
	Collision->SetCollisionResponseToAllChannels(ECR_Ignore);
	Collision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	SetRootComponent(Collision);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> Plasma(TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma"));
	PlasmaMaterial = Plasma.Succeeded() ? Plasma.Object : nullptr;

	Ball = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Ball"));
	Ball->SetupAttachment(Collision);
	Ball->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMesh.Succeeded())
	{
		Ball->SetStaticMesh(SphereMesh.Object);
	}
	Ball->SetRelativeScale3D(FVector(0.52f, 0.22f, 0.22f));   // a BOLT, stretched along flight
	Ball->SetCastShadow(false);

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Collision);
	Light->SetIntensity(1600.f);
	Light->SetAttenuationRadius(320.f);
	Light->SetLightColor(FColor(255, 170, 70));   // kept-fire amber (Color Law)
	Light->SetCastShadows(false);

	Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Movement"));
	Movement->InitialSpeed = BlastSpeed;
	Movement->MaxSpeed = BlastSpeed;
	Movement->ProjectileGravityScale = 0.f;   // spark-fire flies true (a bent law, priced by lifespan)
	Movement->bRotationFollowsVelocity = true;
}

void ASparkBlastProjectile::BeginPlay()
{
	Super::BeginPlay();

	Collision->OnComponentBeginOverlap.AddDynamic(this, &ASparkBlastProjectile::OnBlastOverlap);

	// PLASMA: the forged additive-fresnel material — white-hot core, glowing rim,
	// blooms under the cinematic post. Fallback to a flat amber tint if missing.
	if (PlasmaMaterial)
	{
		if (UMaterialInstanceDynamic* MID = Ball->CreateDynamicMaterialInstance(0, PlasmaMaterial))
		{
			MID->SetVectorParameterValue(TEXT("Tint"), FLinearColor(3.0f, 2.0f, 1.1f));
		}
	}
	else if (UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
	{
		UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
		MID->SetVectorParameterValue(TEXT("Color"), FLinearColor(1.f, 0.65f, 0.18f));
		Ball->SetMaterial(0, MID);
	}
}

void ASparkBlastProjectile::OnBlastOverlap(UPrimitiveComponent*, AActor* OtherActor,
                                           UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	if (!OtherActor || OtherActor == GetOwner() || OtherActor == GetInstigator()) { return; }

	if (AGlimmerEnemy* Glimmer = Cast<AGlimmerEnemy>(OtherActor))
	{
		Glimmer->TakeStrike();   // Motes die to spark-fire (mass-class ladder)
		Destroy();
	}
}
