// Super Claude Bros 2 — THE GLADE PROWLER (Adam's July 23 call: a lower boss who
// PATROLS the crystal maze, unaware of the hero until SPOTTED — the small battle
// before the Bramblehulk). A Hollow-seeped titan far from its foundry, wandering
// the crystal rows with moss on its shoulders.
//
// The stealth contract: he never engages by proximity (DuelStartRadius is dead).
// He walks his rounds; his EYES start the fight — a vision cone plus a real
// line-of-sight trace, so the forest itself is cover and a crouched hero is
// half as visible. Escape past the disengage ring and he loses the scent, stands
// down, and resumes his rounds (the base walk-away law doing stealth's work).
// Defeating him raises every hero power tier by one (the tier ladder's first rung).

#pragma once

#include "CoreMinimal.h"
#include "SparkRivalBase.h"
#include "GladeProwler.generated.h"

class UAnimSequence;

UENUM(BlueprintType)
enum class EProwlerMove : uint8 { None, MossSwing, RootChop, BrambleSweep };

UCLASS()
class AGladeProwler : public ASparkRivalBase
{
	GENERATED_BODY()

public:
	AGladeProwler();

	// ---------------- The patrol ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Patrol")
	float PatrolSpeed = 420.f;   // "very active" — a brisk, restless prowl

	/** Walk-clip rate while prowling. The Warlord's stride was scanned for his
	    640-speed approach; rated down so patrol feet GRIP instead of skate
	    (Articulation Checklist rule 3: rate every loop to the ground). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Patrol")
	float PatrolAnimRate = 0.66f;

	/** He wanders this far from his spawn before the leash bends him home —
	    wide enough to own the whole maze (Adam, July 23: expand the rounds). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Patrol")
	float LeashRadius = 8000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Patrol")
	float WanderIntervalMin = 2.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Patrol")
	float WanderIntervalMax = 5.5f;

	// ---------------- The eyes ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Vision")
	float SightRange = 1600.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Vision")
	float SightHalfAngleDeg = 55.f;

	/** A crouched hero shrinks into the undergrowth: sight range scales by this. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Vision")
	float CrouchSightScale = 0.5f;

	/** The startle beat between the glimpse and the roar — the hero's last chance
	    to break line of sight before it becomes a fight. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Vision")
	float ReactionSeconds = 0.35f;

	// ---------------- Moves (the Warlord's steel, slowed by moss) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float SwingTell = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float SwingActive = 0.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float SwingRecover = 1.0f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float SwingReach = 270.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float ChopTell = 0.9f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float ChopActive = 0.35f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float ChopRecover = 1.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float ChopReach = 250.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float SweepTell = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float SweepActive = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float SweepRecover = 1.1f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Moves")
	float SweepRadius = 300.f;

	// ---------------- Clip windows (the Warlord's scans carry over) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SwingClipStart = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Anim")
	float SwingClipRate = 0.85f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float ChopClipStart = 0.42f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Anim")
	float ChopClipRate = 1.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SweepClipStart = 0.15f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prowler|Anim")
	float SweepClipRate = 1.05f;

protected:
	virtual void BeginPlay() override;

	/** The patrol IS his Waiting state — one owner for anim, rotation, velocity
	    (the July 23 double-driver law). Base idle/face-hero never runs for him. */
	virtual void TickWaiting(float DeltaTime, ASparkHeroCharacter* Hero, float Dist) override;

	// ---- pure-virtual seams ----
	virtual void SelectMove(float DistToHero) override;
	virtual void StartTelegraph() override;
	virtual void StartAttack() override;
	virtual void TickAttack(float DeltaTime, ASparkHeroCharacter* Hero) override;
	virtual void HandleAttackExpired(ASparkHeroCharacter* Hero) override;
	virtual float GetTriggerRange() const override { return 300.f; }
	virtual bool HasMoveSelected() const override { return Move != EProwlerMove::None; }
	virtual void ClearMove() override { Move = EProwlerMove::None; }

	// ---- hooks ----
	virtual void NotifyRivalDefeated() override;
	/** An unaware warden never shoulders anyone — a sneaking hero brushing past
	    must not be shoved into his vision cone (July 23 audit). */
	virtual bool AllowSeparationPush() const override { return State != ERivalState::Waiting; }
	/** A stealth strike IS a spotting: the ambushed warden wheels and roars
	    instead of sliding into the duel through a recover flinch. */
	virtual bool OnStruck(int32 ComboBeat, bool bCharged) override;

private:
	bool CanSeeHero(const ASparkHeroCharacter* Hero) const;
	void PickNewHeading(bool bBlocked);
	/** The one engage path: roar burst, movement stop, intro clip, Intro state. */
	void RoarAndEngage();

	EProwlerMove Move = EProwlerMove::None;
	FVector PatrolCenter = FVector::ZeroVector;
	float HeadingYaw = 0.f;
	float NextHeadingAt = 0.f;
	float SpottedSince = -1.f;   // <0 = nothing in the eyes yet

	UPROPERTY() TObjectPtr<UAnimSequence> SwingAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> ChopAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> SweepAnim;
};
