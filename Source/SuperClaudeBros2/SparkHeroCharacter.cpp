#include "SparkHeroCharacter.h"

#include "Animation/AnimSequence.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EmberMeterComponent.h"
#include "Engine/SkeletalMesh.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GlimmerEnemy.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/OverlapResult.h"
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

	// Crouch (CTRL on the ground; in the air the same button fast-falls).
	Move->GetNavAgentPropertiesRef().bCanCrouch = true;
	Move->SetCrouchedHalfHeight(CrouchHalfHeight);
	Move->MaxWalkSpeedCrouched = CrouchSpeed;

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
	// HeroSkelV2 + the _Anim names: the importer-built layout (mesh-ful clip FBXes
	// produce a junk mesh + a properly BOUND <name>_Anim sequence — heroine-proven).
	// The old /HeroSkel folder is CDO-locked and stays orphaned until a manual sweep.
	static ConstructorHelpers::FObjectFinder<USkeletalMesh> SkelModel(TEXT("/Game/Art/HeroSkelV4/SCB2Hero.SCB2Hero"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> IdleClip(TEXT("/Game/Art/HeroSkelV4/A_Hero_Idle_Anim.A_Hero_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> WalkClip(TEXT("/Game/Art/HeroSkelV4/A_Hero_Walk_Anim.A_Hero_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> RunClip(TEXT("/Game/Art/HeroSkelV4/A_Hero_Run_Anim.A_Hero_Run_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> JumpClip(TEXT("/Game/Art/HeroSkelV4/A_Hero_Jump2_Anim.A_Hero_Jump2_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> Strike1Clip(TEXT("/Game/Art/HeroSkelV4/A_Hero_Strike1_Anim.A_Hero_Strike1_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> Strike2Clip(TEXT("/Game/Art/HeroSkelV4/A_Hero_Strike2_Anim.A_Hero_Strike2_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HaymakerClip(TEXT("/Game/Art/HeroSkelV4/A_Hero_Haymaker_Anim.A_Hero_Haymaker_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HitReactClip(TEXT("/Game/Art/HeroSkelV4/A_Hero_HitReact_Anim.A_Hero_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> RelightClip(TEXT("/Game/Art/HeroSkelV4/A_Hero_Relight_Anim.A_Hero_Relight_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> CrouchClip(TEXT("/Game/Art/HeroSkelV4/A_Hero_CrouchWalk_Anim.A_Hero_CrouchWalk_Anim"));

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
	IdleAnim = IdleClip.Succeeded() ? IdleClip.Object : nullptr;
	WalkAnim = WalkClip.Succeeded() ? WalkClip.Object : nullptr;
	RunAnim = RunClip.Succeeded() ? RunClip.Object : nullptr;
	JumpAnim = JumpClip.Succeeded() ? JumpClip.Object : nullptr;
	Strike1Anim = Strike1Clip.Succeeded() ? Strike1Clip.Object : nullptr;
	Strike2Anim = Strike2Clip.Succeeded() ? Strike2Clip.Object : nullptr;
	HaymakerAnim = HaymakerClip.Succeeded() ? HaymakerClip.Object : nullptr;
	HitReactAnim = HitReactClip.Succeeded() ? HitReactClip.Object : nullptr;
	RelightAnim = RelightClip.Succeeded() ? RelightClip.Object : nullptr;
	CrouchAnim = CrouchClip.Succeeded() ? CrouchClip.Object : nullptr;

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

	// --- The Ember Meter: health as a flame above the dome (spec §2) ---
	// Placeholder flame = a small sphere the meter scales; the point light is the
	// part that actually sells it (and dims the world as the hero gutters).
	EmberMeter = CreateDefaultSubobject<UEmberMeterComponent>(TEXT("EmberMeter"));

	EmberFlame = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("EmberFlame"));
	EmberFlame->SetupAttachment(VisualRoot);   // squashes with the body — flames bounce too
	EmberFlame->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMesh.Succeeded())
	{
		EmberFlame->SetStaticMesh(SphereMesh.Object);
	}
	EmberFlame->SetRelativeLocation(FVector(0.f, 0.f, 74.f));  // re-seated onto the head bone at BeginPlay
	EmberFlame->SetRelativeScale3D(FVector(0.08f, 0.08f, 0.15f));
	EmberFlame->SetCastShadow(false);

	// Adam's playtest verdict: "too much orange glow." The inverse-square fix is
	// distance + source size, not wattage alone — soft-sourced, dim, tight.
	// The glow rides the flame (which rides the head bone) so light follows pose.
	EmberGlow = CreateDefaultSubobject<UPointLightComponent>(TEXT("EmberGlow"));
	EmberGlow->SetupAttachment(EmberFlame);
	EmberGlow->SetRelativeLocation(FVector(0.f, 0.f, 0.f));
	EmberGlow->SetIntensity(40.f);                             // candle, final answer
	EmberGlow->SetAttenuationRadius(120.f);
	EmberGlow->SetSourceRadius(10.f);                          // soft area light, no hot pinprick
	EmberGlow->SetLightColor(FColor(255, 150, 60));            // kept-fire amber (Color Law)
	EmberGlow->SetCastShadows(false);                          // small, warm, cheap

	// --- Power pulse VFX: a flat amber shockwave disc + a flash light ---
	PulseDisc = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PulseDisc"));
	PulseDisc->SetupAttachment(RootComponent);
	PulseDisc->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMesh.Succeeded())
	{
		PulseDisc->SetStaticMesh(SphereMesh.Object);
	}
	PulseDisc->SetRelativeScale3D(FVector(0.01f, 0.01f, 0.04f));
	PulseDisc->SetCastShadow(false);
	PulseDisc->SetVisibility(false);

	PulseLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("PulseLight"));
	PulseLight->SetupAttachment(RootComponent);
	PulseLight->SetIntensity(0.f);
	PulseLight->SetAttenuationRadius(600.f);
	PulseLight->SetLightColor(FColor(255, 170, 70));
	PulseLight->SetCastShadows(false);
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

	// L9 amplification: the spark learns a second air dash.
	if (HasPowerLevel(9))
	{
		MaxAirDashes = FMath::Max(MaxAirDashes, 2);
	}

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
		GEngine->AddOnScreenDebugMessage(1, 12.f, FColor::Orange,
			FString::Printf(TEXT("SPARK HERO L%d  |  LMB power(hold=WAVE)  RMB strike(x3/hold=CHARGED)  Q guard  SPACE jump x2  SHIFT dash  C/CTRL crouch  air+push wall=CLIMB  WHEEL zoom"), PowerLevel));
	}

	// Visual pecking order: rigged skeletal hero > imported static hero > placeholder.
	if (bHasSkeletalModel)
	{
		BodyMesh->SetVisibility(false);
		SparkHead->SetVisibility(false);
		if (bEnableClipPlayback && WalkAnim)
		{
			SkelBody->SetAnimation(WalkAnim);
			SkelBody->Stop();                 // standing frame as the v1 idle pose
		}
		// The mesh carries M_HeroPBR (retextured orange/white/black 4K maps) —
		// assigned on the asset by import_hero_textures.py; nothing to override here.
		UE_LOG(LogTemp, Display, TEXT("SCB2 HERO: skeletal model active (%s anims), loc=%s"),
			(WalkAnim && RunAnim && JumpAnim) ? TEXT("all") : TEXT("partial"),
			*SkelBody->GetComponentLocation().ToString());

		// The ember flame rides the DOME, not the capsule: a fixed offset left an
		// egg floating over animated poses (Adam's playtest). Find the head bone
		// and re-seat the flame on it; the glow is the flame's child and follows.
		if (EmberFlame)
		{
			FName HeadBone = NAME_None;
			for (int32 i = 0; i < SkelBody->GetNumBones(); ++i)
			{
				const FName Bone = SkelBody->GetBoneName(i);
				if (Bone.ToString().Contains(TEXT("head"), ESearchCase::IgnoreCase))
				{
					HeadBone = Bone;
					break;
				}
			}
			if (HeadBone != NAME_None)
			{
				EmberFlame->AttachToComponent(SkelBody,
					FAttachmentTransformRules::KeepWorldTransform, HeadBone);
				UE_LOG(LogTemp, Display, TEXT("SCB2 HERO: ember flame seated on bone '%s'"),
					*HeadBone.ToString());
			}
			EmberFlame->SetVisibility(bShowEmberFlame);
		}
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

	// The Ember Meter takes the flame: amber tint on the placeholder sphere, then
	// hand both visuals to the component — it animates them from here on.
	if (EmberFlame)
	{
		if (UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
				nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
		{
			UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
			MID->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.85f, 0.42f, 0.10f));
			EmberFlame->SetMaterial(0, MID);
		}
	}
	if (EmberMeter)
	{
		EmberMeter->RegisterFlameVisuals(EmberFlame, EmberGlow);
		EmberMeter->OnFlameOut.AddDynamic(this, &ASparkHeroCharacter::HandleFlameOut);
	}

	// Amber tint for the power shockwave disc.
	if (PulseDisc)
	{
		if (UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
				nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
		{
			UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
			MID->SetVectorParameterValue(TEXT("Color"), FLinearColor(1.0f, 0.62f, 0.18f));
			PulseDisc->SetMaterial(0, MID);
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

	ZoomAction = NewObject<UInputAction>(this, TEXT("IA_Zoom"));
	ZoomAction->ValueType = EInputActionValueType::Axis1D;

	JumpAction = NewObject<UInputAction>(this, TEXT("IA_Jump"));
	JumpAction->ValueType = EInputActionValueType::Boolean;

	DashAction = NewObject<UInputAction>(this, TEXT("IA_Dash"));
	DashAction->ValueType = EInputActionValueType::Boolean;

	StrikeAction = NewObject<UInputAction>(this, TEXT("IA_Strike"));
	StrikeAction->ValueType = EInputActionValueType::Boolean;

	PowerAction = NewObject<UInputAction>(this, TEXT("IA_Power"));
	PowerAction->ValueType = EInputActionValueType::Boolean;

	GuardAction = NewObject<UInputAction>(this, TEXT("IA_Guard"));
	GuardAction->ValueType = EInputActionValueType::Boolean;

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

	// Zoom: mouse wheel (up = closer) + d-pad up/down.
	MappingContext->MapKey(ZoomAction, EKeys::MouseWheelAxis);
	MappingContext->MapKey(ZoomAction, EKeys::Gamepad_DPad_Up);
	AddNegate(MappingContext->MapKey(ZoomAction, EKeys::Gamepad_DPad_Down));

	// Jump / dash / fast-fall.
	MappingContext->MapKey(JumpAction, EKeys::SpaceBar);
	MappingContext->MapKey(JumpAction, EKeys::Gamepad_FaceButton_Bottom);
	MappingContext->MapKey(DashAction, EKeys::LeftShift);
	MappingContext->MapKey(DashAction, EKeys::Gamepad_FaceButton_Left);

	// Adam's layout: LEFT click = SUPERPOWERS (tap = Prism Burst, hold = Beacon
	// Wave); RIGHT click = strikes (tap = combo, hold = Charged Haymaker).
	MappingContext->MapKey(PowerAction, EKeys::LeftMouseButton);
	MappingContext->MapKey(PowerAction, EKeys::Gamepad_RightTrigger);

	MappingContext->MapKey(StrikeAction, EKeys::RightMouseButton);
	MappingContext->MapKey(StrikeAction, EKeys::Gamepad_FaceButton_Right);

	// Ember Guard: the flame armors itself.
	MappingContext->MapKey(GuardAction, EKeys::Q);
	MappingContext->MapKey(GuardAction, EKeys::Gamepad_LeftShoulder);
	MappingContext->MapKey(FastFallAction, EKeys::LeftControl);
	MappingContext->MapKey(FastFallAction, EKeys::C);   // crouch's second home
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
		EIC->BindAction(ZoomAction, ETriggerEvent::Triggered, this, &ASparkHeroCharacter::HandleZoom);
		EIC->BindAction(JumpAction, ETriggerEvent::Started, this, &ASparkHeroCharacter::HandleJumpPressed);
		EIC->BindAction(JumpAction, ETriggerEvent::Completed, this, &ASparkHeroCharacter::HandleJumpReleased);
		EIC->BindAction(DashAction, ETriggerEvent::Started, this, &ASparkHeroCharacter::HandleDashPressed);
		EIC->BindAction(StrikeAction, ETriggerEvent::Started, this, &ASparkHeroCharacter::HandleStrikePressed);
		EIC->BindAction(StrikeAction, ETriggerEvent::Completed, this, &ASparkHeroCharacter::HandleStrikeReleased);
		EIC->BindAction(PowerAction, ETriggerEvent::Started, this, &ASparkHeroCharacter::HandlePowerPressed);
		EIC->BindAction(PowerAction, ETriggerEvent::Completed, this, &ASparkHeroCharacter::HandlePowerReleased);
		EIC->BindAction(GuardAction, ETriggerEvent::Started, this, &ASparkHeroCharacter::HandleGuardPressed);
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

	// Climbing remaps the stick: forward/back = up/down the wall, sideways = strafe.
	if (bClimbing)
	{
		const FVector AlongWall = FVector::CrossProduct(FVector::UpVector, ClimbWallNormal);
		AddMovementInput(FVector::UpVector, Axis.Y);
		AddMovementInput(AlongWall, Axis.X);
		AddMovementInput(-ClimbWallNormal, 0.3f);   // hug the surface
		return;
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

void ASparkHeroCharacter::HandleZoom(const FInputActionValue& Value)
{
	// Wheel up = closer. Exponential steps so every notch feels equal; the
	// multiplier rides on top of the context camera (Tick applies it).
	const float Notches = Value.Get<float>();
	if (FMath::IsNearlyZero(Notches)) { return; }
	ZoomMultiplier = FMath::Clamp(
		ZoomMultiplier * FMath::Pow(ZoomStepPerNotch, -Notches),
		ZoomMinMultiplier, ZoomMaxMultiplier);
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
	// Climbing: jump = the WALL LEAP — kick away and up, fresh air resources.
	if (bClimbing)
	{
		const FVector Away = ClimbWallNormal;
		StopClimb();
		LaunchCharacter(Away * WallLeapAway + FVector(0.f, 0.f, WallLeapUp), true, true);
		AirJumpsRemaining = MaxAirJumps;
		AirDashesRemaining = MaxAirDashes;
		ApplySquash(JumpStretch);
		PlaySfx(TEXT("/Game/Art/Audio/sfx_jump.sfx_jump"));
		OnHeroJumped(false);
		return;
	}

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
	if (bClimbing) { return; }   // jump leaves the wall, dash doesn't
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
// The Spark Combo: lash, lash, HAYMAKER. (SCB2_POWERS_CODEX.md §1 — Adam's
// June 11 lock.) Strikes are movement: each beat lunges the hero forward and
// sweeps a sphere ahead. No clips yet — lunge + squash + shake sell it, the
// dash precedent. Stomp remains the sacred finisher; fists open doors.
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::HandleStrikePressed()
{
	if (bClimbing) { return; }                        // both hands are busy
	if (bIsDashing) { return; }                       // the dash owns its moment
	if (Now() < ComboCooldownUntil) { return; }       // post-haymaker breather
	if (bStriking) { bStrikeQueued = true; return; }  // chain the next beat

	// L3+: holding the button charges the haymaker; the strike fires on release.
	bChargingStrike = true;
	StrikeChargeStart = Now();
}

void ASparkHeroCharacter::HandleStrikeReleased()
{
	if (!bChargingStrike) { return; }
	bChargingStrike = false;

	const float Held = Now() - StrikeChargeStart;
	if (Held >= StrikeChargeTime && HasPowerLevel(3) && !bStriking)
	{
		DoChargedStrike();
		return;
	}
	if (bStriking || bIsDashing || Now() < ComboCooldownUntil) { return; }
	if ((Now() - LastStrikeEndTime) > StrikeComboWindow)
	{
		ComboBeat = 0;                                // too slow — the string resets
	}
	DoStrike();
}

void ASparkHeroCharacter::DoChargedStrike()
{
	// L3 — the CHARGED HAYMAKER: the fist arrives glowing. Bigger lunge, bigger
	// sweep; flips Rolys and staggers Champions once they exist (Codex §2).
	bStriking = true;
	bChargedStrike = true;
	ComboBeat = 2;                                    // counts as the heavy beat

	FVector Dir = GetActorForwardVector();
	Dir.Z = 0.f;
	LaunchCharacter(Dir.GetSafeNormal() * ChargedLunge, true, false);

	ApplySquash(1.16f);
	PlaySfx(TEXT("/Game/Art/Audio/sfx_dash.sfx_dash"));
	if (EmberMeter) { EmberMeter->FlashGlow(0.35f, 4.f); }
	FirePulse(220.f, 0.35f, 2500.f);
	OnHeroChargedStrike();
	PlayActionClip(HaymakerAnim, 0.55f);

	GetWorldTimerManager().SetTimer(StrikeHitTimerHandle, this, &ASparkHeroCharacter::StrikeHitCheck,
	                                0.22f, false);
	GetWorldTimerManager().SetTimer(StrikeTimerHandle, this, &ASparkHeroCharacter::EndStrike,
	                                0.5f, false);
}

void ASparkHeroCharacter::DoStrike()
{
	bStriking = true;
	const bool bHeavy = (ComboBeat >= 2);
	const float Duration = bHeavy ? StrikeHeavyDuration : StrikeLightDuration;
	const float Lunge = bHeavy ? StrikeHeavyLunge : StrikeLightLunge;

	// The strike steps INTO the target — facing-direction lunge, Z untouched.
	FVector Dir = GetActorForwardVector();
	Dir.Z = 0.f;
	Dir = Dir.GetSafeNormal();
	LaunchCharacter(Dir * Lunge, true, false);

	ApplySquash(bHeavy ? 1.10f : 1.05f);              // a forward-leaning stretch
	PlaySfx(TEXT("/Game/Art/Audio/sfx_dash.sfx_dash"));
	OnHeroStrike(ComboBeat);

	// The body acts the beat: clip fitted to the beat window (plus a little
	// follow-through into recovery) — fighting-game speed from library clips.
	UAnimSequence* StrikeClip = bHeavy ? HaymakerAnim : (ComboBeat == 1 ? Strike2Anim : Strike1Anim);
	PlayActionClip(StrikeClip, Duration * 1.35f);

	GetWorldTimerManager().SetTimer(StrikeHitTimerHandle, this, &ASparkHeroCharacter::StrikeHitCheck,
	                                Duration * 0.45f, false);
	GetWorldTimerManager().SetTimer(StrikeTimerHandle, this, &ASparkHeroCharacter::EndStrike,
	                                Duration, false);
}

void ASparkHeroCharacter::StrikeHitCheck()
{
	UWorld* World = GetWorld();
	if (World == nullptr) { return; }

	const bool bHeavy = (ComboBeat >= 2);
	const FVector Center = GetActorLocation() + GetActorForwardVector() * StrikeRange;
	const float Radius = StrikeRadius + (bHeavy ? 15.f : 0.f)
	                   + (bChargedStrike ? ChargedRadiusBonus : 0.f);

	TArray<FOverlapResult> Hits;
	FCollisionQueryParams Params(TEXT("SparkStrike"), false, this);
	World->OverlapMultiByChannel(Hits, Center, FQuat::Identity, ECC_Pawn,
	                             FCollisionShape::MakeSphere(Radius), Params);

	bool bConnected = false;
	for (const FOverlapResult& Hit : Hits)
	{
		// v1: Motes die to any beat (mass-class ladder: Spark >> Mote). Heavier
		// classes get their CLASH/CLANG rows when the duel framework lands (P1).
		if (AGlimmerEnemy* Glimmer = Cast<AGlimmerEnemy>(Hit.GetActor()))
		{
			Glimmer->TakeStrike();
			OnHeroStrikeHit(Glimmer, ComboBeat);
			bConnected = true;
		}
	}
	if (bConnected)
	{
		PlaySfx(TEXT("/Game/Art/Audio/sfx_land.sfx_land"));
		PlayShake(bHeavy ? USparkBigLandShake::StaticClass() : USparkLandShake::StaticClass());
	}
}

void ASparkHeroCharacter::EndStrike()
{
	if (!bStriking) { return; }
	bStriking = false;
	bChargedStrike = false;
	LastStrikeEndTime = Now();
	GetWorldTimerManager().ClearTimer(StrikeTimerHandle);

	const bool bWasHeavy = (ComboBeat >= 2);
	if (bWasHeavy)
	{
		ComboBeat = 0;
		bStrikeQueued = false;
		ComboCooldownUntil = Now() + StrikeComboCooldown;
		EndActionClip();                              // string over — body back to locomotion
	}
	else
	{
		ComboBeat++;
		if (bStrikeQueued)
		{
			bStrikeQueued = false;
			DoStrike();                               // the chained beat fires immediately
		}
		else
		{
			EndActionClip();                          // string broken — resume locomotion
		}
	}
}

// ---------------------------------------------------------------------------
// Climb: the squid grips the wall. Press toward a surface while airborne to
// cling; stick = up/down/strafe; jump = the wall leap. (GRIPPABLE-material-only
// once the W3 tags land — bClimbAnywhere is the interim law.)
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::TryStartClimb()
{
	if (LastWorldMoveInput.IsNearlyZero()) { return; }

	FHitResult WallHit;
	FCollisionQueryParams Params(TEXT("ClimbGrab"), false, this);
	const FVector Start = GetActorLocation();
	const float Reach = GetCapsuleComponent()->GetScaledCapsuleRadius() + ClimbCheckDistance;
	if (!GetWorld()->LineTraceSingleByChannel(WallHit, Start,
			Start + LastWorldMoveInput * Reach, ECC_Visibility, Params))
	{
		return;
	}
	if (FMath::Abs(WallHit.ImpactNormal.Z) > 0.4f) { return; }       // walls only, not ramps
	if (FVector::DotProduct(LastWorldMoveInput, WallHit.ImpactNormal) > -0.5f) { return; }

	bClimbing = true;
	ClimbWallNormal = WallHit.ImpactNormal;

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->SetMovementMode(MOVE_Flying);
	Move->MaxFlySpeed = ClimbSpeed;
	Move->BrakingDecelerationFlying = 2048.f;
	Move->GravityScale = 0.f;
	Move->Velocity = FVector::ZeroVector;
	SetActorRotation(FRotationMatrix::MakeFromX(-ClimbWallNormal).Rotator());
}

void ASparkHeroCharacter::StopClimb()
{
	if (!bClimbing) { return; }
	bClimbing = false;
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->SetMovementMode(MOVE_Falling);
	Move->GravityScale = bFastFalling ? FastFallGravityScale : BaseGravityScale;
	AnimState = EHeroAnimState::None;   // re-pick locomotion
}

// ---------------------------------------------------------------------------
// THE SPARK SURGE KIT (Powers Codex §2): Adam's directive — build the FULL hero
// now; world deployment stages PowerLevel per Great-Lantern relight.
// ---------------------------------------------------------------------------
bool ASparkHeroCharacter::IsAuraActive() const
{
	return HasPowerLevel(2) && EmberMeter && !EmberMeter->IsFlameOut();
}

// The asset-free power flash: a ground disc that races outward + a light spike.
// Tick animates it (scale and fade) until PulseDuration runs out.
void ASparkHeroCharacter::FirePulse(float Radius, float Duration, float LightIntensity)
{
	PulseStartTime = Now();
	PulseDuration = Duration;
	PulseTargetRadius = Radius;
	if (PulseDisc)
	{
		const float FootZ = -GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 4.f;
		PulseDisc->SetRelativeLocation(FVector(0.f, 0.f, FootZ));
		PulseDisc->SetVisibility(true);
	}
	if (PulseLight)
	{
		PulseLight->SetAttenuationRadius(Radius * 1.3f);
		PulseLight->SetIntensity(LightIntensity);
	}
}

void ASparkHeroCharacter::HandlePowerPressed()
{
	if (!HasPowerLevel(4)) { return; }   // the burst is the kit's entry power
	bChargingPower = true;
	PowerChargeStart = Now();
}

void ASparkHeroCharacter::HandlePowerReleased()
{
	if (!bChargingPower) { return; }
	bChargingPower = false;

	const float Held = Now() - PowerChargeStart;
	if (Held >= WaveChargeTime && HasPowerLevel(6))
	{
		DoBeaconWave();
	}
	else
	{
		DoPrismBurst();
	}
}

void ASparkHeroCharacter::DoPrismBurst()
{
	// L4 — PRISM BURST: a ring of light that staggers Motes (and lures moths,
	// once moths exist). Dazzles, never wounds — the kit keeps the kindness.
	if (Now() < BurstReadyTime) { return; }
	BurstReadyTime = Now() + BurstCooldown;

	const float Radius = BurstRadius * (HasPowerLevel(8) ? 1.3f : 1.f);
	FirePulse(Radius, 0.45f, 5000.f);
	if (EmberMeter) { EmberMeter->FlashGlow(0.4f, 8.f); }
	PlayShake(USparkLandShake::StaticClass());
	PlaySfx(TEXT("/Game/Art/Audio/sfx_doublejump.sfx_doublejump"));
	OnHeroPrismBurst(Radius);

	TArray<FOverlapResult> Hits;
	FCollisionQueryParams Params(TEXT("PrismBurst"), false, this);
	GetWorld()->OverlapMultiByChannel(Hits, GetActorLocation(), FQuat::Identity, ECC_Pawn,
	                                  FCollisionShape::MakeSphere(Radius), Params);
	for (const FOverlapResult& Hit : Hits)
	{
		if (AGlimmerEnemy* Glimmer = Cast<AGlimmerEnemy>(Hit.GetActor()))
		{
			Glimmer->TakeStagger(BurstStagger);
		}
	}
}

void ASparkHeroCharacter::DoBeaconWave()
{
	// L6 — BEACON WAVE: the big pulse. Staggers wide today; when the lantern
	// light-state system lands (M0.2), this also relights every lamp in radius —
	// the W5 territory mechanic in the hero's own hands.
	if (Now() < WaveReadyTime) { return; }
	WaveReadyTime = Now() + WaveCooldown;

	FirePulse(WaveRadius, 0.7f, 12000.f);
	if (EmberMeter) { EmberMeter->FlashGlow(0.8f, 16.f); }
	PlayShake(USparkBigLandShake::StaticClass());
	PlaySfx(TEXT("/Game/Art/Audio/sfx_land.sfx_land"));
	OnHeroBeaconWave(WaveRadius);

	TArray<FOverlapResult> Hits;
	FCollisionQueryParams Params(TEXT("BeaconWave"), false, this);
	GetWorld()->OverlapMultiByChannel(Hits, GetActorLocation(), FQuat::Identity, ECC_Pawn,
	                                  FCollisionShape::MakeSphere(WaveRadius), Params);
	for (const FOverlapResult& Hit : Hits)
	{
		if (AGlimmerEnemy* Glimmer = Cast<AGlimmerEnemy>(Hit.GetActor()))
		{
			Glimmer->TakeStagger(BurstStagger * 1.5f);
		}
	}
	// TODO(M0.2): ILightResponsive sweep — relight every lantern in WaveRadius.
}

void ASparkHeroCharacter::HandleGuardPressed()
{
	// L5 — EMBER GUARD: the flame armors itself (extended grace; the white-hot
	// flare is the telegraph). L9 holds it a second longer.
	if (!HasPowerLevel(5) || !EmberMeter) { return; }
	if (Now() < GuardReadyTime) { return; }
	GuardReadyTime = Now() + GuardCooldown;

	EmberMeter->ActivateGuard(HasPowerLevel(9) ? GuardDuration + 1.f : GuardDuration);
	EmberMeter->FlashGlow(0.5f, 6.f);
	FirePulse(160.f, 0.4f, 3000.f);
	OnHeroEmberGuard();
}

// ---------------------------------------------------------------------------
// Action-override animation layer: one-shot clips take the body, the locomotion
// state machine waits, then resumes through the None sentinel.
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::PlayActionClip(UAnimSequence* Clip, float FitDuration)
{
	if (!bEnableClipPlayback) { return; } // TEMP: juice carries strikes until then
	if (!bHasSkeletalModel || !Clip || !SkelBody) { return; }
	bActionAnimActive = true;
	SkelBody->PlayAnimation(Clip, false);
	const float Rate = Clip->GetPlayLength() / FMath::Max(FitDuration, 0.05f);
	SkelBody->SetPlayRate(FMath::Clamp(Rate, 0.5f, 5.f));
}

void ASparkHeroCharacter::EndActionClip()
{
	if (!bActionAnimActive) { return; }
	bActionAnimActive = false;
	if (SkelBody) { SkelBody->SetPlayRate(1.f); }
	AnimState = EHeroAnimState::None;                 // force a fresh locomotion pick
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

// ---------------------------------------------------------------------------
// The Ember Meter: contact costs fire (outside grace) — and a dead flame is
// relit at the respawn point. Lumen keeps your continue lit.
// ---------------------------------------------------------------------------
void ASparkHeroCharacter::TakeEmberHit(float Embers)
{
	if (!EmberMeter) { return; }
	if (EmberMeter->ApplyEmberDamage(Embers))
	{
		PlayShake(USparkLandShake::StaticClass());
		OnHeroEmberHit(EmberMeter->GetFraction());

		// The body flinches (interrupting any strike mid-swing — getting hit hurts).
		if (HitReactAnim)
		{
			PlayActionClip(HitReactAnim, 0.5f);
			GetWorldTimerManager().SetTimer(HitReactTimerHandle, this,
			                                &ASparkHeroCharacter::EndActionClip, 0.5f, false);
		}
	}
}

void ASparkHeroCharacter::HandleFlameOut()
{
	// Today: instant relight at the safe spot. The ~3 s lantern ceremony (respawn
	// at the last LIT lantern, spec §2) arrives with the checkpoint system, M0.3.
	OnHeroFlameOut();
	RespawnAtStart();
	if (EmberMeter) { EmberMeter->RefillFull(); }
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
	// One button, two verbs: CTRL/C crouches on the ground, fast-falls in the air.
	if (bClimbing) { StopClimb(); return; }   // let go of the wall
	if (GetCharacterMovement()->IsMovingOnGround())
	{
		if (!bIsDashing)
		{
			Crouch();
			UE_LOG(LogTemp, Display, TEXT("SCB2 HERO: crouch requested (CanCrouch=%d, bIsCrouched=%d)"),
				CanCrouch() ? 1 : 0, bIsCrouched ? 1 : 0);
		}
		return;
	}
	if (bIsDashing) { return; }
	bFastFalling = true;
	GetCharacterMovement()->GravityScale = FastFallGravityScale;
}

void ASparkHeroCharacter::HandleFastFallReleased()
{
	UnCrouch();
	bFastFalling = false;
	if (!bIsDashing)
	{
		GetCharacterMovement()->GravityScale = BaseGravityScale;
	}
}

// Crouch shrinks the capsule and drops its center; shift the visuals so the
// feet stay planted. ABSOLUTE positions, never deltas — the additive version
// accumulated across crouch cycles and sank the hero permanently (Adam's bug).
void ASparkHeroCharacter::OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust)
{
	Super::OnStartCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust);
	if (VisualRoot)
	{
		VisualRoot->SetRelativeLocation(FVector(0.f, 0.f, ScaledHalfHeightAdjust));
	}
}

void ASparkHeroCharacter::OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust)
{
	Super::OnEndCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust);
	if (VisualRoot)
	{
		VisualRoot->SetRelativeLocation(FVector::ZeroVector);   // the one true rest pose
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
	// Air resources restore here too — landing isn't the only way to be grounded
	// (walking off a ledge used to silently eat the double jump: Adam's bug report).
	if (Move->IsMovingOnGround())
	{
		LastGroundedTime = Now();
		bCoyoteConsumed = false;
		AirJumpsRemaining = MaxAirJumps;
		AirDashesRemaining = MaxAirDashes;
		SafeGroundLocation = GetActorLocation();
	}
	PrevTickVelZ = Move->Velocity.Z;

	// Climb maintenance + entry: pressing toward a nearby wall while airborne
	// grabs it (the squid speaks to surfaces; GRIPPABLE-only once W3 tags land).
	if (bClimbing)
	{
		FHitResult WallHit;
		FCollisionQueryParams ClimbParams(TEXT("ClimbHold"), false, this);
		const FVector Start = GetActorLocation();
		const float Reach = GetCapsuleComponent()->GetScaledCapsuleRadius() + ClimbCheckDistance + 10.f;
		const bool bWallStillThere = GetWorld()->LineTraceSingleByChannel(
			WallHit, Start, Start - ClimbWallNormal * Reach, ECC_Visibility, ClimbParams);
		if (!bWallStillThere || Move->IsMovingOnGround())
		{
			StopClimb();
		}
		else
		{
			ClimbWallNormal = WallHit.ImpactNormal;
		}
	}
	else if (!Move->IsMovingOnGround() && !bIsDashing && bClimbAnywhere)
	{
		TryStartClimb();
	}

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
		// Player zoom rides on top of the context camera (wheel / d-pad).
		TargetLen = FMath::Clamp(TargetLen * ZoomMultiplier, 60.f, 3000.f);
		SpringArm->TargetArmLength = FMath::FInterpTo(SpringArm->TargetArmLength, TargetLen,
		                                              DeltaSeconds, 4.f);
	}

	// Drive the rigged hero's clips from movement state.
	if (bHasSkeletalModel)
	{
		UpdateHeroAnimation();
	}

	// Power pulse animation: the disc races outward and the flash decays.
	if (Now() < PulseStartTime + PulseDuration)
	{
		const float T = (Now() - PulseStartTime) / PulseDuration;          // 0..1
		const float Eased = 1.f - FMath::Square(1.f - T);                  // fast out
		if (PulseDisc)
		{
			const float S = FMath::Max(0.02f, (PulseTargetRadius / 50.f) * Eased);
			PulseDisc->SetRelativeScale3D(FVector(S, S, 0.04f));
		}
		if (PulseLight)
		{
			PulseLight->SetIntensity(PulseLight->Intensity * (1.f - DeltaSeconds * 3.f));
		}
	}
	else if (PulseDisc && PulseDisc->IsVisible())
	{
		PulseDisc->SetVisibility(false);
		if (PulseLight) { PulseLight->SetIntensity(0.f); }
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
	if (!bEnableClipPlayback) { return; } // TEMP: ref-pose until the converter fix
	if (bActionAnimActive) { return; }   // a one-shot (strike/flinch) owns the body

	const UCharacterMovementComponent* Move = GetCharacterMovement();
	const float GroundSpeed = static_cast<float>(Move->Velocity.Size2D());

	EHeroAnimState Desired;
	if (bClimbing)
	{
		Desired = EHeroAnimState::Climb;
	}
	else if (!Move->IsMovingOnGround())
	{
		Desired = EHeroAnimState::Jump;
	}
	else if (bIsCrouched)
	{
		Desired = EHeroAnimState::Crouch;
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
			if (JumpAnim)
			{
				// Skip the routine's lead-in: start at the leap, play it fitted.
				SkelBody->SetAnimation(JumpAnim);
				SkelBody->SetPlayRate(JumpClipRate);
				SkelBody->SetPosition(JumpAnim->GetPlayLength() * JumpClipStartFraction, false);
				SkelBody->Play(false);
			}
			break;
		case EHeroAnimState::Crouch:
			if (CrouchAnim)
			{
				SkelBody->PlayAnimation(CrouchAnim, true);   // cautious sway, looped
			}
			break;
		case EHeroAnimState::Climb:
			if (CrouchAnim)
			{
				SkelBody->PlayAnimation(CrouchAnim, true);   // crawl reads as climb
				SkelBody->SetPlayRate(0.8f);                 // (proper climb clip queued)
			}
			break;
		case EHeroAnimState::Run:
			if (RunAnim) { SkelBody->PlayAnimation(RunAnim, true); }
			break;
		case EHeroAnimState::Walk:
			if (WalkAnim) { SkelBody->PlayAnimation(WalkAnim, true); }
			break;
		case EHeroAnimState::Idle:
		default:
			if (IdleAnim)
			{
				SkelBody->PlayAnimation(IdleAnim, true);
				SkelBody->SetPlayRate(1.f);
			}
			else if (WalkAnim)
			{
				SkelBody->SetAnimation(WalkAnim);
				SkelBody->SetPosition(0.f);
				SkelBody->Stop();             // fallback until an idle clip lands
			}
			break;
		}
	}

	// Scale locomotion playback to actual speed so feet slide less.
	if (AnimState == EHeroAnimState::Crouch)
	{
		SkelBody->SetPlayRate(FMath::Clamp(GroundSpeed / 220.f, 0.35f, 1.4f));
	}
	else if (AnimState == EHeroAnimState::Walk)
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
