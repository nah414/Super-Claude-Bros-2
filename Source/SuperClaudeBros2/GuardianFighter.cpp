// AGuardianFighter — one fighter engine, four guardians. Everything below reads the
// move TABLE the subclass populated in its constructor; nothing here knows whether it
// drives the Knight or the Boxer. The five hit SHAPES (Cone / ConeTwice / Lunge /
// Ring / Guard) cover every guardian move; the SIGNATURE row glows apart and can be
// armed to fire on a phase break (the wound-bites-back beat the Warlord proved).

#include "GuardianFighter.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "SparkHeroCharacter.h"
#include "SparkImpactBurst.h"

AGuardianFighter::AGuardianFighter()
{
	// Fighter defaults: nimble, close-quarters duelists. Each guardian overrides
	// pacing/size/colors in its own constructor; these are just sane fallbacks.
	ApproachSpeed = 600.f;
	TurnRate = 8.f;
	IntroSeconds = 1.3f;
	StaggerSeconds = 1.8f;
	KnockbackForce = 820.f;
	KnockbackLift = 360.f;
	DuelHitEmbers = 18.f;
}

int32 AGuardianFighter::AddMove(const FGuardianMove& InMove)
{
	return Moves.Add(InMove);
}

void AGuardianFighter::NotifyRivalPhaseChanged(int32 NewPhase)
{
	// A phase break ARMS the signature (if the subclass declared one): the next move
	// the guardian commits to is its headline — the duel escalates on a visible beat.
	if (SignatureIdx != INDEX_NONE && Moves.IsValidIndex(SignatureIdx))
	{
		bSignatureQueued = true;
	}
	OnGuardianPhaseChanged(NewPhase);
}

float AGuardianFighter::ModifyIncomingEmbers(float Embers, int32 /*ComboBeat*/, bool /*bCharged*/)
{
	// A guardian inside a Guard window soaks the blow (block/parry stance).
	return bGuarding ? Embers * GuardEmberScale : Embers;
}

void AGuardianFighter::ClearActiveMoveState()
{
	// Any interrupt (phase roar / stagger / disengage) drops the guard + combo latch.
	bGuarding = false;
	bComboReArmed = false;
}

void AGuardianFighter::SelectMove(float /*DistToHero*/)
{
	if (Moves.Num() == 0) { MoveIdx = INDEX_NONE; return; }

	// Armed signature wins (the phase-break headline).
	if (bSignatureQueued && Moves.IsValidIndex(SignatureIdx))
	{
		bSignatureQueued = false;
		MoveIdx = SignatureIdx;
		LastMoveIdx = MoveIdx;
		return;
	}

	// Build the legal pool for this phase, then pick — never the same move twice in
	// a row. We filter on LastMoveIdx (which survives ClearMove) rather than MoveIdx,
	// because the state machine clears MoveIdx before Approach calls SelectMove, so
	// MoveIdx is always INDEX_NONE here and the avoidance would otherwise be a no-op.
	TArray<int32> Pool;
	for (int32 i = 0; i < Moves.Num(); ++i)
	{
		if (Moves[i].MinPhase <= Phase && i != LastMoveIdx) { Pool.Add(i); }
	}
	if (Pool.Num() == 0)
	{
		// Only the just-used move is legal — allow the repeat rather than stall.
		for (int32 i = 0; i < Moves.Num(); ++i)
		{
			if (Moves[i].MinPhase <= Phase) { Pool.Add(i); }
		}
	}
	MoveIdx = Pool.Num() ? Pool[FMath::RandRange(0, Pool.Num() - 1)] : 0;
	LastMoveIdx = MoveIdx;
}

void AGuardianFighter::StartTelegraph()
{
	bHitThisAttack = false;
	bComboReArmed = false;
	bGuarding = false;
	GetCharacterMovement()->StopMovementImmediately();
	if (!Moves.IsValidIndex(MoveIdx)) { EnterState(ERivalState::Recover, 0.4f); return; }

	const FGuardianMove& M = Moves[MoveIdx];
	const float Tell = M.Tell * TellScale();
	if (TelegraphLight)
	{
		TelegraphLight->SetLightColor(M.bSignature ? SignatureColor : BodyGlowColor);
	}
	PlayOneShot(M.Clip, Tell + M.Active + M.Recover * 0.4f, M.ClipStart, M.ClipRate);
	EnterState(ERivalState::Telegraph, Tell);
}

