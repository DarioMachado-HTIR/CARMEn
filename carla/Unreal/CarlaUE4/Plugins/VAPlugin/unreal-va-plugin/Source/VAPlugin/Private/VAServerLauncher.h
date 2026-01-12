#pragma once

#include "Sockets.h"

#include "VAEnums.h"

class FVAServerLauncher
{
public:
	// Remote Start VAServer
	bool RemoteStartVAServer(const FString& Host, int Port,
	                                const FString& VersionName, const FString& VARendererIni, const EReproductionInput ReproductionInputType);

	bool StartVAServerLauncher();

	bool SendFileToVAServer(const FString& RelativeFilename);


	//this closes the connection to the server launcher script, which will quit the VAServer instance
	void ReleaseVAServerLauncherConnection();

	bool IsVAServerLauncherConnected();
	

private:

	bool SendReproductionInputSignalType(const EReproductionInput ReproductionInputType);

	TArray<uint8> ConvertString(const FString& String);
	FString ByteArrayToString(const uint8* In, int32 Count);

	static FString EnumToString(EReproductionInput Enum);


	//Socket connection to the VAServerLauncher, has to be held open until the program ends
	FSocket* VAServerLauncherSocket=nullptr;
};
