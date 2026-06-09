#include "SparkHeroCharacter.h"

#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

ASparkHeroCharacter::ASparkHeroCharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	// --- Collision capsule: a compact hero ---
	GetCapsuleComponent()->InitCapsuleSize(34.f, 72.f);

	// --- Platformer-style rotation: face where you RUN, not where you LOOK ---
	bUseControllerRotationYaw = false;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->bOrientRotationToMovement = true;
	Move->RotationRate = FRotator(0.f, 780.f, 0.f);
	Move->MaxWalkSpeed = MaxRunSpeed;
	Move->MaxAcceleration = GroundAcceleration;
	Move->BrakingDecelerationWalking = BrakingDeceleration;
	Move->GroundFriction = 8.f;
	Move->GravityScale = BaseGravityScale;
	Move->JumpZVelocity = JumpVelocity;
	Move->AirControl = AirControlAmount;
	Move->BrakingDecelerationFalling = 200.f;

	// --- Visual root so squash & stretch never touches collision ---
	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	VisualRoot->SetupAttachment(RootComponent);

	// Placeholder Spark Hero from engine primitives: egg-shaped sphere body + sphere head.
	// (UE 5.7 ships no Capsule in /Engine/BasicShapes — only Cone/Cube/Cylinder/Plane/Sphere.)
	// The real procedural-modeled hero (glTF) replaces these meshes later.
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));

	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BodyMesh"));
	BodyMesh->SetupAttachment(VisualRoot);
	BodyMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMesh.Succeeded())
	{
		BodyMesh->SetStaticMesh(SphereMesh.Object);
	}
	BodyMesh->SetRelativeScale3D(FVector(0.70f, 0.70f, 1.05f));
	BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, -18.f));

	SparkHead = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SparkHead"));
	SparkHead->SetupAttachment(VisualRoot);
	SparkHead->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMesh.Succeeded())
	{
		SparkHead->SetStaticMesh(SphereMesh.Object);
	}
	SparkHead->SetRelativeScale3D(FVector(0.52f));
	SparkHead->SetRelativeLocation(FVector(0.f, 0.f, 52.f));

	// --- Camera rig: spring arm with collision probe + lag, free orbit ---
	SpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("SpringArm"));
	SpringArm->SetupAttachment(RootComponent);
	SpringArm->TargetArmLength = BaseArmLength;
	SpringArm->bUsePawnControlRotation = true;   // orbit follows the player's look input
	SpringArm->bDoCollisionTest = true;          // push in instead of clipping through walls
	SpringArm->ProbeSize = 14.f;
	SpringArm->bEnableCameraLag = true;
	SpringArm->CameraLagSpeed = 12.f;
	SpringArm->bEnableCameraRotationLag = true;
	SpringArm->CameraRotationLagSpeed = 18.f;
	SpringArm->SocketOffset = FVector(0.f, 0.f, 60.f);  // frame the hero slightly low in shot

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(SpringArm, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;
	FollowCamera->FieldOfView = 80.f;
}

float ASparkHeroCharacter::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void ASparkHeroCharacter::BeginPlay()
{
	Super::BeginPlay();

	AirJumpsRemaining = MaxAirJumps;
	AirDashesRemaining = MaxAirDashes;
	GetCharacterMovement()->GravityScale = BaseGravityScale;

	// Tint the placeholder hero in the Anthropic palette. The sphere asset's default
	// slot is the grid material (no Color param), so explicitly base our dynamic
	// materials on the engine's tintable BasicShapeMaterial.
	const FLinearColor SparkOrange(0.851f, 0.467f, 0.341f); // #d97757
	const FLinearColor Cream(0.980f, 0.976f, 0.961f);       // #faf9f5
	if (UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
	{
		if (BodyMesh)
		{
			UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
			MID->SetVectorParameterValue(TEXT("Color"), SparkOrange);
			BodyMesh->SetMaterial(0, MID);
		}
		if (SparkHead)
		{
			UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
			MID->SetVectorParameterValue(TEXT("Color"), Cream);
			SparkHead->SetMaterial(0, MID);
		}
	}

	// Camera pitch limits (don't let the orbit flip under the floor / over the top).
	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (PC->PlayerCameraManager)
		{
			PC->PlayerCameraManager->ViewPitchMin = CameraPitchMin;
			PC->PlayerCameraManager->ViewPitchMax = CameraPitchMax;
		}
	}
}

