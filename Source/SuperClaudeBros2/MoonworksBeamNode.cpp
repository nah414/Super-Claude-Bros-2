#include "MoonworksBeamNode.h"

#include "Bramblehulk.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "InteractionSubsystem.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "MoonflowerPlatform.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	// The moonlight look, damped per the Brightness War. The focused crystal
	// brightens ITSELF (diegetic prompt) — never a floating UI.
	constexpr float CrownIdleIntensity = 650.f;
	constexpr float CrownFocusScale = 2.4f;
	constexpr float ImpactIntensity = 1900.f;
}

AMoonworksBeamNode::AMoonworksBeamNode()
{
	PrimaryActorTick.bCanEverTick = true;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	SetRootComponent(VisualRoot);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshyCrystal(TEXT("/Game/Art/Moonworks/moon_crystal.moon_crystal"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> Plasma(TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma"));

	// Body: Meshy prop when the stage-29 import lands; crystal-shard cone until then.
	// Meshy bodies keep identity transforms — the garden script probes their bounds
	// and sizes each instance; the cone's offsets are tuned here because it never gets one.
	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	BodyMesh->SetupAttachment(VisualRoot);
	BodyMesh->SetCollisionProfileName(TEXT("BlockAll"));   // blocks beams and feet alike
	if (MeshyCrystal.Succeeded())
	{
		BodyMesh->SetStaticMesh(MeshyCrystal.Object.Get());
	}
	else if (Cone.Succeeded())
	{
		BodyMesh->SetStaticMesh(Cone.Object.Get());
		BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, 120.f));
		BodyMesh->SetRelativeScale3D(FVector(1.1f, 1.1f, 2.4f));
	}

	CrownGlow = CreateDefaultSubobject<UPointLightComponent>(TEXT("CrownGlow"));
	CrownGlow->SetupAttachment(VisualRoot);
	CrownGlow->SetRelativeLocation(FVector(0.f, 0.f, 210.f));
	CrownGlow->SetLightColor(FLinearColor(0.65f, 0.85f, 1.f));
	CrownGlow->SetIntensity(CrownIdleIntensity);
	CrownGlow->SetAttenuationRadius(420.f);
	CrownGlow->SetCastShadows(false);

	for (int32 i = 0; i < 2; ++i)
	{
		BeamMesh[i] = CreateDefaultSubobject<UStaticMeshComponent>(*FString::Printf(TEXT("Beam%d"), i));
		BeamMesh[i]->SetupAttachment(VisualRoot);
		BeamMesh[i]->SetAbsolute(true, true, true);   // shafts live in world space
		if (Cylinder.Succeeded()) { BeamMesh[i]->SetStaticMesh(Cylinder.Object.Get()); }
		if (Plasma.Succeeded()) { BeamMesh[i]->SetMaterial(0, Plasma.Object.Get()); }
		BeamMesh[i]->SetCollisionEnabled(ECollisionEnabled::NoCollision);   // light never blocks light
		BeamMesh[i]->SetCastShadow(false);
		BeamMesh[i]->SetVisibility(false);

		ImpactGlow[i] = CreateDefaultSubobject<UPointLightComponent>(*FString::Printf(TEXT("ImpactGlow%d"), i));
		ImpactGlow[i]->SetupAttachment(VisualRoot);
		ImpactGlow[i]->SetAbsolute(true, true, true);
		ImpactGlow[i]->SetLightColor(FLinearColor(0.7f, 1.4f, 1.7f));
		ImpactGlow[i]->SetIntensity(0.f);
		ImpactGlow[i]->SetAttenuationRadius(380.f);
		ImpactGlow[i]->SetCastShadows(false);
	}
}

void AMoonworksBeamNode::BeginPlay()
{
	Super::BeginPlay();

	// Placed actor: MIDs are born HERE, never in the constructor (the unsavable-level law).
	if (UMaterialInterface* Base = BodyMesh ? BodyMesh->GetMaterial(0) : nullptr)
	{
		// Only skin the plasma family — a real Meshy prop keeps its imported textures.
		if (Base->GetName().Contains(TEXT("SparkPlasma")))
		{
			BodyMID = UMaterialInstanceDynamic::Create(Base, this);
			BodyMID->SetVectorParameterValue(TEXT("Tint"), BeamTint * 0.35f);
			BodyMesh->SetMaterial(0, BodyMID);
		}
	}
	for (int32 i = 0; i < 2; ++i)
	{
		if (UMaterialInterface* Base = BeamMesh[i] ? BeamMesh[i]->GetMaterial(0) : nullptr)
		{
			BeamMID[i] = UMaterialInstanceDynamic::Create(Base, this);
			BeamMID[i]->SetVectorParameterValue(TEXT("Tint"), BeamTint);
			BeamMesh[i]->SetMaterial(0, BeamMID[i]);
		}
	}

	TargetYaw = GetActorRotation().Yaw;
	ShimmerPhase = GetActorLocation().X * 0.013f;   // neighbors never pulse in lockstep

	if (UWorld* W = GetWorld())
	{
		if (UInteractionSubsystem* Sub = W->GetSubsystem<UInteractionSubsystem>())
		{
			Sub->Register(this);
		}
	}
}

float AMoonworksBeamNode::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

bool AMoonworksBeamNode::IsFed() const
{
	return Now() - LastFedTime < FedGraceSeconds;
}

FVector AMoonworksBeamNode::EmitPoint() const
{
	return GetActorLocation() + FVector(0.f, 0.f, EmitHeight);
}

void AMoonworksBeamNode::GetOutDirections(TArray<FVector>& Out) const
{
	Out.Add(GetActorForwardVector());
}

bool AMoonworksBeamNode::OnInteractTap(ASparkHeroCharacter* Hero)
{
	if (!bPlayerRotatable) { return false; }
	// INPUT LAW: the step COMMITS on the press — the swing that follows is theater.
	TargetYaw = FMath::UnwindDegrees(TargetYaw + RotateStepDeg);
	if (CrownGlow) { CrownGlow->SetIntensity(CrownIdleIntensity * CrownFocusScale * 1.4f); }   // the click flash
	return true;
}

void AMoonworksBeamNode::SetFocusHighlight(bool bNewFocused)
{
	bFocused = bNewFocused;
	if (CrownGlow) { CrownGlow->SetIntensity(CrownIdleIntensity * (bFocused ? CrownFocusScale : 1.f)); }
}

void AMoonworksBeamNode::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// The cosmetic swing toward the committed stop.
	FRotator R = GetActorRotation();
	if (!FMath::IsNearlyEqual(R.Yaw, TargetYaw, 0.05f))
	{
		R.Yaw = FMath::FixedTurn(R.Yaw, TargetYaw, RotateInterpSpeed * 45.f * DeltaSeconds);
		SetActorRotation(R);
	}

	if (EmitsUnfed())
	{
		Propagate(DeltaSeconds, 0);
	}
	else if (!IsFed())
	{
		HideBeams();
	}

	// LOAD LAW: continuous params breathe at 10Hz, never per frame.
	ShimmerClock += DeltaSeconds;
	if (ShimmerClock >= 0.1f)
	{
		ShimmerClock = 0.f;
		ShimmerPhase += 0.63f;
		const float Shimmer = 0.88f + 0.24f * FMath::Sin(ShimmerPhase);
		const bool bLit = EmitsUnfed() || IsFed();
		for (int32 i = 0; i < 2; ++i)
		{
			if (BeamMID[i] && bBeamVisible[i]) { BeamMID[i]->SetVectorParameterValue(TEXT("Tint"), BeamTint * Shimmer); }
			if (ImpactGlow[i]) { ImpactGlow[i]->SetIntensity(bBeamVisible[i] ? ImpactIntensity * Shimmer : 0.f); }
		}
		if (BodyMID) { BodyMID->SetVectorParameterValue(TEXT("Tint"), BeamTint * (bLit ? 0.55f : 0.28f) * Shimmer); }
		if (CrownGlow && !bFocused)
		{
			CrownGlow->SetIntensity(CrownIdleIntensity * (bLit ? 1.35f : 0.8f) * Shimmer);
		}
	}
}

