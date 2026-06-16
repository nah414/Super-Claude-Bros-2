// USparkInteractionComponent — the hero's one interaction code path.

#include "SparkInteractionComponent.h"

#include "Interactable.h"
#include "InteractionSubsystem.h"
#include "SparkHeroCharacter.h"

USparkInteractionComponent::USparkInteractionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

ASparkHeroCharacter* USparkInteractionComponent::Hero() const
{
	return Cast<ASparkHeroCharacter>(GetOwner());
}

void USparkInteractionComponent::SetFocus(AActor* NewFocus)
{
	AActor* Old = Focused.Get();
	if (Old == NewFocus) { return; }
	if (Old)
	{
		if (IInteractable* I = Cast<IInteractable>(Old)) { I->SetFocusHighlight(false); }
	}
	Focused = NewFocus;
	if (NewFocus)
	{
		if (IInteractable* I = Cast<IInteractable>(NewFocus)) { I->SetFocusHighlight(true); }
	}
}

void USparkInteractionComponent::TickComponent(float DeltaTime, ELevelTick TickType,
                                               FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	ASparkHeroCharacter* H = Hero();
	if (!H) { return; }

	// Advance an in-progress hold; the focused thing renders its own climb.
	if (bHolding)
	{
		AActor* F = Focused.Get();
		IInteractable* I = F ? Cast<IInteractable>(F) : nullptr;
		if (!I)
		{
			bHolding = false;
			return;
		}
		HoldElapsed += DeltaTime;
		const float P = (HoldSeconds > 0.f) ? (HoldElapsed / HoldSeconds) : 1.f;
		I->OnHoldTick(H, P);
		if (P >= 1.f)
		{
			I->OnHoldComplete(H);
			bHolding = false;
			SetFocus(nullptr);   // re-focus next tick (it's lit now, no longer interactable)
		}
		return;
	}

	// Refresh focus: the nearest interactable becomes the diegetic prompt.
	if (UWorld* W = GetWorld())
	{
		if (UInteractionSubsystem* Sub = W->GetSubsystem<UInteractionSubsystem>())
		{
			SetFocus(Sub->FindFocus(H->GetActorLocation(), H));
		}
	}
}

bool USparkInteractionComponent::OnInteractPressed()
{
	ASparkHeroCharacter* H = Hero();
	if (!H) { return false; }
	AActor* F = Focused.Get();
	IInteractable* I = F ? Cast<IInteractable>(F) : nullptr;
	if (!I || !I->CanInteract(H)) { return false; }

	switch (I->GetInteractKind())
	{
	case EInteractKind::Hold:
		bHolding = true;
		HoldElapsed = 0.f;
		HoldSeconds = FMath::Max(I->GetHoldSeconds(), 0.05f);
		I->OnHoldBegin(H);
		return true;

	case EInteractKind::Tap:
		return I->OnInteractTap(H);

	default:
		return false;   // Carry/Rotate: the hero's existing grab path handles these (for now)
	}
}

void USparkInteractionComponent::OnInteractReleased()
{
	if (!bHolding) { return; }
	bHolding = false;
	AActor* F = Focused.Get();
	if (IInteractable* I = F ? Cast<IInteractable>(F) : nullptr)
	{
		I->OnHoldInterrupted(Hero());
	}
}

float USparkInteractionComponent::GetHoldProgress() const
{
	return (bHolding && HoldSeconds > 0.f) ? FMath::Clamp(HoldElapsed / HoldSeconds, 0.f, 1.f) : 0.f;
}
