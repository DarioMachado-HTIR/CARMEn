// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "VAEnums.h"									// EAddress

#include "Templates/SharedPointer.h"

#include "GameFramework/Actor.h"
#include "AuralizationMode/VAAuralizationModeController.h"

#include "Events/DisplayClusterEventWrapper.h"

#include "VAReceiverActor.generated.h"


//forward declarations to not include private header files
class FVAPlugin;
class AVAReflectionWall;
class FVADirectivity;
class FVADirectivityManager;
class FVAHRIR;
class FVAHRIRManager;


UCLASS(ClassGroup = (VA))
class VAPLUGIN_API AVAReceiverActor : public AActor
{
	GENERATED_BODY()

	friend class UVAAbstractSourceComponent;
   friend class FVAPlugin;

protected:


	// How many units in UE equal 1m in World
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Scale", Category = "General Settings"))
	float WorldScale = 100.0f;

	// How often are position updates etc. send
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Updates per second", Category = "General Settings"))
	int UpdateRate = 30;

	// Check if should ask for debug Mode?
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Ask for Debug mode?", Category = "General Settings"))
	bool bAskForDebugMode = false;

	// View point to head center offset (x forward-dir, y right-dir, z up-dir) in cm. Note that x and z most probably need to be negative!
	UPROPERTY(EditAnywhere, meta = (Category = "General Settings"))
		FVector ViewpointToHeadcenterOffset = FVector(0, 0, 0);

	// Source for tracking data, e.g., VirtualRealityPawn, ManualData (e.g., manually passed on from Optitrack)
	UPROPERTY(EditAnywhere, meta = (Category = "General Settings"))
		ETrackingSource TrackingSource = ETrackingSource::VirtualRealityPawn;


	// Choose how to connect to the Server (automatic: build with windows connect with 127.0.0.1:12340, build with linux connect to cave)
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Usecase", Category = "Connection"))
	TEnumAsByte<EConnectionSetting::Type> AddressSetting = EConnectionSetting::Type::Automatic;

	// IP Address for manual input
	UPROPERTY(EditAnywhere, meta = (DisplayName = "IP Adress", Category = "Connection"))
	FString ServerIPAddress = "10.0.1.240";

	// Port for manual input
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Port [0, 65535]", Category = "Connection",
		ClampMin = "0", ClampMax = "65535", UIMin = "0", UIMax = "65535"))
	uint16 ServerPort = 12340;

	// Always reconnect to VAServer when this level is started?
	UPROPERTY(EditAnywhere, meta = (Category = "Connection", DisplayName = "Automatic Reconnect"))
	bool bReconnecToVAServer = true;

	// Activate automatic remote VAServer start via Python (VAServerLauncher)
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Use VAServerLauncher", Category = "VAServerLauncher"))
	bool bAutomaticRemoteVAStart = true;

	// Port for remote VAServerLauncher [0, 65535]
	UPROPERTY(EditAnywhere, meta = (DisplayName = "VAServerLauncher Port", Category = "VAServerLauncher",
		ClampMin = "0", ClampMax = "65535", UIMin = "0", UIMax = "65535"))
	uint16 RemoteVAStarterPort = 41578;

	// ID for VAServer version being started automatically, configurable in the Config of the VAServerLauncher
	UPROPERTY(EditAnywhere, meta = (DisplayName = "VAServer Version ID", Category = "VAServerLauncher"))
	FString WhichVAServerVersionToStart = TEXT("2022.a");

	// Ini file with VA renderer settings. File will be sent to VAServer launcher on startup if filename is not empty.
	UPROPERTY(EditAnywhere, meta = (DisplayName = "VARenderer.ini file", Category = "VAServerLauncher"))
	FString VARendererIniFile = TEXT("");

	//Used to select the group of reproduction modules specified in VAServerLauncher config.
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Reproduction input signal type", Category = "VAServerLauncher"))
	EReproductionInput ReproductionInputType = EReproductionInput::Binaural;


	// Read an initial mapping file for directivities?
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Read an initial mapping file?", Category = "Directivity Manager"))
	bool bReadInitialMappingFile = false;
	
	// File name of the Directivity mapping file (e.g., for chaning directivities dynamically based on phonemes)
	// if not specified it will be ignored.
	UPROPERTY(EditAnywhere, meta = (DisplayName = "Name of ini file for directivities", Category = "Directivity Manager"))
	FString DirMappingFileName = "";

	// Controller for global auraliztion modes
	UPROPERTY(EditAnywhere, Instanced, NoClear, meta = (DisplayName = "Auraliztion Mode Controller", Category = "Auralization Modes"))
	UVAAuralizationModeController* AuralizationModeController;

