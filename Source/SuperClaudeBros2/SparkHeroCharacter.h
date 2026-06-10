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
class USceneComponent;
class UInputAction;
class UInputMappingContext;

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

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<USpringArmComponent> SpringArm;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UCameraComponent> FollowCamera;

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
	void HandleFastFallPressed();
	void HandleFastFallReleased();

private:
	// Runtime-built Enhanced Input (no content assets needed).
	void BuildInputObjects();

	UPROPERTY(Transient) TObjectPtr<UInputMappingContext> MappingContext;
	UPROPERTY(Transient) TObjectPtr<UInputAction> MoveAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> LookAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> JumpAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> DashAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> FastFallAction;

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

	// Respawn (solid-ground guarantee)
	void RespawnAtStart();
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
};