// ---------------------------------------------------------------------------
// Input: built entirely at runtime so the project needs zero input .uassets.
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::BuildInputObjects()
{
	if (MappingContext) { return; }

	MappingContext = NewObject<UInputMappingContext>(this, TEXT("SparkHeroMappingContext"));

	MoveAction = NewObject<UInputAction>(this, TEXT("IA_Move"));
	MoveAction->ValueType = EInputActionValueType::Axis2D;

	LookAction = NewObject<UInputAction>(this, TEXT("IA_Look"));
	LookAction->ValueType = EInputActionValueType::Axis2D;

	JumpAction = NewObject<UInputAction>(this, TEXT("IA_Jump"));
	JumpAction->ValueType = EInputActionValueType::Boolean;

	DashAction = NewObject<UInputAction>(this, TEXT("IA_Dash"));
	DashAction->ValueType = EInputActionValueType::Boolean;

	FastFallAction = NewObject<UInputAction>(this, TEXT("IA_FastFall"));
	FastFallAction->ValueType = EInputActionValueType::Boolean;

	auto AddSwizzle = [this](FEnhancedActionKeyMapping& M)
	{
		M.Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(MappingContext)); // X -> Y
	};
	auto AddNegate = [this](FEnhancedActionKeyMapping& M)
	{
		M.Modifiers.Add(NewObject<UInputModifierNegate>(MappingContext));
	};

	// Move: WASD (Y = forward, X = right) + gamepad left stick.
	AddSwizzle(MappingContext->MapKey(MoveAction, EKeys::W));
	{
		FEnhancedActionKeyMapping& M = MappingContext->MapKey(MoveAction, EKeys::S);
		AddNegate(M); AddSwizzle(M);
	}
	AddNegate(MappingContext->MapKey(MoveAction, EKeys::A));
	MappingContext->MapKey(MoveAction, EKeys::D);
	MappingContext->MapKey(MoveAction, EKeys::Gamepad_Left2D);

	// Look: mouse + gamepad right stick.
	MappingContext->MapKey(LookAction, EKeys::Mouse2D);
	MappingContext->MapKey(LookAction, EKeys::Gamepad_Right2D);

	// Jump / dash / fast-fall.
	MappingContext->MapKey(JumpAction, EKeys::SpaceBar);
	MappingContext->MapKey(JumpAction, EKeys::Gamepad_FaceButton_Bottom);
	MappingContext->MapKey(DashAction, EKeys::LeftShift);
	MappingContext->MapKey(DashAction, EKeys::Gamepad_FaceButton_Left);
	MappingContext->MapKey(FastFallAction, EKeys::LeftControl);
	MappingContext->MapKey(FastFallAction, EKeys::Gamepad_RightShoulder);
}

void ASparkHeroCharacter::NotifyControllerChanged()
{
	Super::NotifyControllerChanged();

	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
			ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
		{
			BuildInputObjects();
			Subsystem->ClearAllMappings();
			Subsystem->AddMappingContext(MappingContext, 0);
		}
	}
}

void ASparkHeroCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	BuildInputObjects();
	if (UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent))
	{
		EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this, &ASparkHeroCharacter::HandleMove);
		EIC->BindAction(LookAction, ETriggerEvent::Triggered, this, &ASparkHeroCharacter::HandleLook);
		EIC->BindAction(JumpAction, ETriggerEvent::Started, this, &ASparkHeroCharacter::HandleJumpPressed);
		EIC->BindAction(JumpAction, ETriggerEvent::Completed, this, &ASparkHeroCharacter::HandleJumpReleased);
		EIC->BindAction(DashAction, ETriggerEvent::Started, this, &ASparkHeroCharacter::HandleDashPressed);
		EIC->BindAction(FastFallAction, ETriggerEvent::Started, this, &ASparkHeroCharacter::HandleFastFallPressed);
		EIC->BindAction(FastFallAction, ETriggerEvent::Completed, this, &ASparkHeroCharacter::HandleFastFallReleased);
	}
}

