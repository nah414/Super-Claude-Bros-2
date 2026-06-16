// Super Claude Bros 2 — the Ember Meter.
// The hero's health is a flame, not a HUD: an inner Spark-fire that burns tall at
// full health and gutters low when hurt (locked by Adam, June 11 — full spec in
// SCB2_INTERACTION_SPEC.md §2). This component owns the numbers and drives the
// owner's registered flame visuals; it never draws UI. Reusable by design: the
// same meter is Sonnet's companion health and every rival's duel meter.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EmberMeterComponent.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnFlameOut);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnEmbersChanged, float, Fraction);

UCLASS(ClassGroup = (SCB2), meta = (BlueprintSpawnableComponent))
class UEmberMeterComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UEmberMeterComponent();

	// ---------------- Tunables (spec §2 — TARGET values now CODE) ----------------
	/** Full flame. The hearth boon (one per world) raises this by +25. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	float MaxEmbers = 100.f;

	/** No-damage grace after a hit; the flame flares to telegraph it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	float GraceDuration = 0.8f;

	/** Below this fraction the flame visibly gutters (flicker + dim). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	float GutterFraction = 0.25f;

	/** Embers per second regained inside a lit lantern's radius (wired to the light-state
	    component + checkpoint subsystem — P0-M0.2, now live). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	float LanternRefillRate = 25.f;

	/** Only the heroes drink in lantern warmth — the hero enables this; default off so
	    rivals' duel meters and other ember-bearers are unaffected. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember")
	bool bRefillsInLanternLight = false;

	// ---------------- Flame visuals (owner registers; both optional) ----------------
	/** Flame height tracks the meter: Z scale = GutterScale..FullScale. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember|Visual")
	float FlameFullScaleZ = 0.22f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember|Visual")
	float FlameGutterScaleZ = 0.05f;

	/** Tuned DOWN three times (1200 → 380 → 120 → 40, Adam's "too much orange glow"
	    verdict, June 11) — the flame reads as a candle the player carries, not a
	    floodlight. Lessons: at point-blank range surfaces saturate at almost ANY
	    wattage (inverse square), and the glade's FFT bloom turns hot pixels into
	    stars — so the fix was distance + source size + a smaller, dimmer flame. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ember|Visual")
	float GlowFullIntensity = 40.f;

	// ---------------- Events ----------------
	/** The flame went out. The owner decides what death means (hero: respawn). */
	UPROPERTY(BlueprintAssignable, Category = "Ember|Events")
	FOnFlameOut OnFlameOut;

	/** Fired on every damage/refill with the new 0..1 fraction (VFX/SFX seam). */
	UPROPERTY(BlueprintAssignable, Category = "Ember|Events")
	FOnEmbersChanged OnEmbersChanged;

	// ---------------- API ----------------
	/** Drain embers. Returns false if the hit was eaten by grace or the flame is
	    already out (knockback still applies at the caller — contact always costs
	    momentum, it just doesn't always cost fire). */
	UFUNCTION(BlueprintCallable, Category = "Ember")
	bool ApplyEmberDamage(float Embers);

	UFUNCTION(BlueprintCallable, Category = "Ember")
	void Refill(float Embers);

	UFUNCTION(BlueprintCallable, Category = "Ember")
	void RefillFull();

	UFUNCTION(BlueprintPure, Category = "Ember")
	float GetFraction() const { return MaxEmbers > 0.f ? CurrentEmbers / MaxEmbers : 0.f; }

	UFUNCTION(BlueprintPure, Category = "Ember")
	bool IsInGrace() const;

	UFUNCTION(BlueprintPure, Category = "Ember")
	bool IsFlameOut() const { return bFlameOut; }

	/** EMBER GUARD (hero power L5): extends the no-damage grace window — the
	    flame armors itself. The existing grace flare IS the telegraph. */
	UFUNCTION(BlueprintCallable, Category = "Ember")
	void ActivateGuard(float Seconds);

	/** Power-cast light pulse (Prism Burst / Beacon Wave): boosts the glow for a
	    moment without fighting the per-tick intensity drive. */
	UFUNCTION(BlueprintCallable, Category = "Ember")
	void FlashGlow(float Seconds, float IntensityBoost);

	/** The owner hands over its flame mesh + glow light; the meter animates them.
	    Both nullptr-safe — the meter runs fine invisible (house pattern). */
	void RegisterFlameVisuals(UStaticMeshComponent* InFlame, UPointLightComponent* InGlow);

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
	                           FActorComponentTickFunction* ThisTickFunction) override;

private:
	float CurrentEmbers = 100.f;
	float GraceUntilTime = -1000.f;
	float GlowPulseUntil = -1000.f;
	float GlowPulseBoost = 1.f;
	bool bFlameOut = false;

	TWeakObjectPtr<UStaticMeshComponent> Flame;
	TWeakObjectPtr<UPointLightComponent> Glow;

	void UpdateFlameVisuals(float DeltaTime);
	float Now() const;
};
