// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "VAEnums.h"
#include "../../Private/SignalSources/VAAudiofileManager.h"


#include "Events/DisplayClusterEventWrapper.h"
#include <string>

#include "CoreMinimal.h"
#include "SignalSources/VAAbstractSignalSource.h"

#include "VAAudiofileSignalSource.generated.h"


/**
 * 
 */
UCLASS(ClassGroup = (VA))
class VAPLUGIN_API UVAAudiofileSignalSource : public UVAAbstractSignalSource
{
	GENERATED_BODY()
	
public:
	UVAAudiofileSignalSource() = default;
	~UVAAudiofileSignalSource();

	// Creates the signal source in VA and sets the ID accordingly
	void Initialize() override;

	// *** Playback Settings *** //

	UFUNCTION(BlueprintCallable)
	bool Play();
	UFUNCTION(BlueprintCallable)
	bool PlayFromTime(float fTime);
	UFUNCTION(BlueprintCallable)
	bool Pause();
	UFUNCTION(BlueprintCallable)
	bool Stop();

	// *** Audiofile related *** //
	
	UFUNCTION(BlueprintCallable)
	// (Pre-) loads an audiofile for later usage
	//   Internally, VA creates a signal source and the ID is stored. See FVAAudiofileManager
	//   @return True on success
	bool PreLoadAudiofile(FString Filename);

	UFUNCTION(BlueprintCallable)
	// Switches the internal signal source to match the corresponding audiofile. Creates a new signal source, if audiofile is not pre-loaded.
	//    Additionally, copies sets the loop and play back action of the new internal signal source accordingly.
	//    Raises an even broadcasting the ID of the internal audiofile signal source which is "-1", if signal source could not be created.
	//    @return True on success
	bool SetAudiofile(FString Filename);

	// *** Setter *** //

	UFUNCTION(BlueprintCallable)
	bool SetLoop(bool bLoopN);
	UFUNCTION(BlueprintCallable)
	bool SetPlayBackPosition(float Time);


	// *** Getter *** //

	UFUNCTION(BlueprintCallable)
	FString GetFilename() const;
	UFUNCTION(BlueprintCallable)
	bool GetLoop() const;

	//CAUTION when used in cluster mode (e.g., CAVE):
	// GetPlayActionEnum() might be one tick behind in cluster mode, since the current play action is only synced between master and slaves after this is called
	// so make sure to, e.g., call this every frame or at least multiple times (if you, e.g., want to observe a change from play to pause)
	// Alternatively, you can also set the bDirectOnMaster flag to get the status directly from the master, in that case you should make sure
	// that everything is synced to the slaves, e.g., using sync components, as data will be delayed on the slaves!!!
	UFUNCTION(BlueprintCallable) 
	EPlayAction::Type GetPlayActionEnum(bool bDirectOnMaster = false);

	

	// *** Events/Delegates *** //

	DECLARE_EVENT_OneParam(UVAAudiofileSignalSource, FChangedAudiofileEvent, const std::string&)
	//Get the delegate for the event broadcasted on an audiofile change, which provides the new signal source ID
	FChangedAudiofileEvent& OnAudiofileChanged() { return AudiofileChangedEvent; }

protected:
	// Copies the loop bool and play action of the current signal source to the one with given ID
	// @return True on success
	bool CopySignalSourceSettings(const std::string& ID);

	// Action of the sound source at the first tick
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Starting State", Category = "Audio file"))
		TEnumAsByte<EPlayAction::Type> StartingPlayAction = EPlayAction::Type::Stop;

	// Name of Sound file. Subfolders can be used, e.g.,  "folder/soundfile.wav"
	// By default these files are looked for in the data folder of the VAServer
	// If the automatic VAServer starter script is used, they are searched relative to the Content dir and then send over to the VAServer
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Filename", Category = "Audio file"))
		FString Filename = "";

	// Sets Buffer to a specific time stamp when playing back at the first tick (see Action)
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Play from x [s]", Category = "Audio file"))
		float StartingTime = 0.0f;

	// Check if the sound should be played back in a loop
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Loop", Category = "Audio file"))
		bool bLoop = false;

private:

	bool SetPlayAction(int Action);
	int GetPlayAction(bool bDirectOnMaster=false);

	void StorePlayStateInternally(int PlayAction);
	DECLARE_DISPLAY_CLUSTER_EVENT(UVAAudiofileSignalSource, StorePlayStateInternally);
	int InterallyStoredPlayAction = -1;


	FChangedAudiofileEvent AudiofileChangedEvent;

	FVAAudiofileManager AudiofileManager;
};
