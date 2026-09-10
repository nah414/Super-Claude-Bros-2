// UCheckpointSubsystem — respawn anchor + ember-refill warmth query.

#include "CheckpointSubsystem.h"

#include "Lantern.h"
#include "LightStateComponent.h"

void UCheckpointSubsystem::SetActiveCheckpoint(ALantern* Lantern)
{
	if (Lantern) { ActiveCheckpoint = Lantern; }
}

FTransform UCheckpointSubsystem::GetRespawnTransform() const
{
	if (ALantern* L = ActiveCheckpoint.Get())
	{
		return FTransform(L->GetActorRotation(), L->GetActorLocation() + FVector(0.f, 0.f, 50.f));
	}
	return FTransform::Identity;
}

void UCheckpointSubsystem::RegisterLight(ULightStateComponent* Light)
{
	if (Light) { Lights.AddUnique(Light); }
}

void UCheckpointSubsystem::CollectLightsInGroup(FName Group, TArray<ULightStateComponent*>& Out) const
{
	for (int32 i = Lights.Num() - 1; i >= 0; --i)
	{
		ULightStateComponent* L = Lights[i].Get();
		if (!L)
		{
			Lights.RemoveAtSwap(i);
			continue;
		}
		if (Group.IsNone() || L->GroupName == Group)
		{
			Out.Add(L);
		}
	}
}

bool UCheckpointSubsystem::IsInsideRefillZone(const FVector& Location) const
{
	for (int32 i = Lights.Num() - 1; i >= 0; --i)
	{
		ULightStateComponent* L = Lights[i].Get();
		if (!L)
		{
			Lights.RemoveAtSwap(i);   // compact stale weak entries
			continue;
		}
		if (!L->IsRefillZone()) { continue; }
		const AActor* Owner = L->GetOwner();
		if (!Owner) { continue; }
		if (FVector::DistSquared(Location, Owner->GetActorLocation()) <= L->LitRadius * L->LitRadius)
		{
			return true;
		}
	}
	return false;
}
