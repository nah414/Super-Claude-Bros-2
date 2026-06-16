// Super Claude Bros 2 — IInteractable: the one contract every interactable thing
// satisfies, so the hero has a SINGLE interaction code path. Rich actors (ALantern)
// implement it directly off their own state; trivial archetypes (pickups, levers) get
// it for free via UInteractableComponent. Pure C++ virtuals (the asset-free logic
// doctrine); every consumer is nullptr-safe.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "InteractTypes.h"
#include "Interactable.generated.h"

class ASparkHeroCharacter;

UINTERFACE()
class UInteractable : public UInterface
{
	GENERATED_BODY()
};

class IInteractable
{
	GENERATED_BODY()

public:
	/** Tap / Hold / Carry / Rotate — the hero disambiguates the one E input by this. */
	virtual EInteractKind GetInteractKind() const { return EInteractKind::Tap; }

	/** Gate: e.g. a Lantern only offers its Hold-relight while it is DARK. */
	virtual bool CanInteract(const ASparkHeroCharacter* Hero) const { return true; }

	/** How close the hero must be to focus this (its prompt brightens within the radius). */
	virtual float GetFocusRadius() const { return 150.f; }

	/** Hold-kind only: how long the hold takes to complete (the flame-climb length). */
	virtual float GetHoldSeconds() const { return 1.2f; }

	/** Tap: fired on press. Return true if it consumed the interaction. */
	virtual bool OnInteractTap(ASparkHeroCharacter* Hero) { return false; }

	/** Hold lifecycle. Tick carries 0..1 progress; the thing renders its own diegetic
	    climb (no UI). Interrupted fires if the hero releases before completion. */
	virtual void OnHoldBegin(ASparkHeroCharacter* Hero) {}
	virtual void OnHoldTick(ASparkHeroCharacter* Hero, float Progress01) {}
	virtual void OnHoldComplete(ASparkHeroCharacter* Hero) {}
	virtual void OnHoldInterrupted(ASparkHeroCharacter* Hero) {}

	/** The diegetic prompt: brighten/dim my own emissive seams (never floating UI). */
	virtual void SetFocusHighlight(bool bFocused) {}
};
