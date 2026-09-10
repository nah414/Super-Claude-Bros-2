// ALightNetworkManager — the wave that takes the city's light, or gives it back.

#include "LightNetworkManager.h"

#include "CheckpointSubsystem.h"
#include "LightStateComponent.h"

ALightNetworkManager::ALightNetworkManager()
{
	PrimaryActorTick.bCanEverTick = true;
}

void ALightNetworkManager::PlayGroupSequence(FName Group, ELightState Target, float TotalSeconds, bool bSpatialWave)
{
	TArray<ULightStateComponent*> Lights;
	if (UWorld* W = GetWorld())
	{
		if (UCheckpointSubsystem* CP = W->GetSubsystem<UCheckpointSubsystem>())
		{
			CP->CollectLightsInGroup(Group, Lights);
		}
	}
	if (Lights.Num() == 0) { return; }

	// Order the cascade: a spatial wave rolls the change outward from this actor; else
	// the lamps fire in registry order (still spread evenly across TotalSeconds).
	if (bSpatialWave)
	{
		const FVector Origin = GetActorLocation();
		Lights.Sort([Origin](const ULightStateComponent& A, const ULightStateComponent& B)
		{
			const AActor* OA = A.GetOwner();
			const AActor* OB = B.GetOwner();
			const float DA = OA ? FVector::DistSquared(Origin, OA->GetActorLocation()) : 0.f;
			const float DB = OB ? FVector::DistSquared(Origin, OB->GetActorLocation()) : 0.f;
			return DA < DB;
		});
	}

	FLightSeq Seq;
	Seq.Group = Group;
	Seq.Target = Target;
	Seq.Elapsed = 0.f;
	Seq.Total = FMath::Max(TotalSeconds, 0.01f);
	Seq.Ordered.Reserve(Lights.Num());
	Seq.Fired.Reserve(Lights.Num());
	for (ULightStateComponent* L : Lights)
	{
		Seq.Ordered.Add(L);
		Seq.Fired.Add(false);
	}
	Active.Add(MoveTemp(Seq));
}

void ALightNetworkManager::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	for (int32 s = Active.Num() - 1; s >= 0; --s)
	{
		FLightSeq& Seq = Active[s];
		Seq.Elapsed += DeltaSeconds;
		const int32 N = Seq.Ordered.Num();

		for (int32 i = 0; i < N; ++i)
		{
			if (Seq.Fired[i]) { continue; }
			const float FireAt = (N > 1) ? (static_cast<float>(i) / static_cast<float>(N)) * Seq.Total : 0.f;
			if (Seq.Elapsed >= FireAt)
			{
				if (ULightStateComponent* L = Seq.Ordered[i].Get())
				{
					L->SetState(Seq.Target);
				}
				Seq.Fired[i] = true;
			}
		}

		if (Seq.Elapsed >= Seq.Total)
		{
			// snap any stragglers to the target, then announce completion
			for (int32 i = 0; i < N; ++i)
			{
				if (!Seq.Fired[i])
				{
					if (ULightStateComponent* L = Seq.Ordered[i].Get()) { L->SetState(Seq.Target); }
					Seq.Fired[i] = true;
				}
			}
			OnGroupComplete.Broadcast(Seq.Group, Seq.Target);
			Active.RemoveAt(s);
		}
	}
}
