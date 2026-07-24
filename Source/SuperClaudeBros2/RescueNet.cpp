#include "RescueNet.h"

#include "CheckpointSubsystem.h"
#include "Components/BoxComponent.h"
#include "SparkHeroCharacter.h"

ARescueNet::ARescueNet()
{
	PrimaryActorTick.bCanEverTick = false;

	Net = CreateDefaultSubobject<UBoxComponent>(TEXT("Net"));
	SetRootComponent(Net);
	Net->SetBoxExtent(FVector(100.f, 100.f, 100.f));   // builder scales the actor
	Net->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Net->SetCollisionResponseToAllChannels(ECR_Ignore);
	Net->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Net->SetGenerateOverlapEvents(true);
	Net->SetHiddenInGame(true);
}

void ARescueNet::BeginPlay()
{
	Super::BeginPlay();
	Net->OnComponentBeginOverlap.AddDynamic(this, &ARescueNet::OnNetOverlap);
}

void ARescueNet::OnNetOverlap(UPrimitiveComponent*, AActor* Other,
                              UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	ASparkHeroCharacter* Hero = Cast<ASparkHeroCharacter>(Other);
	if (!Hero)
	{
		return;
	}
	FVector Loc = RescueTarget;
	if (Loc.IsNearlyZero())
	{
		if (const UCheckpointSubsystem* CP = GetWorld()->GetSubsystem<UCheckpointSubsystem>())
		{
			Loc = CP->GetRespawnTransform().GetLocation();
		}
	}
	if (Loc.IsNearlyZero())
	{
		return;   // no target, no checkpoint — never teleport to the origin
	}
	UE_LOG(LogTemp, Log, TEXT("RESCUE_NET: %s caught %s -> %s"),
	       *GetName(), *Hero->GetName(), *Loc.ToCompactString());
	Hero->RescueTo(Loc, FRotator(0.f, RescueYaw, 0.f));
}
