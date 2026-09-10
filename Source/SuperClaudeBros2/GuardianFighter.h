// Super Claude Bros 2 — AGuardianFighter: the data-driven duelist for the four
// GUARDIANS (the characters who once only granted hero skins). Adam's "upgrade all
// characters" round promoted them to full fighting characters — so rather than four
// more hand-written ASparkRivalBase subclasses, the base owns ONE generic fighter
// whose moves are a DATA TABLE. Each guardian is now ~50 lines: load its mesh + clips,
// push its move set, set its colors. The Knight duels, the Tank charges, the
// Powerhouse hammers, the Boxer counters — all from the same engine, different rows.
//
// A move row carries everything the state machine needs: clip + windows + the hit
// SHAPE (Cone / two-beat Combo / committed Lunge / 360 Ring / defensive Guard). The
// base routes ERivalState through the table; the seams never switch on a per-guardian
// enum. One guardian move per set is flagged the SIGNATURE — it glows the signature
// color, and (if the subclass arms it) fires automatically on a phase break.

#pragma once

#include "CoreMinimal.h"
#include "SparkRivalBase.h"
#include "GuardianFighter.generated.h"

class UAnimSequence;

UENUM(BlueprintType)
enum class EGuardianMoveKind : uint8
{
	Cone,       // a single front-arc melee strike inside Reach
	ConeTwice,  // a two-beat flurry: lands, re-arms at mid-window, lands again
	Lunge,      // a committed gap-closing dash-strike (locks its line at start)
	Ring,       // a 360 sweep at Reach (spin) — back off, it has no safe angle
	Guard       // a defensive beat: no strike, brief incoming-damage reduction
};

USTRUCT()
struct FGuardianMove
{
	GENERATED_BODY()

	UPROPERTY() FString Name;
	UPROPERTY() TObjectPtr<UAnimSequence> Clip = nullptr;
	UPROPERTY() float Tell = 0.6f;        // telegraph window (the readable wind-up)
	UPROPERTY() float Active = 0.35f;     // the hit window
	UPROPERTY() float Recover = 0.9f;     // the opening after
	UPROPERTY() float Reach = 240.f;      // strike distance (or ring radius)
	UPROPERTY() float ClipStart = 0.f;    // scanned: where in the clip the move begins
	UPROPERTY() float ClipRate = 0.f;     // scanned: play rate so impact lands on Active
	UPROPERTY() float EmberMul = 1.f;     // damage multiplier on DuelHitEmbers
	UPROPERTY() EGuardianMoveKind Kind = EGuardianMoveKind::Cone;
	UPROPERTY() int32 MinPhase = 1;       // gated: the move unlocks at this phase
	UPROPERTY() bool bSignature = false;  // the headline move (color + phase-break arm)
};

UCLASS(Abstract)
class AGuardianFighter : public ASparkRivalBase
{
	GENERATED_BODY()

public:
	AGuardianFighter();

	/** Hall/story seam: the guardian yields and salutes (BP hooks). */
	UFUNCTION(BlueprintImplementableEvent, Category = "Guardian")
	void OnGuardianDefeated();

	UFUNCTION(BlueprintImplementableEvent, Category = "Guardian")
	void OnGuardianPhaseChanged(int32 NewPhase);

	/** Read by the HUD/debug: the move the guardian is committing to (or "" / idle). */
	UFUNCTION(BlueprintPure, Category = "Guardian")
	FString GetCurrentMoveName() const { return Moves.IsValidIndex(MoveIdx) ? Moves[MoveIdx].Name : FString(); }

	// ---------------- Generic fighter tuning ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guardian")
	float LungeSpeed = 1500.f;     // the committed dash-strike velocity

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guardian")
	FLinearColor SignatureColor = FLinearColor(2.2f, 1.4f, 0.4f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guardian")
	FLinearColor BodyGlowColor = FLinearColor(1.6f, 1.1f, 0.5f);   // the honest-tell glow

	/** Embers taken while inside a Guard window (block/parry stance). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guardian")
	float GuardEmberScale = 0.4f;

protected:
	// ---- pure-virtual seams (all generic; the table is the soul) ----
	virtual void SelectMove(float DistToHero) override;
	virtual void StartTelegraph() override;
	virtual void StartAttack() override;
	virtual void TickAttack(float DeltaTime, ASparkHeroCharacter* Hero) override;
	virtual void HandleAttackExpired(ASparkHeroCharacter* Hero) override;
	virtual float GetTriggerRange() const override;
	virtual bool HasMoveSelected() const override { return Moves.IsValidIndex(MoveIdx); }
	virtual void ClearMove() override { MoveIdx = INDEX_NONE; }

	// ---- hooks ----
	virtual void NotifyRivalDefeated() override { OnGuardianDefeated(); }
	virtual void NotifyRivalPhaseChanged(int32 NewPhase) override;
	virtual float ModifyIncomingEmbers(float Embers, int32 ComboBeat, bool bCharged) override;
	virtual void ClearActiveMoveState() override;

	/** Subclass ctor helper: append a move row (its clip is kept GC-alive by the
	    UPROPERTY table). Returns the new row's index — used to arm the signature. */
	int32 AddMove(const FGuardianMove& InMove);

	/** A shared front-arc contact test (Cone / ConeTwice). */
	bool TryConeHit(ASparkHeroCharacter* Hero, const FGuardianMove& M, float CosThreshold = 0.2f);

	UPROPERTY() TArray<FGuardianMove> Moves;

	int32 MoveIdx = INDEX_NONE;
	int32 LastMoveIdx = INDEX_NONE;    // survives ClearMove() so repeat-avoidance actually works
	int32 SignatureIdx = INDEX_NONE;   // subclass sets this to a Moves index (-1 = none)
	bool bSignatureQueued = false;     // armed by a phase break; fires next SelectMove

	/** Richer move VFX: a periodic shaped plasma burst painted during an active move
	    (the Knight's spin ring, the Tank's charge trail) — throttled, not per-frame. */
	void TickMoveVfx(const FGuardianMove& M, float DeltaTime);

	/** Land a hit AND, for the signature move, add a bigger signature-color flourish. */
	void LandGuardianHit(ASparkHeroCharacter* Hero, const FGuardianMove& M);

private:
	FVector LungeDir = FVector::ForwardVector;
	bool bGuarding = false;
	bool bComboReArmed = false;
	float NextVfxTime = 0.f;     // throttle for TickMoveVfx
	float VfxSpin = 0.f;         // rolling angle for the ring sweep
};
