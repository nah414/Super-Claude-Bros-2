// Super Claude Bros 2 — the Spark Hero.
// A 3D platformer character built for FEEL: momentum movement, variable-height jump,
// double-jump, coyote time, jump buffering, fast-fall, and a signature spark-dash.
// Every tunable is an EditAnywhere UPROPERTY so feel can be tuned live in-editor
// without recompiling. Input is built entirely in C++ at runtime (no .uasset deps).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "InputActionValue.h"
#include "SparkHeroCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class USceneComponent;
class UInputAction;
class UInputMappingContext;
class UAnimSequence;
class UEmberMeterComponent;
class UPointLightComponent;

UCLASS()
class ASparkHeroCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	ASparkHeroCharacter();

	// ---------------- Components ----------------
	/** Scales for squash & stretch without touching the collision capsule. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<USceneComponent> VisualRoot;

	/** Placeholder body (engine capsule mesh) until the real Spark Hero model lands. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UStaticMeshComponent> BodyMesh;

	/** Placeholder spark head (engine sphere mesh). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UStaticMeshComponent> SparkHead;

	/** The rigged hero (Meshy pipeline). When it loads, the static placeholders hide. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<USkeletalMeshComponent> SkelBody;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<USpringArmComponent> SpringArm;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UCameraComponent> FollowCamera;

	/** The Ember Meter — the hero's health IS this flame (SCB2_INTERACTION_SPEC.md §2). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UEmberMeterComponent> EmberMeter;

	/** The visible Spark-flame above the dome; the meter drives its height. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UStaticMeshComponent> EmberFlame;

	/** The flame's warm light — the world dims with the hero's health, no HUD. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UPointLightComponent> EmberGlow;

	// ---------------- Movement feel ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Movement")
	float MaxRunSpeed = 650.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Movement")
	float GroundAcceleration = 2600.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Movement")
	float BrakingDeceleration = 2200.f;

	/** 0..1 — how much steering you keep while airborne. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Movement", meta = (ClampMin = "0", ClampMax = "1"))
	float AirControlAmount = 0.85f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Movement")
	float BaseGravityScale = 1.9f;

	/** Falling below this world Z teleports the hero back to the start — no endless void falls. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|World")
	float RespawnBelowZ = -2000.f;

	// ---------------- Jump feel ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float JumpVelocity = 950.f;

	/** Releasing jump while rising clamps upward speed to this — variable jump height. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float JumpCutoffVelocity = 320.f;

	/** Grace window after walking off a ledge in which a jump still counts (seconds). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float CoyoteTime = 0.12f;

	/** Pressing jump slightly before landing still fires the jump (seconds). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float JumpBufferTime = 0.10f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	int32 MaxAirJumps = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float AirJumpVelocity = 850.f;

	/** Holding fast-fall in the air multiplies gravity by this. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float FastFallGravityScale = 3.4f;

	// ---------------- Spark dash ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Dash")
	float DashSpeed = 1900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Dash")
	float DashDuration = 0.18f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Dash")
	float DashCooldown = 0.7f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Dash")
	int32 MaxAirDashes = 1;

	// ---------------- The Spark Combo (hand-to-hand — Adam's June 11 lock) ----------------
	// Three beats: tentacle lash, tentacle lash, fist HAYMAKER. No block button —
	// the dash is the dodge. Full design: SCB2_POWERS_CODEX.md §1.
	/** How far ahead of the hero the strike sphere lands. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeRange = 85.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeRadius = 55.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeLightDuration = 0.22f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeHeavyDuration = 0.38f;

	/** Forward step the lash carries (the strike IS movement — squid boxing). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeLightLunge = 420.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeHeavyLunge = 550.f;

	/** Next beat must be pressed within this window after a beat ends, or the combo resets. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeComboWindow = 0.45f;

	/** Breather after the haymaker before the string can start again. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeComboCooldown = 0.35f;

	// ---------------- Camera feel ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float BaseArmLength = 460.f;

	/** Arm length when looking steeply DOWN (tighter, tactical). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float ArmLengthLookingDown = 330.f;

	/** Arm length when looking UP (wider, scenic). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float ArmLengthLookingUp = 580.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float LookSensitivity = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	bool bInvertLookY = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float CameraPitchMin = -70.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float CameraPitchMax = 45.f;

	// ---------------- Squash & stretch ----------------
	/** Z scale on landing (XY bulges to conserve volume). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Juice")
	float LandSquash = 0.80f;

	/** Z scale on jump takeoff. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Juice")
	float JumpStretch = 1.14f;

	/** How fast the visual scale springs back to 1. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Juice")
	float SquashRecoverySpeed = 11.f;

	// ---------------- Event hooks (Niagara/SFX wire in later, in Blueprint) ----------------
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroJumped(bool bWasAirJump);

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroLanded(float ImpactSpeed);

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnDashStarted(FVector DashDirection);

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnDashEnded();

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroRespawned();

	/** A hit got through (grace didn't eat it). NewFraction is the flame's new 0..1. */
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroEmberHit(float NewFraction);

	/** The flame went out. Fires just before the lantern relights the hero. */
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroFlameOut();

	/** Enemies route ember damage through here (Contact Matrix, spec §5). Knockback
	    is the caller's job and always applies; fire only drains outside grace. */
	UFUNCTION(BlueprintCallable, Category = "SparkHero")
	void TakeEmberHit(float Embers);

	/** True while the spark-dash owns the hero's velocity (read by enemies for dash-kills). */
	UFUNCTION(BlueprintPure, Category = "SparkHero")
	bool IsDashing() const { return bIsDashing; }

	/** True mid-strike (read by duelists for CLASH resolution, later). */
	UFUNCTION(BlueprintPure, Category = "SparkHero")
	bool IsStriking() const { return bStriking; }

	/** A combo beat fired (0/1 = lash, 2 = haymaker) — VFX/SFX seam. */
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroStrike(int32 Beat);

	/** A strike connected with something. */
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroStrikeHit(AActor* Victim, int32 Beat);

	/** Most negative recent vertical velocity — landing zeroes velocity BEFORE contact
	    events fire, so stomp checks must read the fall as it was a tick ago. */
	UFUNCTION(BlueprintPure, Category = "SparkHero")
	float GetRecentFallSpeed() const
	{
		return FMath::Min(GetVelocity().Z, PrevTickVelZ);
	}

	// ---------------- Hero model (imported glb; falls back to placeholder shapes) ----------------
	/** Yaw correction for the imported hero mesh (axis conventions differ between tools). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Model")
	float HeroMeshYaw = -90.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Model")
	float HeroMeshScale = 1.05f;   // mesh is 132uu tall (scale baked); capsule is 144

	/** Yaw correction for the skeletal hero (FBX axis conventions; tuned by screenshot:
	    at 0 the model faces -Y, so +90 turns it to the actor's +X forward). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Model")
	float SkelMeshYaw = 90.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Model")
	float SkelMeshScale = 1.0f;

	// ---------------- Animation (single-node playback; no AnimBP assets) ----------------
	/** Ground speed above which the run cycle replaces the walk cycle. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float RunAnimSpeedThreshold = 420.f;

	/** Ground speed below which the hero counts as standing still. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float WalkAnimMinSpeed = 60.f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void NotifyControllerChanged() override;
	virtual void Landed(const FHitResult& Hit) override;
	virtual void FellOutOfWorld(const UDamageType& DmgType) override;

	// Input handlers
	void HandleMove(const FInputActionValue& Value);
	void HandleLook(const FInputActionValue& Value);
	void HandleJumpPressed();
	void HandleJumpReleased();
	void HandleDashPressed();
	void HandleStrikePressed();
	void HandleFastFallPressed();
	void HandleFastFallReleased();
	void HandleQuit();

private:
	// Runtime-built Enhanced Input (no content assets needed).
	void BuildInputObjects();

	UPROPERTY(Transient) TObjectPtr<UInputMappingContext> MappingContext;
	UPROPERTY(Transient) TObjectPtr<UInputAction> MoveAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> LookAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> JumpAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> DashAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> StrikeAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> FastFallAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> QuitAction;

	// Jump state
	void TryJump();
	void DoJump(bool bAirJump);
	float LastGroundedTime = -1000.f;
	float LastJumpPressedTime = -1000.f;
	int32 AirJumpsRemaining = 0;
	bool bCoyoteConsumed = false;

	// Dash state
	void EndDash();
	bool bIsDashing = false;
	int32 AirDashesRemaining = 0;
	float LastDashEndTime = -1000.f;
	FTimerHandle DashTimerHandle;

	// Strike state (the Spark Combo)
	void DoStrike();
	void StrikeHitCheck();
	void EndStrike();
	bool bStriking = false;
	bool bStrikeQueued = false;
	int32 ComboBeat = 0;                 // 0/1 = lash, 2 = haymaker
	float LastStrikeEndTime = -1000.f;
	float ComboCooldownUntil = -1000.f;
	FTimerHandle StrikeTimerHandle;
	FTimerHandle StrikeHitTimerHandle;

	// True when the imported SparkHero model loaded in the constructor.
	bool bHasRealModel = false;

	// Skeletal hero + clips (constructor-loaded; all optional).
	UPROPERTY() TObjectPtr<UAnimSequence> IdleAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> WalkAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> RunAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> JumpAnim;
	// M0.6 Hero Ascension II — the combo made flesh (+ the relight kneel, wired at M0.2).
	UPROPERTY() TObjectPtr<UAnimSequence> Strike1Anim;
	UPROPERTY() TObjectPtr<UAnimSequence> Strike2Anim;
	UPROPERTY() TObjectPtr<UAnimSequence> HaymakerAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> HitReactAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> RelightAnim;
	bool bHasSkeletalModel = false;

	enum class EHeroAnimState : uint8 { None, Idle, Walk, Run, Jump };
	EHeroAnimState AnimState = EHeroAnimState::None;
	void UpdateHeroAnimation();

	// Action-override layer: one-shot clips (strikes, hit-react) take the body;
	// the locomotion state machine waits, then resumes via the None sentinel.
	void PlayActionClip(UAnimSequence* Clip, float FitDuration);
	void EndActionClip();
	bool bActionAnimActive = false;
	FTimerHandle HitReactTimerHandle;

	// Respawn (solid-ground guarantee)
	void RespawnAtStart();
	UFUNCTION() void HandleFlameOut();   // bound to the meter's OnFlameOut
	FVector SpawnLocation = FVector::ZeroVector;     // the level's PlayerStart
	FRotator SpawnRotation = FRotator::ZeroRotator;
	FVector SafeGroundLocation = FVector::ZeroVector; // last spot we truly stood on

	// Misc state
	FVector LastWorldMoveInput = FVector::ForwardVector; // dash direction fallback
	float PrevTickVelZ = 0.f;                            // landing impact speed
	bool bFastFalling = false;
	FVector VisualScaleTarget = FVector::OneVector;
	FVector VisualScaleCurrent = FVector::OneVector;

	void ApplySquash(float ZScale);
	float Now() const;

	// Juice helpers — every asset is optional (nullptr-safe) so the game runs
	// before/without the audio pack and shake classes.
	void PlaySfx(const TCHAR* AssetPath) const;
	void PlayShake(TSubclassOf<class UCameraShakeBase> ShakeClass) const;
};
