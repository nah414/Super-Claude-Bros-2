// Super Claude Bros 2 — ASparkRivalBase: the shared spine of every duelist rival.
//
// Three concrete voices were written as deliberate siblings (Iron Kraken, Ember
// Reaver, Void Stalker) — same duel framework, different bodies and powers. This
// Abstract base extracts that framework so a NEW rival (Rust Warlord and beyond)
// is a thin subclass, not a fourth hand-copied 300-line class.
//
// The base OWNS the universal machinery: the component tree, the duel tunables,
// the state machine scaffold (Tick/BeginPlay/TakeStrike/HandleDuelMeterEmpty),
// and the helpers (EnterState/Now/ResolveHero/FaceHero/PlayLoop/PlayOneShot/
// LandDuelHit/FinishAttack/TakeStagger). Each rival fills the PURE-VIRTUAL seams
// (SelectMove/StartTelegraph/StartAttack/TickAttack/HandleAttackExpired/
// GetTriggerRange/HasMoveSelected/ClearMove) and optionally the virtual hooks.
//
// Design notes baked into the seams (so the three approved rivals can migrate
// here later WITHOUT behavior change):
//  · ERivalState carries Vanished (only the Stalker enters it; others never do).
//  · LandDuelHit does NOT touch bHitThisAttack — callers own that latch (the
//    Kraken's internal-guard form is reconciled at its migration). Flurry/Cut
//    moves that hit twice rely on this.
//  · ClearActiveMoveState() lets the Kraken purge grip/tether on every exit path.
//  · ModifyIncomingEmbers() (pre-damage) carries the Reaver's blind-cone 1.5x;
//    OnStruck() (post-damage) carries the Stalker's blink-feint break.
//  · The MOVE enum stays per-rival; the base never switches on it — it routes
//    through HasMoveSelected()/ClearMove()/GetTriggerRange() and the seams.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SparkContactTypes.h"
#include "UObject/ConstructorHelpers.h"
#include "SparkRivalBase.generated.h"

class ASparkHeroCharacter;
class UEmberMeterComponent;
class USkeletalMeshComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UAnimSequence;

UENUM(BlueprintType)
enum class ERivalState : uint8
{
	Waiting,    // visibly ready; duels are player-initiated
	Intro,      // the flourish when the hero commits
	Approach,   // menace at ~0.9x hero tunings
	Telegraph,  // the theatrical tell
	Attack,     // the active window
	Recover,    // THE OPENING after a heavy
	Staggered,  // the charged-strike punish window
	Vanished,   // gone between blink and arrival (Stalker only)
	Defeated    // a state, never Destroy() — there is an epilogue to attend
};

UCLASS(Abstract)
class ASparkRivalBase : public ACharacter
{
	GENERATED_BODY()

public:
	ASparkRivalBase();

	/** Hero strikes route here (CLASH row: duel meters take 8/8/15 embers). */
	UFUNCTION(BlueprintCallable, Category = "Rival")
	void TakeStrike(int32 ComboBeat, bool bCharged);

	/** Charged-strike / future stagger sources: opens the punish window. */
	UFUNCTION(BlueprintCallable, Category = "Rival")
	void TakeStagger(float Seconds);

	UFUNCTION(BlueprintPure, Category = "Rival")
	bool IsDefeated() const { return State == ERivalState::Defeated; }

	// Dashboard getters (the HUD reads these; never pokes internals).
	bool IsDueling() const { return State != ERivalState::Waiting && State != ERivalState::Defeated; }
	float GetDuelFraction() const;

	// ---------------- Duel tuning (shared across all rivals) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float DuelStartRadius = 900.f;

