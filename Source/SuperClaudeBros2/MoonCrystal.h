// Super Claude Bros 2 — THE MOON CRYSTAL & THE MOON PRISM. The Moonworks' two
// rotatable optics (Roadmap II, Core 1 "The Moonworks"): the crystal REDIRECTS a
// beam along its facing; the prism SPLITS one beam into an authored fan. Both are
// the player's to turn — one E-tap, one snap stop (the base node owns the verb).

#pragma once

#include "CoreMinimal.h"
#include "MoonworksBeamNode.h"
#include "MoonCrystal.generated.h"

UCLASS()
class AMoonCrystal : public AMoonworksBeamNode
{
	GENERATED_BODY()

public:
	AMoonCrystal();
};

UCLASS()
class AMoonPrism : public AMoonworksBeamNode
{
	GENERATED_BODY()

public:
	AMoonPrism();

	/** Half-angle of the split fan. Authored optics: presets, never Snell. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Prism")
	float SplitAngleDeg = 30.f;

protected:
	virtual void GetOutDirections(TArray<FVector>& Out) const override;
};
