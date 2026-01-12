// Fill out your copyright notice in the Description page of Project Settings.


#include "SoundSource/VAAudioInputSourceComponent.h"

#include "SignalSources/VAAudioInputSignalSource.h"


UVAAudioInputSourceComponent::UVAAudioInputSourceComponent() : Super()
{
	SignalSource = CreateDefaultSubobject<UVAAudioInputSignalSource>("AudioInputSignalSource");
}
