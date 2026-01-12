// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "SignalSources/VAAbstractSignalSource.h"
#include "VAAudioInputSignalSource.generated.h"

/**
 * 
 */
UCLASS(ClassGroup = (VA))
class VAPLUGIN_API UVAAudioInputSignalSource : public UVAAbstractSignalSource
{
	GENERATED_BODY()

protected:
	// Input channel used to stream into signal source
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Input Channel ID", Category = "Audio Input", ClampMin = "1"))
		int Channel = 1;

public:
	UVAAudioInputSignalSource() = default;

	// Creates the signal source in VA and sets the ID accordingly
	void Initialize() override;

};
