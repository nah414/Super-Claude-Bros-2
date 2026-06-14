// The Foundry King — the Warlord, crowned. Everything inherited; only the scale,
// the reach, and the grandeur of the furnace are his own.

#include "FoundryKing.h"

#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AFoundryKing::AFoundryKing()
{
	// Roly→Shellback Alpha, Warlord→Foundry King: the inheritance ladder (Bible §11).
	GetCapsuleComponent()->SetCapsuleSize(80.f, 112.f);   // ~1.4x the Warlord
	SkelMeshScale = 1.4f;
	RivalDisplayName = TEXT("THE FOUNDRY KING");

	ApproachSpeed = 540.f;   // RESPONSE: catch the player (was 470 — never reached him)
	TurnRate = 6.f;          // RESPONSE: track a strafing player (was 4)
	IntroSeconds = 1.6f;     // snappier first contact (was 1.9)
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;

	// Longer reach to match the bigger body.
	SwingReach = 340.f;
	ChopReach = 310.f;
	SweepRadius = 400.f;
	KnockbackForce = 1180.f;
	KnockbackLift = 480.f;

	// A GRANDER furnace — the King's vent is wider and burns longer.
	VentConeReach = 540.f;
	VentConeHalfAngleDeg = 50.f;
	VentActive = 3.6f;
	VentTickEmbers = 6.f;

	// Royal molten gold where the Warlord ran orange.
	HitBurstColor = FLinearColor(3.9f, 2.4f, 0.7f);
	DefeatBurstColor = FLinearColor(5.2f, 3.2f, 1.1f);
	DefeatBurstScale = 2.6f;
}
