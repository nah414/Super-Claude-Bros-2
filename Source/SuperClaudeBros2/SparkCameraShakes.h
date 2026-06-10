// Super Claude Bros 2 — subtle camera shakes for game feel.
// Three tiny, fully-C++-configured shakes: a soft landing tap, a heavier big-landing
// thump, and an energetic dash wobble. They are deliberately SMALL — juice, not nausea.
//
// ---------------------------------------------------------------------------
// API / MODULE NOTES (read me before "fixing" a compile error here):
//
//  * We derive from UCameraShakeBase (Engine module, "Camera/CameraShakeBase.h")
//    and give each class a UPerlinNoiseCameraShakePattern root pattern, created in
//    the constructor via CreateDefaultSubobject + SetRootShakePattern(). This is the
//    modern UE 5.x pattern and needs NO extra Build.cs dependencies — both classes
//    live in the "Engine" module, which this project already links (see
//    SuperClaudeBros2.Build.cs).
//
//  * We deliberately do NOT use ULegacyCameraShake: in UE 5.x it moved into the
//    GameplayCameras PLUGIN, which would require enabling the plugin and adding
//    "GameplayCameras" to Build.cs. Avoided on purpose.
//
//  * Expected include paths (UE 5.x, Engine module):
//        Engine/Source/Runtime/Engine/Classes/Camera/CameraShakeBase.h
//            -> #include "Camera/CameraShakeBase.h"
//        Engine/Source/Runtime/Engine/Classes/Shakes/PerlinNoiseCameraShakePattern.h
//            -> #include "Shakes/PerlinNoiseCameraShakePattern.h"
//    If 5.7 has moved/renamed the pattern header, the fallback options are:
//      (a) #include "Shakes/DefaultCameraShakeBase.h" and derive from
//          UDefaultCameraShakeBase instead (it is just UCameraShakeBase pre-wired
//          with a Perlin root pattern; fetch it with GetRootShakePattern() and
//          cast, instead of CreateDefaultSubobject below), or
//      (b) search the engine for "PerlinNoiseCameraShakePattern.h" and fix the path.
//
//  * Only the .cpp includes the pattern header; this header forward-declares.
// ---------------------------------------------------------------------------
//
// Intended usage (from the character / game code):
//     PC->ClientStartCameraShake(USparkLandShake::StaticClass());

#pragma once

#include "CoreMinimal.h"
#include "Camera/CameraShakeBase.h"
#include "SparkCameraShakes.generated.h"

class UPerlinNoiseCameraShakePattern;

/**
 * Soft landing tap — very short (0.18s), a few units of vertical bob and a
 * whisper of pitch. Played on every normal landing, so it must be near-subliminal.
 */
UCLASS()
class USparkLandShake : public UCameraShakeBase
{
	GENERATED_BODY()

public:
	USparkLandShake(const FObjectInitializer& ObjectInitializer);
};

/**
 * Big landing thump — 0.3s, roughly 2x the amplitude of the soft land.
 * For high-impact landings (fast-fall, big drops). Still polite.
 */
UCLASS()
class USparkBigLandShake : public UCameraShakeBase
{
	GENERATED_BODY()

public:
	USparkBigLandShake(const FObjectInitializer& ObjectInitializer);
};

/**
 * Dash wobble — 0.2s of energetic, mostly-rotational shake: small yaw wobble
 * plus a quick FOV pulse so the spark-dash feels like a jolt of speed.
 */
UCLASS()
class USparkDashShake : public UCameraShakeBase
{
	GENERATED_BODY()

public:
	USparkDashShake(const FObjectInitializer& ObjectInitializer);
};
