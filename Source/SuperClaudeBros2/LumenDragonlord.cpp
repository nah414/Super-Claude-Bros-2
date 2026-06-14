// The Lumen Dragonlord — the final boss who only ever helps. The duel framework
// is inherited; what lives here is a lantern, a shove toward safety, and a
// sanctuary that gives your light back.

#include "LumenDragonlord.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EmberMeterComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "SparkHeroCharacter.h"
#include "SparkImpactBurst.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	const FLinearColor LumenAmber(1.5f, 1.0f, 0.42f);   // it was always amber
}

ALumenDragonlord::ALumenDragonlord()
{
	GetCapsuleComponent()->SetCapsuleSize(72.f, 118.f);   // the grandest body in the game
	RivalDisplayName = TEXT("LUMEN THE DRAGONLORD");

	ApproachSpeed = 540.f;   // regal but able to close (was 480, far under the hero)
	TurnRate = 6.f;          // RESPONSE: track a strafing player (was 4 — couldn't face you)
	IntroSeconds = 1.6f;     // snappier first contact (was 2.0)
	ApproachAnimRate = 0.9f;
	TelegraphPulseHz = 12.f;
	TelegraphPulseIntensity = 7000.f;
	PhaseRoarSeconds = 1.4f;
	FlinchSeconds = 0.5f;
	StaggerSeconds = 2.4f;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;

	HitBurstColor = FLinearColor(3.f, 2.1f, 0.9f);
	HitBurstScale = 1.4f;
	HitBurstLight = 5400.f;
	DefeatBurstColor = FLinearColor(2.6f, 1.9f, 0.9f);
	DefeatBurstScale = 2.5f;
	DefeatBurstLight = 8200.f;
	if (TelegraphLight) { TelegraphLight->SetLightColor(LumenAmber); }

	ContactProfile.MassClass = EMassClass::Mythic;
	ContactProfile.bStompImmune = true;
	ContactProfile.bDashImmune = true;
	ContactProfile.ContactDamageEmbers = 0.f;   // even his bulk does not harm

	// THE LANTERN — the heart of the whole game, burning in his chest.
	LanternLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("LanternLight"));
	LanternLight->SetupAttachment(VisualRoot);
	LanternLight->SetRelativeLocation(FVector(35.f, 0.f, 45.f));
	// A warm chest GLOW, not a floodlight — point-blank surfaces saturate at any
	// wattage (the ember-meter lesson); keep it candle-soft.
	LanternLight->SetAttenuationRadius(280.f);
	LanternLight->SetIntensity(280.f);
	LanternLight->SetLightColor(LumenAmber);
	LanternLight->SetCastShadows(false);

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/DragonSkelV1/SCB2Dragon.SCB2Dragon"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/DragonSkelV1/A_Dragon_Idle_Anim.A_Dragon_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/DragonSkelV1/A_Dragon_Walk_Anim.A_Dragon_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FShove(TEXT("/Game/Art/DragonSkelV1/A_Dragon_WingShove_Anim.A_Dragon_WingShove_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSweep(TEXT("/Game/Art/DragonSkelV1/A_Dragon_WingSweep_Anim.A_Dragon_WingSweep_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSanct(TEXT("/Game/Art/DragonSkelV1/A_Dragon_Sanctuary_Anim.A_Dragon_Sanctuary_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FFlame(TEXT("/Game/Art/DragonSkelV1/A_Dragon_FirstFlame_Anim.A_Dragon_FirstFlame_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/DragonSkelV1/A_Dragon_HitReact_Anim.A_Dragon_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/DragonSkelV1/A_Dragon_Stagger_Anim.A_Dragon_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/DragonSkelV1/A_Dragon_Defeat_Anim.A_Dragon_Defeat_Anim"));

	if (Model.Succeeded())
	{
		RivalBody->SetSkeletalMesh(Model.Object);
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (Sphere.Succeeded())
		{
			PlaceholderBody->SetStaticMesh(Sphere.Object);
			PlaceholderBody->SetRelativeScale3D(FVector(1.7f, 1.7f, 3.4f));
		}
	}
	IdleAnim = LoadRivalClip(FIdle);
	MoveAnim = LoadRivalClip(FWalk);
	ShoveAnim = LoadRivalClip(FShove);
	SweepAnim = LoadRivalClip(FSweep);
	SanctuaryAnim = LoadRivalClip(FSanct);
	FlameAnim = LoadRivalClip(FFlame);
	HitReactAnim = LoadRivalClip(FHit);
	StaggerAnim = LoadRivalClip(FStagger);
	DefeatAnim = LoadRivalClip(FDefeat);
}

void ALumenDragonlord::PostRivalBeginPlay()
{
	if (LanternLight) { LanternLight->SetIntensity(280.f); }
}

void ALumenDragonlord::SelectMove(float DistToHero)
{
	TArray<EDragonMove> Pool = { EDragonMove::WingShove, EDragonMove::WingSweep, EDragonMove::Sanctuary };
	if (Phase >= 2) { Pool.Add(EDragonMove::FirstFlame); }
	if (Phase >= 3) { Pool.Add(EDragonMove::Sanctuary); }   // he gives MORE as it deepens
	EDragonMove Picked = Pool[FMath::RandRange(0, Pool.Num() - 1)];
	if (Picked == Move && Pool.Num() > 1)
	{
		Picked = Pool[(Pool.Find(Picked) + 1) % Pool.Num()];
	}
	Move = Picked;
}

void ALumenDragonlord::StartTelegraph()
{
	bHitThisAttack = false;
	GetCharacterMovement()->StopMovementImmediately();

	float Tell = ShoveTell;
	switch (Move)
	{
	case EDragonMove::WingSweep:  Tell = SweepTell; break;
	case EDragonMove::Sanctuary:  Tell = SanctTell; break;
	case EDragonMove::FirstFlame: Tell = FlameTell; break;
	default: break;
	}
	Tell *= TellScale();

	if (TelegraphLight) { TelegraphLight->SetLightColor(LumenAmber); }   // amber, always amber

	switch (Move)
	{
	case EDragonMove::WingShove:
		PlayOneShot(ShoveAnim, Tell + ShoveActive + ShoveRecover * 0.4f, ShoveClipStart, ShoveClipRate);
		break;
	case EDragonMove::WingSweep:
		PlayOneShot(SweepAnim, Tell + SweepActive + SweepRecover * 0.4f, SweepClipStart, SweepClipRate);
		break;
	case EDragonMove::Sanctuary:
		PlayOneShot(SanctuaryAnim, Tell + SanctActive + 0.3f, SanctClipStart, SanctClipRate);
		break;
	case EDragonMove::FirstFlame:
		PlayOneShot(FlameAnim, Tell + FlameActive + 0.3f, FlameClipStart, FlameClipRate);
		break;
	default: break;
	}
	EnterState(ERivalState::Telegraph, Tell);
}

void ALumenDragonlord::StartAttack()
{
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 60.f),
		LumenAmber * 2.6f, 1.5f, 5200.f, 0.24f);

	ASparkHeroCharacter* Hero = ResolveHero();
	switch (Move)
	{
	case EDragonMove::WingShove:
		EnterState(ERivalState::Attack, ShoveActive);
		break;
	case EDragonMove::WingSweep:
		EnterState(ERivalState::Attack, SweepActive);
		break;
	case EDragonMove::Sanctuary:
	{
		// The gift lands where YOU stand — a haven of light around the hero.
		SanctuaryLoc = Hero ? Hero->GetActorLocation()
		                    : GetActorLocation() + GetActorForwardVector() * 320.f;
		SanctuaryLoc.Z = GetActorLocation().Z
			- GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 8.f;
		bSanctuaryActive = true;
		SanctuaryUntil = Now() + SanctSeconds;
		NextSanctFx = Now();
		EnterState(ERivalState::Attack, SanctActive);
		break;
	}
	case EDragonMove::FirstFlame:
		// A pillar of amber light — spectacle, not a wound.
		ASparkImpactBurst::Burst(this, GetActorLocation()
			+ GetActorForwardVector() * 200.f, LumenAmber * 3.2f, FlameRadius / 90.f, 7000.f, 0.4f);
		EnterState(ERivalState::Attack, FlameActive);
		break;
	default:
		FinishAttack(ShoveRecover);
		break;
	}
}

