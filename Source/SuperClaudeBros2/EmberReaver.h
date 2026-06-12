// Super Claude Bros 2 — THE EMBER REAVER, rival #2 (spec §4). The aspirational
// duel: where the Kraken is the skill check you pass, the Reaver is the one
// you train for — faster tells, a 0.7s opening (canon), and an arena that
// catches fire behind him. His unique power is the EMBER TRAIL: every dash
// paints burning ground (AEmberTrailPatch). His asymmetry is GEOMETRY, not
// stats: one eye — strikes from inside his blind cone bite 1.5x deeper.
// Crimson, cracked dome, spiked pauldron. In W4 he fights BESIDE you (ally v1).
//
// Deliberately a CONCRETE sibling of AKrakenBoss (prototype-first doctrine):
// the ASparkRivalBase extraction happens when rival #3 (the Stalker) lands.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SparkContactTypes.h"
#include "EmberReaver.generated.h"

class ASparkHeroCharacter;
class UEmberMeterComponent;
class UPointLightComponent;
class UAnimSequence;

UENUM(BlueprintType)
enum class EReaverState : uint8
{
	Waiting, Intro, Approach, Telegraph, Attack, Recover, Staggered, Defeated
};

UENUM(BlueprintType)
enum class EReaverMove : uint8
{
	None,
	FeintSlash,      // quick counter-slash; recover 0.7s = THE canon opening
	CrossingFlurry,  // a three-beat pressure string; sidestep or guard
	EmberDash        // the SIGNATURE: he crosses you at speed, ground ignites
};

UCLASS()
class AEmberReaver : public ACharacter
{
	GENERATED_BODY()

public:
	AEmberReaver();

	/** CLASH row (8/8/15) — strikes from his BLIND CONE land 1.5x (geometry
	    beats stats: he has one eye, and the duel teaches you to use it). */
	UFUNCTION(BlueprintCallable, Category = "Reaver")
	void TakeStrike(int32 ComboBeat, bool bCharged);

	UFUNCTION(BlueprintCallable, Category = "Reaver")
	void TakeStagger(float Seconds);

	UFUNCTION(BlueprintPure, Category = "Reaver")
	bool IsDefeated() const { return State == EReaverState::Defeated; }

	UFUNCTION(BlueprintImplementableEvent, Category = "Reaver")
	void OnReaverDefeated();

	UFUNCTION(BlueprintImplementableEvent, Category = "Reaver")
	void OnReaverPhaseChanged(int32 NewPhase);

	// ---------------- Duel tuning ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float DuelStartRadius = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float DisengageRadius = 1500.f;

	/** Faster than the hero walks — pressure is his language. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float ApproachSpeed = 720.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float TurnRate = 8.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float DuelHitEmbers = 20.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float KnockbackForce = 820.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float KnockbackLift = 360.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float LightStrikeEmbers = 8.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float HeavyStrikeEmbers = 15.f;

	/** The one-eye rule: half-angle of the blind cone behind him, and the
	    multiplier strikes earn inside it (spec §4: cone ~110° total). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float BlindConeHalfAngleDeg = 55.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float BlindSideMultiplier = 1.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float StaggerSeconds = 1.8f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float Phase2Fraction = 0.66f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float Phase3Fraction = 0.33f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Duel")
	float TellSoftenScale = 1.2f;

	// ---------------- Feint Slash ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Moves")
	float SlashTell = 0.45f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Moves")
	float SlashActive = 0.28f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Moves")
	float SlashRecover = 0.7f;    // THE canon opening

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Moves")
	float SlashReach = 240.f;

	// ---------------- Crossing Flurry ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Moves")
	float FlurryTell = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Moves")
	float FlurryActive = 0.85f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Moves")
	float FlurryRecover = 0.9f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Moves")
	float FlurryReach = 250.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Moves")
	float FlurryStepSpeed = 420.f;   // he walks you down through the string

	// ---------------- EMBER DASH (the signature power) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|EmberDash")
	float DashTell = 0.4f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|EmberDash")
	float DashSpeed = 1600.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|EmberDash")
	float DashMaxSeconds = 0.55f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|EmberDash")
	float DashRecover = 0.8f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|EmberDash")
	float DashHitRange = 130.f;

	/** Ground ignites this often along his path. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|EmberDash")
	float TrailSpacing = 75.f;

	// ---------------- Clip windows (data-scanned June 12; all live) ----------------
	/** Slash scan: the counter-slash is a body-drop + max arm reach at frac
	    0.75-0.81 of the long routine — start at the coil before it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SlashClipStart = 0.62f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Anim")
	float SlashClipRate = 2.0f;

	/** Flurry scan: the triple lands at frac 0.42 / 0.50 / 0.66 — rate 1.3
	    syncs the string to the two damage marks in the active window. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float FlurryClipStart = 0.28f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Anim")
	float FlurryClipRate = 1.3f;

	/** Dash: the dodge-lean at frac 0.40; the 1600uu/s velocity sells the rest. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float DashClipStart = 0.36f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Anim")
	float DashClipRate = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Anim")
	float SkelMeshYaw = -90.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Anim")
	float SkelMeshScale = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Contact")
	FContactProfile ContactProfile;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reaver|Contact")
	float SeparationPush = 1600.f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	UPROPERTY(VisibleAnywhere, Category = "Reaver")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "Reaver")
	USkeletalMeshComponent* ReaverBody;

	UPROPERTY(VisibleAnywhere, Category = "Reaver")
	UStaticMeshComponent* PlaceholderBody;

	UPROPERTY(VisibleAnywhere, Category = "Reaver")
	UEmberMeterComponent* DuelMeter;

	/** Ember-red tell glow — his own color (hero amber / Kraken violet taken). */
	UPROPERTY(VisibleAnywhere, Category = "Reaver")
	UPointLightComponent* TelegraphLight;

	UFUNCTION()
	void HandleDuelMeterEmpty();

private:
	EReaverState State = EReaverState::Waiting;
	EReaverMove Move = EReaverMove::None;
	float StateUntil = 0.f;
	int32 Phase = 1;
	int32 HeroLossCount = 0;
	bool bHitThisAttack = false;
	int32 FlurryHitsDone = 0;
	FVector DashDirection = FVector::ForwardVector;
	float DashUntil = 0.f;
	FVector LastTrailPos = FVector::ZeroVector;
	int32 DashesThisAttack = 0;

	UPROPERTY() TObjectPtr<UAnimSequence> IdleAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> RunAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> SlashAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> DashAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> FlurryAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> StaggerAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> HitReactAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> DefeatAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> TauntAnim;
	bool bHasSkeletalModel = false;
	TObjectPtr<UAnimSequence> CurrentLoop;

	ASparkHeroCharacter* ResolveHero() const;
	void EnterState(EReaverState NewState, float Duration);
	void SelectMove(float DistToHero);
	void StartTelegraph();
	void StartAttack();
	void StartDashLeg(const ASparkHeroCharacter* Hero);
	void FinishAttack(float RecoverSeconds);
	void TickAttack(float DeltaTime, ASparkHeroCharacter* Hero);
	void LandDuelHit(ASparkHeroCharacter* Hero, float Embers);
	void FaceHero(const ASparkHeroCharacter* Hero, float DeltaTime);
	void PlayLoop(UAnimSequence* Clip, float Rate = 1.f);
	void PlayOneShot(UAnimSequence* Clip, float FitSeconds, float StartFraction = 0.f, float OverrideRate = 0.f);
	float TellScale() const { return HeroLossCount >= 2 ? TellSoftenScale : 1.f; }
	float Now() const;
};
