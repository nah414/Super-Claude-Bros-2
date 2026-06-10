#include "SparkHeroCharacter.h"

#include "Animation/AnimSequence.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerStart.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Sound/SoundBase.h"
#include "SparkCameraShakes.h"
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

	// The hero's body. Preferred: the procedurally-modeled SparkHero (imported glb),
	// loaded HERE in the constructor — the proven path that renders (BeginPlay-time
	// SetStaticMesh left the component visible-but-unrendered on 5.7). Fallback:
	// egg-shaped engine sphere placeholder. (UE 5.7 ships no Capsule basic shape.)
	static ConstructorHelpers::FObjectFinder<UStaticMesh> HeroModel(TEXT("/Game/Art/Hero/SparkHero.SparkHero"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));

	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BodyMesh"));
	BodyMesh->SetupAttachment(VisualRoot);
	BodyMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	// MYSTERY SOLVED: the "invisible hero" was the import losing the meters->cm unit
	// conversion — the mesh rendered at 1/100 scale. The glb now bakes the x100 scale,
	// so the imported model is back on.
	constexpr bool bPreferImportedModel = true;
	bHasRealModel = bPreferImportedModel && HeroModel.Succeeded();
	if (bHasRealModel)
	{
		BodyMesh->SetStaticMesh(HeroModel.Object);
		BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, -72.f));   // mesh pivot at feet
		BodyMesh->SetRelativeRotation(FRotator(0.f, HeroMeshYaw, 0.f));
		BodyMesh->SetRelativeScale3D(FVector(HeroMeshScale));
	}
	else if (SphereMesh.Succeeded())
	{
		BodyMesh->SetStaticMesh(SphereMesh.Object);
		BodyMesh->SetRelativeScale3D(FVector(0.70f, 0.70f, 1.05f));
		BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, -18.f));
	}

	SparkHead = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SparkHead"));
	SparkHead->SetupAttachment(VisualRoot);
	SparkHead->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMesh.Succeeded())
	{
		SparkHead->SetStaticMesh(SphereMesh.Object);
	}
	SparkHead->SetRelativeScale3D(FVector(0.52f));
	SparkHead->SetRelativeLocation(FVector(0.f, 0.f, 52.f));

	// The rigged hero from the Meshy pipeline (Blender-baked cm, legacy FBX import).
	// Outranks both static visuals when present. Pivot is at the feet (Blender drops
	// it to ground), so it sits at the capsule's bottom.
	static ConstructorHelpers::FObjectFinder<USkeletalMesh> SkelModel(TEXT("/Game/Art/HeroSkel/SCB2Hero.SCB2Hero"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> WalkClip(TEXT("/Game/Art/HeroSkel/A_Hero_Walk.A_Hero_Walk"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> RunClip(TEXT("/Game/Art/HeroSkel/A_Hero_Run.A_Hero_Run"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> JumpClip(TEXT("/Game/Art/HeroSkel/A_Hero_SpinJump.A_Hero_SpinJump"));

	SkelBody = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("SkelBody"));
	SkelBody->SetupAttachment(VisualRoot);
	SkelBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	bHasSkeletalModel = SkelModel.Succeeded();
	if (bHasSkeletalModel)
	{
		SkelBody->SetSkeletalMesh(SkelModel.Object);
		SkelBody->SetRelativeLocation(FVector(0.f, 0.f, -72.f));
		SkelBody->SetRelativeRotation(FRotator(0.f, SkelMeshYaw, 0.f));
		SkelBody->SetRelativeScale3D(FVector(SkelMeshScale));
		SkelBody->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	}
	WalkAnim = WalkClip.Succeeded() ? WalkClip.Object : nullptr;
	RunAnim = RunClip.Succeeded() ? RunClip.Object : nullptr;
	JumpAnim = JumpClip.Succeeded() ? JumpClip.Object : nullptr;

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

void ASparkHeroCharacter::PlaySfx(const TCHAR* AssetPath) const
{
	if (USoundBase* Sound = LoadObject<USoundBase>(nullptr, AssetPath))
	{
		UGameplayStatics::PlaySoundAtLocation(this, Sound, GetActorLocation());
	}
}

void ASparkHeroCharacter::PlayShake(TSubclassOf<UCameraShakeBase> ShakeClass) const
{
	if (!ShakeClass) { return; }
	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		PC->ClientStartCameraShake(ShakeClass);
	}
}

void ASparkHeroCharacter::BeginPlay()
{
	Super::BeginPlay();

	AirJumpsRemaining = MaxAirJumps;
	AirDashesRemaining = MaxAirDashes;
	GetCharacterMovement()->GravityScale = BaseGravityScale;

	// Anchor the respawn to the level's PlayerStart — NOT to wherever we happened to
	// spawn. (PIE's "spawn at camera location" can drop the hero mid-air; anchoring
	// there would respawn him into the sky forever.)
	SpawnLocation = GetActorLocation();
	SpawnRotation = GetActorRotation();
	if (const AActor* Start = UGameplayStatics::GetActorOfClass(GetWorld(), APlayerStart::StaticClass()))
	{
		SpawnLocation = Start->GetActorLocation() + FVector(0.f, 0.f, 20.f);
		SpawnRotation = FRotator(0.f, Start->GetActorRotation().Yaw, 0.f);
	}
	SafeGroundLocation = SpawnLocation;

	// Proof-of-possession + controls card (also instantly tells us if Play put the
	// player into a spectator pawn instead of the hero).
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(1, 10.f, FColor::Orange,
			TEXT("SPARK HERO READY  |  WASD run   SPACE jump (x2 = double)   SHIFT dash   CTRL fast-fall"));
	}

	// Visual pecking order: rigged skeletal hero > imported static hero > placeholder.
	if (bHasSkeletalModel)
	{
		BodyMesh->SetVisibility(false);
		SparkHead->SetVisibility(false);
		if (WalkAnim)
		{
			SkelBody->SetAnimation(WalkAnim);
			SkelBody->Stop();                 // standing frame as the v1 idle pose
		}
		// Spark-orange identity tint until the PBR-textured Meshy model lands
		// (this rig shipped untextured — the texture pass comes via the API).
		if (UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
				nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
		{
			UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
			MID->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.851f, 0.467f, 0.341f));
			for (int32 i = 0; i < SkelBody->GetNumMaterials(); ++i)
			{
				SkelBody->SetMaterial(i, MID);
			}
		}
		UE_LOG(LogTemp, Display, TEXT("SCB2 HERO: skeletal model active (%s anims), loc=%s"),
			(WalkAnim && RunAnim && JumpAnim) ? TEXT("all") : TEXT("partial"),
			*SkelBody->GetComponentLocation().ToString());
	}
	else if (bHasRealModel)
	{
		SparkHead->SetVisibility(false);      // the real model carries its own spark
		UE_LOG(LogTemp, Display, TEXT("SCB2 HERO: real model active, loc=%s"),
			*BodyMesh->GetComponentLocation().ToString());
	}

	// Placeholder tint (Anthropic palette). The engine sphere's default slot is the
	// grid material (no Color param), so base dynamic materials on BasicShapeMaterial.
	if (!bHasRealModel)
	{
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

	QuitAction = NewObject<UInputAction>(this, TEXT("IA_Quit"));
	QuitAction->ValueType = EInputActionValueType::Boolean;

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

	// Quit: Esc (the game window must always be escapable).
	MappingContext->MapKey(QuitAction, EKeys::Escape);
	MappingContext->MapKey(QuitAction, EKeys::Gamepad_Special_Right);
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
		EIC->BindAction(QuitAction, ETriggerEvent::Started, this, &ASparkHeroCharacter::HandleQuit);
	}
}

void ASparkHeroCharacter::HandleQuit()
{
	// In PIE this ends the play session; in the standalone game it closes the window.
	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		PC->ConsoleCommand(TEXT("quit"));
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
	PlaySfx(bAirJump ? TEXT("/Game/Art/Audio/sfx_doublejump.sfx_doublejump")
	                 : TEXT("/Game/Art/Audio/sfx_jump.sfx_jump"));
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
	if (ImpactSpeed > 350.f)
	{
		PlaySfx(TEXT("/Game/Art/Audio/sfx_land.sfx_land"));
		PlayShake(ImpactSpeed > 1400.f ? USparkBigLandShake::StaticClass()
		                               : USparkLandShake::StaticClass());
	}
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
	PlaySfx(TEXT("/Game/Art/Audio/sfx_dash.sfx_dash"));
	PlayShake(USparkDashShake::StaticClass());
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
// Respawn: heroes need solid ground — no endless void falls.
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::RespawnAtStart()
{
	if (bIsDashing) { EndDash(); }
	if (bFastFalling) { HandleFastFallReleased(); }

	GetCharacterMovement()->Velocity = FVector::ZeroVector;
	GetCharacterMovement()->SetMovementMode(MOVE_Falling);
	SetActorLocation(SafeGroundLocation + FVector(0.f, 0.f, 50.f), false, nullptr,
	                 ETeleportType::TeleportPhysics);
	SetActorRotation(SpawnRotation);
	if (Controller)
	{
		Controller->SetControlRotation(SpawnRotation);
	}
	AirJumpsRemaining = MaxAirJumps;
	AirDashesRemaining = MaxAirDashes;
	ApplySquash(JumpStretch);                 // a little "pop" back into existence
	PlaySfx(TEXT("/Game/Art/Audio/sfx_respawn.sfx_respawn"));
	OnHeroRespawned();
}

void ASparkHeroCharacter::FellOutOfWorld(const UDamageType& DmgType)
{
	// Engine kill-Z: respawn instead of being destroyed (the default would
	// delete the pawn and leave the camera floating in the void).
	RespawnAtStart();
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

	// Solid-ground guarantee: dropped below the world? Straight back to the start.
	if (GetActorLocation().Z < RespawnBelowZ)
	{
		RespawnAtStart();
	}

	// Track the last moment we stood on ground (coyote time reads this), and the
	// last solid spot we stood on (the respawn point — checkpointing-lite).
	if (Move->IsMovingOnGround())
	{
		LastGroundedTime = Now();
		bCoyoteConsumed = false;
		SafeGroundLocation = GetActorLocation();
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

	// Drive the rigged hero's clips from movement state.
	if (bHasSkeletalModel)
	{
		UpdateHeroAnimation();
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

// Single-node clip switching — the whole "AnimBP" in ~30 lines. States only change
// on transition so PlayAnimation never restarts a clip mid-loop.
void ASparkHeroCharacter::UpdateHeroAnimation()
{
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	const float GroundSpeed = static_cast<float>(Move->Velocity.Size2D());

	EHeroAnimState Desired;
	if (!Move->IsMovingOnGround())
	{
		Desired = EHeroAnimState::Jump;
	}
	else if (GroundSpeed > RunAnimSpeedThreshold)
	{
		Desired = EHeroAnimState::Run;
	}
	else if (GroundSpeed > WalkAnimMinSpeed)
	{
		Desired = EHeroAnimState::Walk;
	}
	else
	{
		Desired = EHeroAnimState::Idle;
	}

	if (Desired != AnimState)
	{
		AnimState = Desired;
		switch (AnimState)
		{
		case EHeroAnimState::Jump:
			if (JumpAnim) { SkelBody->PlayAnimation(JumpAnim, false); }
			break;
		case EHeroAnimState::Run:
			if (RunAnim) { SkelBody->PlayAnimation(RunAnim, true); }
			break;
		case EHeroAnimState::Walk:
			if (WalkAnim) { SkelBody->PlayAnimation(WalkAnim, true); }
			break;
		case EHeroAnimState::Idle:
		default:
			if (WalkAnim)
			{
				SkelBody->SetAnimation(WalkAnim);
				SkelBody->SetPosition(0.f);
				SkelBody->Stop();             // hold the standing frame until an idle clip lands
			}
			break;
		}
	}

	// Scale locomotion playback to actual speed so feet slide less.
	if (AnimState == EHeroAnimState::Walk)
	{
		SkelBody->SetPlayRate(FMath::Clamp(GroundSpeed / 280.f, 0.6f, 1.8f));
	}
	else if (AnimState == EHeroAnimState::Run)
	{
		SkelBody->SetPlayRate(FMath::Clamp(GroundSpeed / 600.f, 0.7f, 1.5f));
	}
}

void ASparkHeroCharacter::ApplySquash(float ZScale)
{
	// Conserve apparent volume: squashing down bulges XY, stretching up slims XY.
	const float XY = FMath::Sqrt(FMath::Max(0.05f, 1.f / FMath::Max(ZScale, 0.05f)));
	VisualScaleTarget = FVector(XY, XY, ZScale);
	VisualScaleCurrent = VisualScaleTarget; // snap to the pose, spring back to 1
}