void ALumenDragonlord::TickAttack(float DeltaTime, ASparkHeroCharacter* Hero)
{
	switch (Move)
	{
	case EDragonMove::WingShove:
		// SHEPHERD'S WING: he pushes you AWAY — to safety — and never harms you.
		if (Hero && !bHitThisAttack)
		{
			const FVector To = Hero->GetActorLocation() - GetActorLocation();
			if (FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > 0.1f
				&& To.Size() <= ShoveReach)
			{
				bHitThisAttack = true;
				const FVector Away = To.GetSafeNormal2D();
				Hero->LaunchCharacter(Away * ShoveForce + FVector(0.f, 0.f, ShoveLift), true, true);
				ASparkImpactBurst::Burst(this, Hero->GetActorLocation() + FVector(0.f, 0.f, 30.f),
				                         LumenAmber * 2.4f, 1.2f, 4200.f);
			}
		}
		break;

	case EDragonMove::WingSweep:
		// A grand arc — the lightest brush, then a push clear.
		if (Hero && !bHitThisAttack
			&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= SweepRadius)
		{
			bHitThisAttack = true;
			FVector Away = (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
			Hero->LaunchCharacter(Away * (ShoveForce * 0.7f) + FVector(0.f, 0.f, 300.f), true, true);
			Hero->TakeEmberHit(SweepEmbers);   // the only contact he ever makes
			ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 50.f),
			                         LumenAmber * 2.8f, SweepRadius / 150.f, 5000.f);
		}
		break;

	case EDragonMove::FirstFlame:
		// The flame is light, not fire — it eases you back, gently.
		if (Hero && FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= FlameRadius * 0.5f)
		{
			const FVector Away = (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
			Hero->GetCharacterMovement()->Velocity += Away * 600.f * DeltaTime * 60.f;
		}
		break;

	case EDragonMove::Sanctuary:
	default:
		break;   // the sanctuary heals in the main Tick, even after this attack ends
	}
}