// ---------------------------------------------------------------------------
// Movement
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::HandleMove(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	if (Controller == nullptr || Axis.IsNearlyZero()) { return; }

	// Player-relative: move in the camera's yaw frame.
	const FRotator YawRot(0.f, Controller->GetControlRotation().Yaw, 0.f);
	const FVector Forward = FRotationMatrix(YawRot).GetUnitAxis(EAxis::X);
	const FVector Right = FRotationMatrix(YawRot).GetUnitAxis(EAxis::Y);

	const FVector WorldInput = (Forward * Axis.Y + Right * Axis.X);
	if (!WorldInput.IsNearlyZero())
	{
		LastWorldMoveInput = WorldInput.GetSafeNormal();
	}
	if (!bIsDashing) // dashing owns velocity for its duration
	{
		AddMovementInput(Forward, Axis.Y);
		AddMovementInput(Right, Axis.X);
	}
}

void ASparkHeroCharacter::HandleLook(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	AddControllerYawInput(Axis.X * LookSensitivity);
	const float PitchSign = bInvertLookY ? 1.f : -1.f;
	AddControllerPitchInput(Axis.Y * LookSensitivity * PitchSign);
}

// ---------------------------------------------------------------------------
// Jumping: coyote time + buffering + variable height + double-jump
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::HandleJumpPressed()
{
	LastJumpPressedTime = Now();
	TryJump();
}

void ASparkHeroCharacter::TryJump()
{
	UCharacterMovementComponent* Move = GetCharacterMovement();
	const bool bGrounded = Move->IsMovingOnGround();
	const bool bInCoyote = !bCoyoteConsumed && (Now() - LastGroundedTime) <= CoyoteTime;

	if (bGrounded || bInCoyote)
	{
		bCoyoteConsumed = true;
		DoJump(false);
	}
	else if (AirJumpsRemaining > 0)
	{
		AirJumpsRemaining--;
		DoJump(true);
	}
	// else: the press stays buffered; Landed() will consume it if we touch down in time.
}

void ASparkHeroCharacter::DoJump(bool bAirJump)
{
	if (bIsDashing) { EndDash(); } // jump cancels dash

	const float Vz = bAirJump ? AirJumpVelocity : JumpVelocity;
	FVector Vel = GetCharacterMovement()->Velocity;
	Vel.Z = Vz;
	GetCharacterMovement()->Velocity = Vel;
	GetCharacterMovement()->SetMovementMode(MOVE_Falling);

	ApplySquash(JumpStretch);
	OnHeroJumped(bAirJump);
}

void ASparkHeroCharacter::HandleJumpReleased()
{
	// Variable jump height: chop upward speed when the button is released early.
	UCharacterMovementComponent* Move = GetCharacterMovement();
	if (Move->Velocity.Z > JumpCutoffVelocity)
	{
		FVector Vel = Move->Velocity;
		Vel.Z = JumpCutoffVelocity;
		Move->Velocity = Vel;
	}
}

void ASparkHeroCharacter::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);

	const float ImpactSpeed = FMath::Abs(PrevTickVelZ);
	LastGroundedTime = Now();
	bCoyoteConsumed = false;
	AirJumpsRemaining = MaxAirJumps;
	AirDashesRemaining = MaxAirDashes;
	if (bFastFalling) { HandleFastFallReleased(); }

	// Landing squash scales with how hard we hit.
	const float Strength = FMath::GetMappedRangeValueClamped(
		FVector2f(400.f, 2000.f), FVector2f(0.94f, LandSquash), ImpactSpeed);
	ApplySquash(Strength);
	OnHeroLanded(ImpactSpeed);

	// Jump buffering: a press just before touchdown fires now.
	if ((Now() - LastJumpPressedTime) <= JumpBufferTime)
	{
		LastJumpPressedTime = -1000.f; // consume
		TryJump();
	}
}

// ---------------------------------------------------------------------------
// Spark dash
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::HandleDashPressed()
{
	if (bIsDashing) { return; }
	if ((Now() - LastDashEndTime) < DashCooldown) { return; }

	const bool bGrounded = GetCharacterMovement()->IsMovingOnGround();
	if (!bGrounded)
	{
		if (AirDashesRemaining <= 0) { return; }
		AirDashesRemaining--;
	}

	bIsDashing = true;
	FVector Dir = LastWorldMoveInput.IsNearlyZero() ? GetActorForwardVector() : LastWorldMoveInput;
	Dir.Z = 0.f;
	Dir = Dir.GetSafeNormal();

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->GravityScale = 0.f;                      // a flat, confident zip
	Move->Velocity = Dir * DashSpeed;

	GetWorldTimerManager().SetTimer(DashTimerHandle, this, &ASparkHeroCharacter::EndDash,
	                                DashDuration, false);
	OnDashStarted(Dir);
}