public:

	// Sets default values for this actor's properties
	AVAReceiverActor();
	void Tick(float DeltaTime) override;

	// Interface for HRIR Settings
	UFUNCTION(BlueprintCallable)
	void SetUpdateRate(int Rate);

	// Interface for Dir Mapping
	UFUNCTION(BlueprintCallable)
	bool ReadDirMappingFile(FString FileName);

	// Interface for HRIR Settings
	UFUNCTION(BlueprintCallable)
	bool SetHRIRByFileName(FString FileName);
	
	// Set Debug Mode to toggle global visibility of all sound Sources
	UFUNCTION(BlueprintCallable)
	void SetDebugMode(bool bDebugMode);

	// Gets scale of virtual world compared to real world
	UFUNCTION(BlueprintCallable)
	float GetScale() const;

	// Gets IP Address
	UFUNCTION(BlueprintCallable)
	FString GetIPAddress() const;

	// Gets Port
	UFUNCTION(BlueprintCallable)
	int GetPort() const;

	// Gets auralization mode controller
	UFUNCTION(BlueprintCallable)
	UVAAuralizationModeController* GetAuralizationModeController() const;

	// Update Function for TrackingSource==ManualData case.
	// This method has to be called in that case regularly to update the receiver's position/orientation, as this is not done automatically
	UFUNCTION(BlueprintCallable)
	bool SetManualReceiverData(FVector VirtualPos, FRotator VirtualRot, FVector RealWorldPos=FVector(0,0,0), FRotator RealWorldRot = FRotator(0, 0, 0));

	//Returns the VA receiver ID
	int GetReceiverID() const;


protected:
	// Get Walls
	TArray<AVAReflectionWall*> GetReflectionWalls();					// SourceC

	// Directivity Handling
	TSharedPtr<FVADirectivity> GetDirectivityByMapping(FString Phoneme) const;		// SourceC
	TSharedPtr<FVADirectivity> GetDirectivityByFileName(FString FileName);			// SourceC

	
	// Cluster Stuff
	void RunOnAllNodes(FString Command);
	DECLARE_DISPLAY_CLUSTER_EVENT(AVAReceiverActor, RunOnAllNodes);

	// Getter Functions	
	bool IsInitialized() const;											// SourceC
	int GetUpdateRate() const;											// SourceC

	
	// Initialization
	void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	// Position updates
	bool UpdateVirtualWorldPose();
	bool UpdateRealWorldPose();

	void InitializeWalls();

	
#if WITH_EDITOR
	bool CanEditChange(const FProperty* InProperty) const override;
#endif

	
	// Receiver Specific Data
	int ReceiverID;
	TSharedPtr<FVADirectivityManager> DirManager;
	TSharedPtr<FVAHRIRManager> HRIRManager;

	TSharedPtr<FVAHRIR> CurrentHRIR;

	TArray<AVAReflectionWall*> ReflectionWalls;
	
	// State of Actor
	bool bInitialized = false;
	bool bWallsInitialized = false;


	// Time stuff
	float TimeSinceUpdate;
	float TotalTime;

	// Event Listener Delegate
	FOnClusterEventJsonListener ClusterEventListenerDelegate;

};
