// UInteractionSubsystem — the per-world interactable registry.

#include "InteractionSubsystem.h"

#include "Interactable.h"

void UInteractionSubsystem::Register(AActor* Interactable)
{
	if (Interactable && Interactable->Implements<UInteractable>())
	{
		Registered.AddUnique(Interactable);
	}
}

AActor* UInteractionSubsystem::FindFocus(const FVector& From, const ASparkHeroCharacter* Hero) const
{
	AActor* Best = nullptr;
	float BestDistSq = TNumericLimits<float>::Max();
	for (int32 i = Registered.Num() - 1; i >= 0; --i)
	{
		AActor* A = Registered[i].Get();
		if (!A)
		{
			Registered.RemoveAtSwap(i);   // compact stale weak entries lazily
			continue;
		}
		IInteractable* I = Cast<IInteractable>(A);
		if (!I || !I->CanInteract(Hero)) { continue; }
		const float R = I->GetFocusRadius();
		const float DistSq = FVector::DistSquared(From, A->GetActorLocation());
		if (DistSq <= R * R && DistSq < BestDistSq)
		{
			BestDistSq = DistSq;
			Best = A;
		}
	}
	return Best;
}
