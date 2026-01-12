// Fill out your copyright notice in the Description page of Project Settings.


#include "SignalSources/VAAudioInputSignalSource.h"

#include "VAUtils.h"
#include "VAPlugin.h"

void UVAAudioInputSignalSource::Initialize()
{
	if (bInitialized)
	{
		FVAUtils::LogStuff("[UVAAudioInputSignalSource::Initialize()]: Signal source is already initialized, aborting...", true);
		return;
	}


	ID = FVAPlugin::GetAudioInputSignalSourceID(Channel);
	if (!IsValidID(ID))
	{
		FVAUtils::LogStuff("[UVAAudioInputSignalSource::Initialize()]: Error initializing Audio Input Signal Source", true);
		return;
	}

	bInitialized = true;
}
