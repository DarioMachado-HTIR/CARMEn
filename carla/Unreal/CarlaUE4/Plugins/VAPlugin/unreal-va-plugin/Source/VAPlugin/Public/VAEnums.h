#pragma once

#include "CoreMinimal.h"


UENUM(BlueprintType)
namespace EPlayAction
{
	enum Type
	{
		NoPlayAction = -1	UMETA(Hidden),
		Stop = 0,
		Pause = 1,
		Play = 2
	};
}

UENUM()
enum class ETrackingSource : uint8
{
	VirtualRealityPawn, //using the head of the VRPawn for head tracking
	ManualData //rely on external data to be manually set for head tracking (receiver position/orientation)
};

UENUM(BlueprintType)
namespace EConnectionSetting
{
	enum Type
	{
		Automatic = 0,
		Localhost = 1,
		Cave = 2,
		Manual = 3
	};
}

UENUM()
enum class EReproductionInput : uint8
{
	// Use reproduction modules for binaural signals
	Binaural,
	// Use reproduction modules for ambisonics signals
	Ambisonics,
	// Use reproduction modules for custom purposes (e.g. mixed signal types)
	Custom
};


UENUM(BlueprintType)
namespace EDirectivitySetting
{
	enum Type
	{
		DefaultDirectivity = 0,
		Phoneme = 1,
		NoDirectivity = 2,
		ManualFile = 3
	};
}


UENUM(BlueprintType)
namespace EMovement
{
	enum Type
	{
		MoveWithObject = 0,
		ObjectSpawnPoint = 1,
		AttachToBone = 2,
	};
}

