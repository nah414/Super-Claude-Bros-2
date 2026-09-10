// Shellback Alpha — the Roly, three sizes up and three hits tougher. Everything
// inherited; only the bulk, the speed, and the flips are the boss's own.

#include "ShellbackAlpha.h"

#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AShellbackAlpha::AShellbackAlpha()
{
	// Roly→Alpha: the inheritance ladder (Bible §11). ~2.7x the little one.
	GetCapsuleComponent()->SetCapsuleSize(100.f, 90.f);
	BodyScale = 1.25f;

	HitsToDefeat = 3;       // flip it, stomp it, flip it, stomp it... then it's done
	FlipRecoverSeconds = 2.6f;
	bWallCrashFlips = true; // W3 canon: bait the charge into the hard knots -> crash-flip

	AggroRadius = 1100.f;
	WindSeconds = 0.7f;
	RollSpeed = 1300.f;     // a freight cannonball
	RollSeconds = 1.3f;
	RecoverSeconds = 1.5f;
	SpinRate = 520.f;       // the big shell rolls slower-looking
	ContactChipEmbers = 12.f;
	KnockbackForce = 950.f;
	KnockbackLift = 360.f;
	StompBounce = 680.f;
	GetCharacterMovement()->MaxWalkSpeed = RollSpeed;
}