void AMoonworksBeamNode::OnBeamFed(float DeltaTime, int32 Depth)
{
	if (!bLoggedFed)
	{
		bLoggedFed = true;
		UE_LOG(LogTemp, Display, TEXT("MOONWORKS_MARKER: %s fed (depth %d)"), *GetName(), Depth);
	}
	LastFedTime = Now();
	Propagate(DeltaTime, Depth);
}

void AMoonworksBeamNode::Propagate(float DeltaTime, int32 Depth)
{
	if (Depth >= MaxDepth) { return; }
	if (PropagatedFrame == GFrameCounter) { return; }   // one pass per frame — the mirror-loop guard
	PropagatedFrame = GFrameCounter;

	TArray<FVector> Dirs;
	GetOutDirections(Dirs);

	UWorld* W = GetWorld();
	const FVector From = EmitPoint();

	for (int32 i = 0; i < 2; ++i)
	{
		if (!W || i >= Dirs.Num())
		{
			bBeamVisible[i] = false;
			if (BeamMesh[i]) { BeamMesh[i]->SetVisibility(false); }
			continue;
		}

		FHitResult Hit;
		FCollisionQueryParams Params(FName(TEXT("Moonbeam")), false, this);
		const FVector To = From + Dirs[i] * MaxBeamRange;
		const bool bHit = W->LineTraceSingleByChannel(Hit, From, To, ECC_Visibility, Params);
		const FVector End = bHit ? Hit.ImpactPoint : To;

		LayBeam(i, From, End, bHit);

		if (!bHit) { continue; }

		if (AMoonworksBeamNode* Node = Cast<AMoonworksBeamNode>(Hit.GetActor()))
		{
			Node->OnBeamFed(DeltaTime, Depth + 1);
		}
		else if (AMoonflowerPlatform* Flower = Cast<AMoonflowerPlatform>(Hit.GetActor()))
		{
			Flower->FeedLight();
		}
		else if (ABramblehulk* Hulk = Cast<ABramblehulk>(Hit.GetActor()))
		{
			// The soothe channel (Roadmap II): the beam kit pointed at a big friend.
			if (!bLoggedSoothe)
			{
				bLoggedSoothe = true;
				UE_LOG(LogTemp, Display, TEXT("MOONWORKS_MARKER: %s beam soothing %s"), *GetName(), *Hulk->GetName());
			}
			Hulk->AddCalm(BeamCalmPerSecond * DeltaTime);
		}
	}
}

