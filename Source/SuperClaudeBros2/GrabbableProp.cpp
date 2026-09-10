#include "GrabbableProp.h"

#include "Bramblehulk.h"
#include "Components/StaticMeshComponent.h"
#include "EmberReaver.h"
#include "Engine/StaticMesh.h"
#include "GlimmerEnemy.h"
#include "KrakenBoss.h"
#include "RolyShellback.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "SparkImpactBurst.h"
#include "SparkRivalBase.h"
#include "UObject/ConstructorHelpers.h"
#include "VoidStalker.h"

AGrabbableProp::AGrabbableProp()
{
	PrimaryActorTick.bCanEverTick = false;

	PropMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PropMesh"));
	SetRootComponent(PropMesh);
	PropMesh->SetSimulatePhysics(true);
	PropMesh->SetCollisionProfileName(TEXT("PhysicsActor"));
	PropMesh->SetNotifyRigidBodyCollision(true);
	PropMesh->OnComponentHit.AddDynamic(this, &AGrabbableProp::HandleHit);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (Cube.Succeeded())
	{
		PropMesh->SetStaticMesh(Cube.Object);
		PropMesh->SetRelativeScale3D(FVector(0.45f));   // a carryable crate
	}
}

void AGrabbableProp::BeginPlay()
{
	Super::BeginPlay();
	// MID at BeginPlay, never the constructor (the CDO save-failure law).
	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
	{
		if (UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(Base, this))
		{
			MID->SetVectorParameterValue(TEXT("Color"), Tint);
			PropMesh->SetMaterial(0, MID);
		}
	}
}

void AGrabbableProp::OnGrabbed()
{
	bHeld = true;
	bThrown = false;
	PropMesh->SetSimulatePhysics(false);
	PropMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AGrabbableProp::OnDropped()
{
	bHeld = false;
	DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
	PropMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	PropMesh->SetSimulatePhysics(true);
}

void AGrabbableProp::OnThrown(const FVector& Velocity, AActor* InThrower)
{
	OnDropped();
	bThrown = true;
	Thrower = InThrower;
	PropMesh->AddImpulse(Velocity, NAME_None, true);
}

void AGrabbableProp::HandleHit(UPrimitiveComponent*, AActor* OtherActor,
                               UPrimitiveComponent*, FVector, const FHitResult& Hit)
{
	if (!bThrown || !OtherActor || OtherActor == Thrower.Get()) { return; }
	if (GetVelocity().Size() < ThrowImpactSpeed) { bThrown = false; return; }

	// A thrown stone hits like a hero light strike (the universal impact law).
	bool bDamaged = false;
	if (AGlimmerEnemy* Glimmer = Cast<AGlimmerEnemy>(OtherActor))
	{
		Glimmer->TakeStrike();
		bDamaged = true;
	}
	else if (AKrakenBoss* K = Cast<AKrakenBoss>(OtherActor))      { K->TakeStrike(0, false); bDamaged = true; }
	else if (AEmberReaver* R = Cast<AEmberReaver>(OtherActor))    { R->TakeStrike(0, false); bDamaged = true; }
	else if (AVoidStalker* S = Cast<AVoidStalker>(OtherActor))    { S->TakeStrike(0, false); bDamaged = true; }
	else if (ASparkRivalBase* RV = Cast<ASparkRivalBase>(OtherActor)) { RV->TakeStrike(0, false); bDamaged = true; }
	else if (ARolyShellback* SB = Cast<ARolyShellback>(OtherActor)) { SB->TakeStrike(); bDamaged = true; }
	else if (ABramblehulk* B = Cast<ABramblehulk>(OtherActor))    { B->TakeStrikeClang(nullptr, false); bDamaged = true; }

	if (bDamaged)
	{
		ASparkImpactBurst::Burst(this, Hit.ImpactPoint, FLinearColor(4.f, 1.8f, 0.5f), 1.0f, 3000.f);
		if (bShatterOnImpact)
		{
			ASparkImpactBurst::Burst(this, GetActorLocation(), Tint * 3.f, 0.9f, 1800.f);
			Destroy();
			return;
		}
	}
	bThrown = false;   // one impact per throw; after that it's just a rock again
}