	/** Walk-away allowed: past this he stands down and the meter refills. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float DisengageRadius = 1500.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float ApproachSpeed = 600.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float TurnRate = 7.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float DuelHitEmbers = 20.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float KnockbackForce = 880.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float KnockbackLift = 380.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float LightStrikeEmbers = 8.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float HeavyStrikeEmbers = 15.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float StaggerSeconds = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float Phase2Fraction = 0.66f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float Phase3Fraction = 0.33f;

	/** Charter rule 7: two hero flame-outs soften the tells by +20%, invisibly. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Duel")
	float TellSoftenScale = 1.2f;

	// ---------------- Pacing (per-rival values set in ctor; cosmetic) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Pacing")
	float IntroSeconds = 1.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Pacing")
	float ApproachAnimRate = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Pacing")
	float TelegraphPulseHz = 20.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Pacing")
	float TelegraphPulseIntensity = 6000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Pacing")
	float PhaseRoarSeconds = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Pacing")
	float FlinchSeconds = 0.45f;

	// ---------------- Impact cosmetics (per-rival color in ctor) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|FX")
	FLinearColor HitBurstColor = FLinearColor(3.f, 1.65f, 0.6f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|FX")
	float HitBurstScale = 1.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|FX")
	float HitBurstLight = 5000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|FX")
	FLinearColor StaggerBurstColor = FLinearColor(5.f, 2.5f, 0.8f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|FX")
	float StaggerBurstScale = 1.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|FX")
	float StaggerBurstLight = 5200.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|FX")
	FLinearColor DefeatBurstColor = FLinearColor(3.f, 1.5f, 0.5f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|FX")
	float DefeatBurstScale = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|FX")
	float DefeatBurstLight = 7500.f;

	// ---------------- Placement / contact (shared) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Anim")
	float SkelMeshYaw = -90.f;   // native FBX law

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Anim")
	float SkelMeshScale = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Contact")
	FContactProfile ContactProfile;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rival|Contact")
	float SeparationPush = 1600.f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	// ---------------- Shared components ----------------
	UPROPERTY(VisibleAnywhere, Category = "Rival")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "Rival")
	USkeletalMeshComponent* RivalBody;

	UPROPERTY(VisibleAnywhere, Category = "Rival")
	UStaticMeshComponent* PlaceholderBody;

	UPROPERTY(VisibleAnywhere, Category = "Rival")
	UEmberMeterComponent* DuelMeter;

	UPROPERTY(VisibleAnywhere, Category = "Rival")
	UPointLightComponent* TelegraphLight;

	UFUNCTION()
	void HandleDuelMeterEmpty();

	// ---------------- Shared helpers (concrete) ----------------
	ASparkHeroCharacter* ResolveHero() const;   // P-switch-proof: never cache
	void EnterState(ERivalState NewState, float Duration);
	void FaceHero(const ASparkHeroCharacter* Hero, float DeltaTime);
	void PlayLoop(UAnimSequence* Clip, float Rate = 1.f);
	void PlayOneShot(UAnimSequence* Clip, float FitSeconds, float StartFraction = 0.f, float OverrideRate = 0.f);
	void FinishAttack(float RecoverSeconds);
	void LandDuelHit(ASparkHeroCharacter* Hero, float Embers);
	float TellScale() const { return HeroLossCount >= 2 ? TellSoftenScale : 1.f; }
	float Now() const;

	/** Replaces the per-file anon-namespace KrakenClip/ReaverClip/StalkerClip
	    helpers — a class-scoped static has a unique name (no unity-build ODR
	    clash) and no per-file duplication. The FObjectFinder itself MUST still
	    be declared static inside each concrete subclass constructor. */
	static UAnimSequence* LoadRivalClip(const ConstructorHelpers::FObjectFinder<UAnimSequence>& Finder);

	// ---------------- Pure-virtual seams (each rival fills) ----------------
	virtual void SelectMove(float DistToHero) PURE_VIRTUAL(ASparkRivalBase::SelectMove, );
	virtual void StartTelegraph() PURE_VIRTUAL(ASparkRivalBase::StartTelegraph, );
	virtual void StartAttack() PURE_VIRTUAL(ASparkRivalBase::StartAttack, );
	virtual void TickAttack(float DeltaTime, ASparkHeroCharacter* Hero) PURE_VIRTUAL(ASparkRivalBase::TickAttack, );
	/** Runs at attack-expiry: the subclass does any chaining/side-effects and
	    calls FinishAttack(...) itself (or re-enters Attack/Vanished). This is the
	    one place the three diverge most (Kraken grip-slam, Reaver simple recover,
	    Stalker phase-3 chained blink), so it is a full seam, not a duration getter. */
	virtual void HandleAttackExpired(ASparkHeroCharacter* Hero) PURE_VIRTUAL(ASparkRivalBase::HandleAttackExpired, );
	virtual float GetTriggerRange() const PURE_VIRTUAL(ASparkRivalBase::GetTriggerRange, return 0.f;);
	virtual bool HasMoveSelected() const PURE_VIRTUAL(ASparkRivalBase::HasMoveSelected, return false;);
	virtual void ClearMove() PURE_VIRTUAL(ASparkRivalBase::ClearMove, );

	// ---------------- Virtual hooks (default behavior in base) ----------------
	/** The Kraken returns !bGripHolding (the grip legally owns the hero). */
	virtual bool AllowSeparationPush() const { return true; }
	/** Pre-damage embers tweak: the Reaver's blind-cone 1.5x lives here. */
	virtual float ModifyIncomingEmbers(float Embers, int32 ComboBeat, bool bCharged) { return Embers; }
	/** Post-damage short-circuit: the Stalker's blink-feint break lives here.
	    Return true if the strike was fully handled (skip phase/stagger routing). */
	virtual bool OnStruck(int32 ComboBeat, bool bCharged) { return false; }
	/** Purge any per-move physics on every interrupt path (Kraken grip/tether). */
	virtual void ClearActiveMoveState() {}
	/** Fired when the Vanished window expires (Stalker -> DoArrive). */
	virtual void OnVanishedExpired() {}
	/** Per-rival BeginPlay tail (Kraken creates its tether MID here, NOT the ctor). */
	virtual void PostRivalBeginPlay() {}
	/** Subclasses forward these to their own BlueprintImplementableEvents. */
	virtual void NotifyRivalDefeated() {}
	virtual void NotifyRivalPhaseChanged(int32 NewPhase) {}

	// ---------------- Shared state ----------------
	ERivalState State = ERivalState::Waiting;
	float StateUntil = 0.f;
	int32 Phase = 1;
	int32 HeroLossCount = 0;   // Charter 7 softening tally (increment left to subclass/BP)
	bool bHitThisAttack = false;
	bool bHasSkeletalModel = false;
	TObjectPtr<UAnimSequence> CurrentLoop;   // non-UPROPERTY de-dupe cache

	// ---------------- Universal clip slots (subclass ctor fills) ----------------
	UPROPERTY() TObjectPtr<UAnimSequence> IdleAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> MoveAnim;     // walk/run locomotion loop
	UPROPERTY() TObjectPtr<UAnimSequence> StaggerAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> HitReactAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> DefeatAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> TauntAnim;
};