void AGuardianFighter::StartAttack()
{
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	if (!Moves.IsValidIndex(MoveIdx)) { FinishAttack(0.5f); return; }

	const FGuardianMove& M = Moves[MoveIdx];
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 42.f),
		(M.bSignature ? SignatureColor : HitBurstColor) * 2.0f, 1.1f, 4200.f, 0.2f);

	bGuarding = (M.Kind == EGuardianMoveKind::Guard);

	if (M.Kind == EGuardianMoveKind::Lunge)
	{
		// Lock the line NOW — the lunge commits; FaceHero is off during Attack, so
		// a side-step beats it (timing, not a tracking laser).
		if (ASparkHeroCharacter* Hero = ResolveHero())
		{
			LungeDir = (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
		}
		if (LungeDir.IsNearlyZero()) { LungeDir = GetActorForwardVector(); }
	}
	EnterState(ERivalState::Attack, M.Active);
}

bool AGuardianFighter::TryConeHit(ASparkHeroCharacter* Hero, const FGuardianMove& M, float CosThreshold)
{
	if (!Hero || bHitThisAttack) { return false; }
	const FVector To = Hero->GetActorLocation() - GetActorLocation();
	if (FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > CosThreshold
		&& To.Size() <= M.Reach)
	{
		bHitThisAttack = true;
		LandDuelHit(Hero, DuelHitEmbers * M.EmberMul);
		return true;
	}
	return false;
}

void AGuardianFighter::TickAttack(float DeltaTime, ASparkHeroCharacter* Hero)
{
	if (!Moves.IsValidIndex(MoveIdx)) { return; }
	const FGuardianMove& M = Moves[MoveIdx];

	switch (M.Kind)
	{
	case EGuardianMoveKind::Cone:
		TryConeHit(Hero, M);
		break;

	case EGuardianMoveKind::ConeTwice:
		TryConeHit(Hero, M);
		// Re-arm once at the active-window midpoint for the second beat.
		if (bHitThisAttack && !bComboReArmed && Now() >= StateUntil - M.Active * 0.5f)
		{
			bComboReArmed = true;
			bHitThisAttack = false;
		}
		break;

	case EGuardianMoveKind::Ring:
		if (Hero && !bHitThisAttack
			&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= M.Reach)
		{
			bHitThisAttack = true;
			LandDuelHit(Hero, DuelHitEmbers * M.EmberMul);
		}
		break;

	case EGuardianMoveKind::Lunge:
		// Drive forward ONLY until contact — planting on the hit keeps the charge
		// from sliding the rest of the Active window (~1000uu) past the hero and
		// stranding him out of the pocket. A whiff still slides through empty space,
		// so a clean side-step is rewarded.
		if (!bHitThisAttack)
		{
			AddActorWorldOffset(LungeDir * LungeSpeed * DeltaTime, true);
			if (Hero)
			{
				const FVector To = Hero->GetActorLocation() - GetActorLocation();
				if (To.Size() <= M.Reach)
				{
					bHitThisAttack = true;
					GetCharacterMovement()->StopMovementImmediately();
					LandDuelHit(Hero, DuelHitEmbers * M.EmberMul);
				}
			}
		}
		break;

	case EGuardianMoveKind::Guard:
		// A defensive beat: no strike. bGuarding soaks incoming embers; the opening
		// is that the hero gets a free swing if they read it.
		break;

	default:
		break;
	}
}

void AGuardianFighter::HandleAttackExpired(ASparkHeroCharacter* /*Hero*/)
{
	bGuarding = false;
	const float Recover = Moves.IsValidIndex(MoveIdx) ? Moves[MoveIdx].Recover : 0.9f;
	FinishAttack(Recover);
}

float AGuardianFighter::GetTriggerRange() const
{
	if (!Moves.IsValidIndex(MoveIdx)) { return 200.f; }
	const FGuardianMove& M = Moves[MoveIdx];
	switch (M.Kind)
	{
	case EGuardianMoveKind::Lunge: return FMath::Max(M.Reach, 700.f);   // he closes from afar
	case EGuardianMoveKind::Ring:  return M.Reach * 0.8f;
	case EGuardianMoveKind::Guard: return M.Reach;                       // he braces in the pocket
	default:                       return M.Reach * 0.85f;
	}
}
