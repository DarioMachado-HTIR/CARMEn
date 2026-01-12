// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "SoundSource/VAAbstractSourceComponent.h"
#include "VAAudioInputSourceComponent.generated.h"

/**
 * 
 */
UCLASS(ClassGroup = (VA), meta = (BlueprintSpawnableComponent))
class VAPLUGIN_API UVAAudioInputSourceComponent : public UVAAbstractSourceComponent
{
	GENERATED_BODY()
public:

	UVAAudioInputSourceComponent();

};
