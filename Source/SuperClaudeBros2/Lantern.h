// Super Claude Bros 2 — THE LANTERN. The world's light made into an actor: a warm
// flame on a post that can be SNUFFED (the Hollow Warden eats it; the Unlight's void
// spreads from it) and RELIT (the Lamplighter's whole purpose; the hero's relight
// verb). The light-manager's atom — every world is lit by these, and the fight for the
// dark is fought over them.
//
// It now (a) owns a ULightStateComponent — the uniform Lit/Guttering/Dark handle the
// ember-refill system and the LightNetworkManager talk to — and (b) implements
// IInteractable, exposing the RELIGHT as a HOLD: a flame climbs the wick while you
// hold, no progress bar, interruptible. Its public Snuff/Relight/IsLit are preserved
// as thin forwarders so the Warden/Unlight code that snuffs lanterns is untouched.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interactable.h"
#include "LightStateComponent.h"
#include "Lantern.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UPointLightComponent;

UCLASS()
class ALantern : public AActor, public IInteractable
{
	GENERATED_BODY()

public:
	ALantern();

	/** Put it out — dims to dark; the area it lit goes cold. */
	UFUNCTION(BlueprintCallable, Category = "Lantern")
	void Snuff();

	/** Light it again — the keeper's gift, the hero's verb. */
	UFUNCTION(BlueprintCallable, Category = "Lantern")
	void Relight();

	UFUNCTION(BlueprintPure, Category = "Lantern")
	bool IsLit() const;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	float LitIntensity = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	float LitRadius = 520.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	FLinearColor FlameColor = FLinearColor(1.5f, 1.0f, 0.45f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	float PostHeight = 1.4f;   // cylinder scale-Z (engine cylinder is 100uu)

	/** A snuffed lantern re-warms on its own after this long (0 = stays dark until
	    something relights it). The world heals slowly; the keeper heals fast. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	float AutoRelightSeconds = 9.f;

	/** The hero IS light — his presence rekindles a snuffed lantern he passes. The
	    relight verb, automatic; and the live counter to the Warden's dark. 0 disables —
	    set 0 on CHECKPOINT/goal lamps so relighting them is a deliberate HOLD, not a
	    side effect of walking past. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	float RelightByHeroRadius = 300.f;

	/** This lantern becomes the hero's CHECKPOINT (respawn anchor) when deliberately
	    relit. Ambient lamps leave it false. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	bool bIsCheckpoint = false;

	/** The world's GOAL lantern — relighting it is the win condition (the First Lantern). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	bool bIsWorldGoal = false;

	/** Spawn DARK — a dead lamp the hero must relight (checkpoints, the goal, the Night's
	    victims). Default lit (the warm festival ambient). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	bool bStartDark = false;

	/** How long the relight HOLD takes (the flame-climb length). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lantern")
	float RelightHoldSeconds = 1.2f;

	/** The uniform state handle the refill system + LightNetworkManager use. */
	ULightStateComponent* GetLightState() const { return LightState; }

	// ---------------- IInteractable (the relight rite) ----------------
	virtual EInteractKind GetInteractKind() const override { return EInteractKind::Hold; }
	virtual bool CanInteract(const ASparkHeroCharacter* Hero) const override { return !IsLit(); }
	virtual float GetFocusRadius() const override { return 180.f; }
	virtual float GetHoldSeconds() const override { return RelightHoldSeconds; }
	virtual void OnHoldBegin(ASparkHeroCharacter* Hero) override;
	virtual void OnHoldTick(ASparkHeroCharacter* Hero, float Progress01) override;
	virtual void OnHoldComplete(ASparkHeroCharacter* Hero) override;
	virtual void OnHoldInterrupted(ASparkHeroCharacter* Hero) override;
	virtual void SetFocusHighlight(bool bFocused) override;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** The lamp repaints its flame + light here whenever its state changes. */
	UFUNCTION()
	void OnLightStateChanged(ELightState NewState);

	UPROPERTY(VisibleAnywhere, Category = "Lantern")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "Lantern")
	UStaticMeshComponent* PostMesh;

	UPROPERTY(VisibleAnywhere, Category = "Lantern")
	UStaticMeshComponent* FlameMesh;

	UPROPERTY(VisibleAnywhere, Category = "Lantern")
	UPointLightComponent* Light;

	UPROPERTY(VisibleAnywhere, Category = "Lantern")
	ULightStateComponent* LightState;

private:
	float Now() const;
	/** Repaint the flame mesh + point light for the current state / focus / hold. */
	void PaintIdle();
	float RelightAt = 0.f;
	bool bFocused = false;
	bool bHolding = false;       // mid flame-climb (state is still Dark until complete)
	float FlameTopZ = 140.f;     // cached wick top for the climb
	UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> FlameMID;
};
