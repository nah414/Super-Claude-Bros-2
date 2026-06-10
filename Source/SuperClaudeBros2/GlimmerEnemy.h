// Super Claude Bros 2 — the Glimmer.
// The first enemy: a small ink-dark mote with two bright cream eyes that patrols
// its platform at night, turning back at walls and ledges. Stomp it or dash
// through it and it squashes flat; touch it any other way and it bonks the hero
// away (no damage system yet — contact costs momentum, not hearts). Every
// tunable is an EditAnywhere UPROPERTY so feel can be tuned live in-editor.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
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

	/** How far past the capsule's leading edge we probe for walls and ledges. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float TurnCheckDistance = 50.f;

	// ---------------- Hero contact ----------------
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

	/** How long the Glimmer stands still after bonking the hero. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float StunDuration = 1.0f;

	/** How long the flattened body lingers before the actor is destroyed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glimmer")
	float SquashLingerTime = 0.6f;

	// ---------------- Event hooks (Niagara/SFX wire in later, in Blueprint) ----------------
	UFUNCTION(BlueprintImplementableEvent, Category = "Glimmer|Events")
	void OnGlimmerSquashed(bool bByStomp);

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

	// Hero contact state
	void HandleHeroContact(ASparkHeroCharacter* Hero);
	void Die(bool bByStomp);
	void FinishDeath();
	float LastHitTime = -1000.f;
	float StunnedUntilTime = -1000.f;
	bool bDead = false;
	FTimerHandle DestroyTimerHandle;

	// Cached hero for the generous per-frame proximity backstop.
	TWeakObjectPtr<ASparkHeroCharacter> CachedHero;

	float Now() const;
};