void AMoonworksBeamNode::LayBeam(int32 Index, const FVector& From, const FVector& To, bool bHitSomething)
{
	if (!BeamMesh[Index]) { return; }
	const FVector Span = To - From;
	const float Len = Span.Size();
	if (Len < 20.f)
	{
		bBeamVisible[Index] = false;
		BeamMesh[Index]->SetVisibility(false);
		return;
	}

	BeamMesh[Index]->SetWorldLocation(From + Span * 0.5f);
	BeamMesh[Index]->SetWorldRotation(FRotationMatrix::MakeFromZ(Span / Len).Rotator());
	// Engine cylinder: 100uu tall, 50uu radius.
	BeamMesh[Index]->SetWorldScale3D(FVector(BeamRadius / 50.f, BeamRadius / 50.f, Len / 100.f));
	BeamMesh[Index]->SetVisibility(true);
	bBeamVisible[Index] = true;
	BeamEnd[Index] = To;

	if (ImpactGlow[Index])
	{
		ImpactGlow[Index]->SetWorldLocation(To + FVector(0.f, 0.f, 25.f));
		if (!bHitSomething) { ImpactGlow[Index]->SetIntensity(0.f); }
	}
}

void AMoonworksBeamNode::HideBeams()
{
	for (int32 i = 0; i < 2; ++i)
	{
		bBeamVisible[i] = false;
		if (BeamMesh[i]) { BeamMesh[i]->SetVisibility(false); }
		if (ImpactGlow[i]) { ImpactGlow[i]->SetIntensity(0.f); }
	}
}

// ---------------- The source ----------------

AMoonBeamSource::AMoonBeamSource()
{
	// A chrome pylon pouring the Mirror's light: taller, slimmer, never rotatable.
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (Cylinder.Succeeded() && BodyMesh)
	{
		BodyMesh->SetStaticMesh(Cylinder.Object.Get());
		BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, 90.f));
		BodyMesh->SetRelativeScale3D(FVector(0.5f, 0.5f, 1.8f));
	}
	bPlayerRotatable = false;
}