void ALumenDragonlord::HandleAttackExpired(ASparkHeroCharacter* Hero)
{
	float Recover = ShoveRecover;
	switch (Move)
	{
	case EDragonMove::WingSweep:  Recover = SweepRecover; break;
	case EDragonMove::Sanctuary:  Recover = SanctRecover; break;
	case EDragonMove::FirstFlame: Recover = FlameRecover; break;
	default: break;
	}
	FinishAttack(Recover);
}

float ALumenDragonlord::GetTriggerRange() const
{
	switch (Move)
	{
	case EDragonMove::WingSweep:  return SweepRadius * 0.8f;
	case EDragonMove::Sanctuary:  return 720.f;   // the gift reaches across the room
	case EDragonMove::FirstFlame: return 600.f;
	default:                      return ShoveReach * 0.85f;
	}
}

void ALumenDragonlord::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// The lantern breathes — the heart of the game, always amber.
	if (LanternLight)
	{
		LanternLight->SetIntensity(280.f + 80.f * FMath::Sin(Now() * 1.6f));
	}

	// WING-GLOW SANCTUARY: while it glows, it refills the hero's embers. The gift.
	if (bSanctuaryActive)
	{
		if (Now() >= SanctuaryUntil)
		{
			bSanctuaryActive = false;
		}
		else
		{
			if (Now() >= NextSanctFx)
			{
				NextSanctFx = Now() + 0.4f;
				ASparkImpactBurst::Burst(this, SanctuaryLoc + FVector(0.f, 0.f, 10.f),
				                         FLinearColor(2.2f, 1.6f, 0.7f), SanctRadius / 120.f, 2800.f, 0.32f);
			}
			if (ASparkHeroCharacter* Hero = ResolveHero())
			{
				if (FVector::Dist2D(Hero->GetActorLocation(), SanctuaryLoc) <= SanctRadius)
				{
					if (UEmberMeterComponent* Meter = Hero->GetEmberMeter())
					{
						Meter->Refill(SanctHealPerSec * DeltaTime);
					}
				}
			}
		}
	}
}