void ASparkHeroCharacter::EndDash()
{
	if (!bIsDashing) { return; }
	bIsDashing = false;
	LastDashEndTime = Now();
	GetWorldTimerManager().ClearTimer(DashTimerHandle);

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->GravityScale = bFastFalling ? FastFallGravityScale : BaseGravityScale;
	// Bleed the dash speed down to run speed so we exit smoothly, not with a snap.
	FVector Vel = Move->Velocity;
	const FVector VelXY(Vel.X, Vel.Y, 0.f);
	if (VelXY.Size() > MaxRunSpeed)
	{
		const FVector Clamped = VelXY.GetSafeNormal() * MaxRunSpeed;
		Move->Velocity = FVector(Clamped.X, Clamped.Y, Vel.Z);
	}
	OnDashEnded();
}

// ---------------------------------------------------------------------------
// Fast-fall
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::HandleFastFallPressed()
{
	if (GetCharacterMovement()->IsMovingOnGround() || bIsDashing) { return; }
	bFastFalling = true;
	GetCharacterMovement()->GravityScale = FastFallGravityScale;
}

void ASparkHeroCharacter::HandleFastFallReleased()
{
	bFastFalling = false;
	if (!bIsDashing)
	{
		GetCharacterMovement()->GravityScale = BaseGravityScale;
	}
}

// ---------------------------------------------------------------------------
// Per-frame: grounded tracking, context camera, squash recovery
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	UCharacterMovementComponent* Move = GetCharacterMovement();

	// Track the last moment we stood on ground (coyote time reads this).
	if (Move->IsMovingOnGround())
	{
		LastGroundedTime = Now();
		bCoyoteConsumed = false;
	}
	PrevTickVelZ = Move->Velocity.Z;

	// Keep live-tuned values flowing into the movement component (editor tuning).
	Move->MaxWalkSpeed = MaxRunSpeed;
	Move->MaxAcceleration = GroundAcceleration;
	Move->BrakingDecelerationWalking = BrakingDeceleration;
	Move->AirControl = AirControlAmount;

	// Context camera distance: tighter when looking down, wider when looking up.
	if (Controller && SpringArm)
	{
		const float Pitch = static_cast<float>(FRotator::NormalizeAxis(Controller->GetControlRotation().Pitch));
		float TargetLen = BaseArmLength;
		if (Pitch < 0.f)
		{
			TargetLen = FMath::GetMappedRangeValueClamped(
				FVector2f(CameraPitchMin, 0.f), FVector2f(ArmLengthLookingDown, BaseArmLength), Pitch);
		}
		else
		{
			TargetLen = FMath::GetMappedRangeValueClamped(
				FVector2f(0.f, CameraPitchMax), FVector2f(BaseArmLength, ArmLengthLookingUp), Pitch);
		}
		SpringArm->TargetArmLength = FMath::FInterpTo(SpringArm->TargetArmLength, TargetLen,
		                                              DeltaSeconds, 4.f);
	}

	// Squash & stretch spring-back.
	if (VisualRoot)
	{
		VisualScaleCurrent = FMath::VInterpTo(VisualScaleCurrent, VisualScaleTarget,
		                                      DeltaSeconds, SquashRecoverySpeed);
		VisualRoot->SetRelativeScale3D(VisualScaleCurrent);
		if (VisualScaleCurrent.Equals(VisualScaleTarget, 0.01f))
		{
			VisualScaleTarget = FVector::OneVector;
		}
	}
}

void ASparkHeroCharacter::ApplySquash(float ZScale)
{
	// Conserve apparent volume: squashing down bulges XY, stretching up slims XY.
	const float XY = FMath::Sqrt(FMath::Max(0.05f, 1.f / FMath::Max(ZScale, 0.05f)));
	VisualScaleTarget = FVector(XY, XY, ZScale);
	VisualScaleCurrent = VisualScaleTarget; // snap to the pose, spring back to 1
}
