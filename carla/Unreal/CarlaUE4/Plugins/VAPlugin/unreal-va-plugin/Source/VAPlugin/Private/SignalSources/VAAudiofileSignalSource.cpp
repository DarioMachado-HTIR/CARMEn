// Fill out your copyright notice in the Description page of Project Settings.


#include "SignalSources/VAAudiofileSignalSource.h"

#include "VAUtils.h"
#include "VAPlugin.h"
#include "Utility/VirtualRealityUtilities.h"

// ****************************************************************** // 
// ******* Initialization ******************************************* //
// ****************************************************************** //

void UVAAudiofileSignalSource::Initialize()
{
	StorePlayStateInternallyEvent.Attach(this);
	if (bInitialized)
	{
		FVAUtils::LogStuff("[UVAAudiofileSignalSource::Initialize()]: Signal source is already initialized, aborting...", false);
		return;
	}

	if (Filename != "" && !SetAudiofile(Filename))
	{
		FVAUtils::LogStuff("[UVAAudiofileSignalSource::Initialize()]: Error creating Audiofile Signal Source", true);
		return;
	}
	bInitialized = true;
}

UVAAudiofileSignalSource::~UVAAudiofileSignalSource()
{
	if(bInitialized)
	{
		StorePlayStateInternallyEvent.Detach();
		//otherwise it was never attached and would throw a warning
	}
}

// ****************************************************************** // 
// ******* Bluepring Functions ************************************** //
// ****************************************************************** //

bool UVAAudiofileSignalSource::Play()
{
	return SetPlayAction(EPlayAction::Play);
}

bool UVAAudiofileSignalSource::PlayFromTime(const float fTime)
{
	if (SetPlayBackPosition(fTime))
		return SetPlayAction(EPlayAction::Play);

	return false;
}

bool UVAAudiofileSignalSource::Pause()
{
	return SetPlayAction(EPlayAction::Pause);
}

bool UVAAudiofileSignalSource::Stop()
{
	return SetPlayAction(EPlayAction::Stop);
}

bool UVAAudiofileSignalSource::PreLoadAudiofile(FString AudioFilename)
{
	return AudiofileManager.PreLoadAudiofile(AudioFilename);
}


// ****************************************************************** // 
// ******* Setter Functions ***************************************** //
// ****************************************************************** //

bool UVAAudiofileSignalSource::SetAudiofile(FString AudioFilename)
{

	if(!FVAPlugin::GetIsInitialized())
	{
		//not yet "started" (probably called from constructor or similar) so just store the file name for the initialization
		Filename=AudioFilename;
		return true;
	}
	
	std::string NewID = AudiofileManager.GetAudiofileSignalSourceID(AudioFilename);
	if (!IsValidID(NewID))
	{
		FVAUtils::LogStuff("[UVAAudiofileSignalSource::SetAudiofile()]: Audiofile " + AudioFilename + " was loaded incorrectly!", true);
		return false;
	}

	if (ID == NewID)
	{
		//TODO: Should the signal source really be stopped here as in old version?
		//Stop();
		return true;
	}

	if (!CopySignalSourceSettings(NewID))
	{
		FVAUtils::LogStuff("[UVAAudiofileSignalSource::SetAudiofile()]: Could not copy settings to signal source of new audiofile: " + AudioFilename, true);
		return false;
	}
	
	Filename = AudioFilename;
	ID = NewID;

	AudiofileChangedEvent.Broadcast(ID);

	return true;
}

bool UVAAudiofileSignalSource::SetLoop(const bool bLoopN)
{
	if(!FVAPlugin::GetIsInitialized())
	{
		//not yet "started" (probably called from constructor or similar) so just store the parameter for the initialization
		bLoop=bLoopN;
		return true;
	}

	bLoop = bLoopN;
	
	if (!UVirtualRealityUtilities::IsMaster())
	{
		return false;
	}

	if (bLoop == bLoopN)
	{
		return true;
	}

	return FVAPlugin::SetSignalSourceBufferLooping(ID, bLoop);
}

bool UVAAudiofileSignalSource::SetPlayBackPosition(const float Time)
{
	if (!UVirtualRealityUtilities::IsMaster())
	{
		return false;
	}
	return FVAPlugin::SetSignalSourceBufferPlaybackPosition(ID, Time);
}

bool UVAAudiofileSignalSource::SetPlayAction(const int Action)
{
	if (!bInitialized)
	{
		return false;
	}
	InterallyStoredPlayAction = Action;
	StorePlayStateInternallyEvent.Send(Action); //also send this to all slaves, so potentially still pending send numbers from GetPlayAction are overwritten

	if (!UVirtualRealityUtilities::IsMaster())
	{
		return false;
	}

	return FVAPlugin::SetSignalSourceBufferPlayAction(ID, EPlayAction::Type(Action));
}



// ****************************************************************** // 
// ******* Getter Functions ***************************************** //
// ****************************************************************** //

FString UVAAudiofileSignalSource::GetFilename() const
{
	return Filename;
}

bool UVAAudiofileSignalSource::GetLoop() const
{
	return bLoop;
}

EPlayAction::Type UVAAudiofileSignalSource::GetPlayActionEnum(bool bDirectOnMaster /*= false*/)
{
	return EPlayAction::Type(GetPlayAction(bDirectOnMaster));
}

int UVAAudiofileSignalSource::GetPlayAction(bool bDirectOnMaster /*= false*/)
{
	if(!bInitialized)
	{
		return -1;
	}
	//we return the internally stored action in case this is in cluster and not the master
	//but also update the internally stored data by the one which the master can get from the VAServer
	//However, using cluster events to sync, so new data might only be available next frame!
	if (UVirtualRealityUtilities::IsMaster())
	{
		// in case of not being in cluster mode this directly calls StorePlayStateInternally() updating InterallyStoredPlayAction directly
		// otherwise (in cluster mode) this emits acluster event, so the internal data will be updated before next Tick
		int VAServerPlayAction = FVAPlugin::GetSignalSourceBufferPlayAction(ID);
		StorePlayStateInternallyEvent.Send(VAServerPlayAction);
		if(bDirectOnMaster)
		{
			return VAServerPlayAction;
		}
	}

	return InterallyStoredPlayAction;
}

bool UVAAudiofileSignalSource::CopySignalSourceSettings(const std::string& OtherID)
{
	if (!UVirtualRealityUtilities::IsMaster())
	{
		return false;
	}

	if (!FVAPlugin::SetSignalSourceBufferLooping(OtherID, bLoop))
	{
		return false;
	}

	int PlayAction = StartingPlayAction;
	if (bInitialized && Filename != "")
	{
		PlayAction = GetPlayAction();
		if (PlayAction == -1)
		{
			return false;
		}
	}
	return FVAPlugin::SetSignalSourceBufferPlayAction(OtherID, EPlayAction::Type(PlayAction));
}

void UVAAudiofileSignalSource::StorePlayStateInternally(int PlayAction)
{
	InterallyStoredPlayAction = PlayAction;
}
