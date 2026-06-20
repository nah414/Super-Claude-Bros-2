// Super Claude Bros 2 — the Glimmer.
// The first enemy: a small ink-dark mote with two bright cream eyes that patrols
// its platform at night, turning back at walls and ledges. Stomp it or dash
// through it and it squashes flat; touch it any other way and it bonks the hero
// away (no damage system yet — contact costs momentum, not hearts). Every
// tunable is an EditAnywhere UPROPERTY so feel can be tuned live in-editor.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SparkContactTypes.h"
#include "GlimmerEnemy.generated.h"

class UStaticMeshComponent;
class USceneComponent;
class ASparkHeroCharacter;

UCLASS()
class AGlimmerEnemy : public ACharacter
{
	GENERATED_BODY()

public:
	AGlimmerEnemy();

	// ---------------- Components ----------------
	/** Scales for the death-squash without touching the collision capsule. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Glimmer|Components")
	TObjectPtr<USceneComponent> VisualRoot;

	/** Ink-dark body (engine sphere mesh) until the real Glimmer model lands. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Glimmer|Components")
	TObjectPtr<UStaticMeshComponent> BodyMesh;

	/** Cream eye spheres — the only light this little shadow gives off. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Glimmer|Components")
	TObjectPtr<UStaticMeshComponent> LeftEye;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Glimmer|Components")
	TObjectPtr<UStaticMeshComponent> RightEye;

	// ---------------- Patrol ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float PatrolSpeed = 260.f;

	// ---------------- Aggro (hunt on sight) ----------------
	/** A hero inside this range drops the Glimmer out of patrol and into the hunt —
	    it turns and walks straight at him. This is "attacks at first sight". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float AggroRadius = 650.f;

	/** Speed the Glimmer commits to while hunting (a notch above the patrol amble). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float ChaseSpeed = 360.f;

	// ---------------- Strike (the active attack) ----------------
	/** Within this range the Glimmer stops walking and POUNCES at the hero. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float StrikeRange = 280.f;

	/** Horizontal speed of the pounce. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float LungeSpeed = 1150.f;

	/** Upward pop on the pounce so it reads as a leap, not a slide. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float LungeLift = 300.f;

	/** Seconds between pounces (the telegraph/recovery rhythm). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float StrikeCooldown = 1.3f;

	/** How far past the capsule's leading edge we probe for walls and ledges. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float TurnCheckDistance = 50.f;

	// ---------------- Hero contact ----------------
	/** The Glimmer's row in the Limitations Ledger: Mote class, stompable,
	    dashable, 10-ember bonk — the Contact Matrix's reference enemy
	    (SCB2_INTERACTION_SPEC.md §5; struct defaults ARE the Glimmer). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	FContactProfile ContactProfile;

	/** Horizontal launch speed applied to the hero on a side bonk. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float KnockbackForce = 700.f;

	/** Upward pop added to the bonk so the hero clears the Glimmer cleanly. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float KnockbackLift = 350.f;

	/** Upward launch the hero earns for a successful stomp. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float StompBounce = 600.f;

	/** The hero must be falling at least this fast (velocity Z below this) to stomp. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float StompVelocityThreshold = -300.f;

	/** Seconds before contact can bonk the hero again — no per-frame retriggers. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float HitCooldown = 0.8f;

	/** How long the Glimmer stands still after bonking the hero. Kept BELOW HitCooldown
	    so a hero pressed flush against us can no longer chain-stun the Glimmer into a
	    permanent freeze — it always gets a beat to re-engage and push back. (This was
	    the "Glimmer stops moving when you get close" bug: 1.0s stun > 0.8s cooldown.) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float StunDuration = 0.5f;

	/** How long the flattened body lingers before the actor is destroyed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float SquashLingerTime = 0.6f;

	// ---------------- Event hooks (Niagara/SFX wire in later, in Blueprint) ----------------
	UFUNCTION(BlueprintImplementableEvent, Category = "Glimmer|Events")
	void OnGlimmerSquashed(bool bByStomp);

	/** A hero strike landed (the Spark Combo). Motes die to any beat — the
	    mass-class ladder, applied by fist. */
	UFUNCTION(BlueprintCallable, Category = "Glimmer")
	void TakeStrike();

	/** A power pulse (Prism Burst / Beacon Wave) staggered us — dazzled, not hurt. */
	UFUNCTION(BlueprintCallable, Category = "Glimmer")
	void TakeStagger(float Seconds);

	/** Calm-state flips (entered/left the hero's Spark Aura) — VFX/SFX seam. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Glimmer|Events")
	void OnCalmChanged(bool bCalm);

	UFUNCTION(BlueprintPure, Category = "Glimmer")
	bool IsCalmedByAura() const { return bCalmedByAura; }

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	// Capsule contact — both routes funnel into HandleHeroContact().
	UFUNCTION()
	void OnCapsuleHit(UPrimitiveComponent* HitComp, AActor* OtherActor, UPrimitiveComponent* OtherComp,
	                  FVector NormalImpulse, const FHitResult& Hit);

	UFUNCTION()
	void OnCapsuleOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp,
	                      int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

private:
	// Patrol state
	void SenseAndTurn();
	float LastTurnTime = -1000.f;

	// Aggro state: face + walk straight at the hero (ledge-safe, reuses SenseAndTurn).
	void ChaseHero(ASparkHeroCharacter* Hero);

	// The active attack: pounce at the hero (ledge-guarded), spark telegraph, then the bonk lands.
	void Lunge(ASparkHeroCharacter* Hero);
	float NextStrikeTime = -1000.f;

	// Hero contact state
	void HandleHeroContact(ASparkHeroCharacter* Hero);
	void Die(bool bByStomp);
	void FinishDeath();
	float LastHitTime = -1000.f;
	float StunnedUntilTime = -1000.f;
	bool bDead = false;
	bool bCalmedByAura = false;   // settled inside the hero's Spark Aura (L2+)
	FTimerHandle DestroyTimerHandle;

	// Cached hero for the generous per-frame proximity backstop.
	TWeakObjectPtr<ASparkHeroCharacter> CachedHero;

	// True when the Roster crystal-sprite model loaded (eyes/tint stay off).
	bool bHasRealModel = false;

	float Now() const;
};
