#include "VAServerLauncher.h"

#include <string>

#include "Misc/FileHelper.h"
#include "SocketSubsystem.h"
#include "GeneralProjectSettings.h"

#include "Utility/VirtualRealityUtilities.h"

#include "VAUtils.h"
#include "VASettings.h"
#include "VAPlugin.h"
#include "HAL/FileManagerGeneric.h"


bool FVAServerLauncher::RemoteStartVAServer(const FString& Host, const int Port, const FString& VersionName, const FString& VARendererIniFile, const EReproductionInput ReproductionInputType)
{
	if (!UVirtualRealityUtilities::IsMaster())
	{
		return false;
	}

	if (VAServerLauncherSocket != nullptr)
	{
		return true;
	}

	FVAUtils::LogStuff("[FVAServerLauncher::RemoteStartVAServer()]: Try to remotely start the VAServer at address " + 
		Host + ":" + FString::FromInt(Port) + " for version: " + VersionName, false);


	//Connect
	const FString SocketName(TEXT("VAServerStarterConnection"));
	VAServerLauncherSocket = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateSocket(
		NAME_Stream, SocketName, false);

	TSharedPtr<FInternetAddr> InternetAddress = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateInternetAddr();

	bool bValidIP;
	InternetAddress->SetIp(*Host, bValidIP);
	InternetAddress->SetPort(Port);

	if (!bValidIP)
	{
		FVAUtils::LogStuff("[FVAServerLauncher::RemoteStartVAServer()]: The Ip cannot be parsed!", true);
		return false;
	}

	if (VAServerLauncherSocket == nullptr || !VAServerLauncherSocket->Connect(*InternetAddress))
	{
		FVAUtils::LogStuff("[FVAServerLauncher::RemoteStartVAServer()]: Cannot connect to Launcher!", true);
		return false;
	}
	FVAUtils::LogStuff("[FVAServerLauncher::RemoteStartVAServer()]: Successfully connected to Launcher", false);

	const bool bSendVARendererIni = !VARendererIniFile.IsEmpty();
	if (bSendVARendererIni)
	{
		if (!SendFileToVAServer(VARendererIniFile))
		{
			FVAUtils::OpenMessageBox("[FVAServerLauncher::RemoteStartVAServer()]: VARenderer.ini file '" + VARendererIniFile +
				"' could not be copied to VAServerLauncher. Does the file exist? See error log for additional info. VAServerLauncher will run with default settings.", true);
		}
	}


	if (!SendReproductionInputSignalType(ReproductionInputType))
	{
		FVAUtils::OpenMessageBox("[FVAServerLauncher::RemoteStartVAServer()]: ReproductionInputType '" + EnumToString(ReproductionInputType) +
			"' could not be sent to VAServerLauncher. See error log for additional info. VAServerLauncher will run with default settings.", true);
	}


	//Send requested version
	TArray<uint8> RequestData = ConvertString(VersionName);
	int BytesSend = 0;
	VAServerLauncherSocket->Send(RequestData.GetData(), RequestData.Num(), BytesSend);
	FVAUtils::LogStuff("[FVAServerLauncher::RemoteStartVAServer()]: Send " + FString::FromInt(BytesSend) + 
		" bytes to the VAServerLauncher, with version name: " + VersionName + " Waiting for answer.", false);

	//Receive response
	const int32 BufferSize = 16;
	int32 BytesRead = 0;
	uint8 Response[16];
	if (VAServerLauncherSocket->Recv(Response, BufferSize, BytesRead) && BytesRead == 1)
	{
		switch (Response[0])
		{
		case 'g':
			FVAUtils::LogStuff("[FVAServerLauncher::RemoteStartVAServer()]: Received go from launcher, VAServer seems to be correctly started.", false);
			break;
		case 'n':
			FVAUtils::OpenMessageBox("[FVAServerLauncher::RemoteStartVAServer()]: VAServer cannot be launched, invalid VAServer binary file or cannot be found",
			                        true);
			VAServerLauncherSocket = nullptr;
			return false;
		case 'i':
			FVAUtils::OpenMessageBox("[FVAServerLauncher::RemoteStartVAServer()]: VAServer cannot be launched, invalid file entry in the config", true);
			VAServerLauncherSocket = nullptr;
			return false;
		case 'a':
			FVAUtils::OpenMessageBox("[FVAServerLauncher::RemoteStartVAServer()]: VAServer was aborted", true);
			VAServerLauncherSocket = nullptr;
			return false;
		case 'f':
			FVAUtils::OpenMessageBox("[FVAServerLauncher::RemoteStartVAServer()]: VAServer cannot be launched, requested version \"" + 
				VersionName + "\" is not available/specified", true);
			VAServerLauncherSocket = nullptr;
			return false;
		default:
			FVAUtils::OpenMessageBox("[FVAServerLauncher::RemoteStartVAServer()]: Unexpected response from VAServerLauncher: " + 
				FString(reinterpret_cast<char*>(&Response[0])), true);
			VAServerLauncherSocket = nullptr;
			return false;
		}
	}
	else
	{
		FVAUtils::LogStuff("[FVAServerLauncher::RemoteStartVAServer()]: Error while receiving response from VAServerLauncher", true);
		VAServerLauncherSocket = nullptr;
		return false;
	}

	return true;
}

bool FVAServerLauncher::StartVAServerLauncher()
{
  //check whether we can also start the VSServer Launcher python script.

	if (!UVirtualRealityUtilities::IsMaster())
	{
		return false;
	}

  const UVASettings* Settings = GetDefault<UVASettings>();
  FString LauncherScriptDir = Settings->VALauncherPath;

  if(FPaths::IsRelative(LauncherScriptDir))
  {
    FString ProjectDir = FPaths::ProjectDir();
    ProjectDir = IFileManager::Get().ConvertToAbsolutePathForExternalAppForRead(*ProjectDir);
    LauncherScriptDir = FPaths::ConvertRelativePathToFull(ProjectDir, LauncherScriptDir);
  }

  LauncherScriptDir = FPaths::Combine(LauncherScriptDir, TEXT("LaunchScript"));
  FString LauncherScript = TEXT("VirtualAcousticsStarterServer.py");
  if (FPaths::FileExists(FPaths::Combine(LauncherScriptDir, LauncherScript)))
  {
		FString CMDCommand = "cd/d " + LauncherScriptDir + " & ";

		//check whether py or python exist
		auto DoesCommandExist = [&](FString Command)
		{
			//this checks whether a given command returns a result
			FString TmpCmdResultFile = "tmpPyVersion.txt";
			TmpCmdResultFile = FPaths::Combine(LauncherScriptDir, TmpCmdResultFile);
			Command = Command + " >> \"" + TmpCmdResultFile + "\"";
			system(TCHAR_TO_ANSI(*Command));
			FString Result;
			FFileHelper::LoadFileToString(Result, *TmpCmdResultFile);
			IFileManager::Get().Delete(*TmpCmdResultFile);
			return !Result.IsEmpty();
		};

		bool bPyExists = DoesCommandExist("py --version");
		bool bPythonExists = DoesCommandExist("python --version");

		if(bPythonExists || bPyExists)
		{
			FString Command = CMDCommand + "start " + (bPythonExists?"python":"py") + " " + LauncherScript;
			system(TCHAR_TO_ANSI(*Command));
			return true;
		}
		else
		{
			FVAUtils::OpenMessageBox("VA Launcher cannot be started since neither \"py\" nor \"python\" can be found. If it is installed add it to PATH (and restart Visual Studio)", true);
			return false;
		}
  }
  else
  {
    FVAUtils::LogStuff("[FVAServerLauncher::StartVAServerLauncher] Unable to automatically start the launcher script, looked for "+LauncherScript+" at "+LauncherScriptDir+". If you want to use this convenience function change the VALauncher Path in the Engine/Virtual Acoustics(VA) section of the project settings. However, nothing bad will happen without.");
  }
  return false;
}

bool FVAServerLauncher::SendFileToVAServer(const FString& RelativeFilename)
{

	if (!UVirtualRealityUtilities::IsMaster())
	{
		return false;
	}
	
	if(VAServerLauncherSocket==nullptr)
	{
		FVAUtils::LogStuff("[FVAServerLauncher::SendFileToVAServer()]: No connection to VAServer Starter, so no files can be send to VAServer!", true);
		return false;
	}

	if(!GetDefault<UVASettings>()->VALauncherCopyFiles)
	{
		FVAUtils::LogStuff("[FVAServerLauncher::SendFileToVAServer()]: Setting to not send files over the network to VAServer is set, so not sending anything!", false);
		return false;
	}

	if(!FPaths::FileExists(FPaths::Combine(FPaths::ProjectContentDir(),RelativeFilename)))
	{
		FVAUtils::LogStuff("[FVAServerLauncher::SendFileToVAServer()]: File to send("+RelativeFilename+") could not be found and therefore not send!", true);
		return false;
	}

	TArray<uint8> FileBinaryArray;
	FFileHelper::LoadFileToArray(FileBinaryArray, *FPaths::Combine(FPaths::ProjectContentDir(),RelativeFilename));
	FString FullPath = FPaths::Combine(FPaths::ProjectContentDir(), RelativeFilename);
	const TCHAR* charFilePath = *FullPath;
	FFileManagerGeneric fm;
	FDateTime LastModification = fm.GetTimeStamp(charFilePath);

	const FString ProjectName = GetDefault<UGeneralProjectSettings>()->ProjectName;
	FString MetaInfo = "file:"
			+RelativeFilename+":"
			+FString::FromInt(FileBinaryArray.Num())+":"
			+ProjectName+":"
			+FString::FromInt(LastModification.ToUnixTimestamp());
	TArray<uint8> MetaInfoBinary = ConvertString(MetaInfo);

	int32 BytesSend;
	VAServerLauncherSocket->Send(MetaInfoBinary.GetData(), MetaInfoBinary.Num(), BytesSend);
	//Receive response
	const int32 BufferSize = 128;
	int32 BytesRead = 0;
	uint8 Response[16];
	if (VAServerLauncherSocket->Recv(Response, BufferSize, BytesRead))
	{
		FString ResponseString = ByteArrayToString(Response, BytesRead);
		if(ResponseString=="ack"){
			//VAServer waits for file
			int32 BytesAlreadySend = 0;
			while(BytesAlreadySend<FileBinaryArray.Num())
			{
				//send 1024 byte packages
				int32 BytesToSend = (FileBinaryArray.Num()-BytesAlreadySend>1024?1024:FileBinaryArray.Num()-BytesAlreadySend);
				VAServerLauncherSocket->Send(&FileBinaryArray[BytesAlreadySend],BytesToSend, BytesSend);
				BytesAlreadySend += BytesSend;
			}
			FVAUtils::LogStuff("[FVAServerLauncher::SendFileToVAServer()]: Entire file ("+RelativeFilename+") send!", false);
			VAServerLauncherSocket->Recv(Response, BufferSize, BytesRead);
			ResponseString = ByteArrayToString(Response, BytesRead);
			if(ResponseString == "ack")
			{
				FVAUtils::LogStuff("[FVAServerLauncher::SendFileToVAServer()]: File was received by VAServerLauncher successfully!", false);
				//the search path is added potenitally multiple times, but can only be added once the folder is created (which the above guarantees)
				const std::string SearchPath = "../tmp/" + std::string(TCHAR_TO_UTF8(*GetDefault<UGeneralProjectSettings>()->ProjectName));
				FVAPlugin::AddVAServerSearchPath(SearchPath);
			}
			else
			{
				FVAUtils::LogStuff("[FVAServerLauncher::SendFileToVAServer()]: File was NOT received by VAServerLauncher!", true);
				return false;
			}
		}
		else if (ResponseString=="exists"){
			FVAUtils::LogStuff("[FVAServerLauncher::SendFileToVAServer()]: File already exists with same size, no need ro re-send!", false);
		}
		else
		{
			FVAUtils::LogStuff("[FVAServerLauncher::SendFileToVAServer()]: Server Launcher does not want to receive a file, answer: "+ResponseString, true);
			return false;	
		}
	}
	else
	{
		FVAUtils::LogStuff("[FVAServerLauncher::SendFileToVAServer()]: Server Launcher does not want to receive a file, no answer!", true);
		return false;	
	}

	//the search path is added in any case once after connecting to a new server

	return true;
}

void FVAServerLauncher::ReleaseVAServerLauncherConnection()
{
	if (!UVirtualRealityUtilities::IsMaster())
	{
		return;
	}

	if(VAServerLauncherSocket!=nullptr){
		VAServerLauncherSocket->Close();
		VAServerLauncherSocket = nullptr;
	}
}

bool FVAServerLauncher::IsVAServerLauncherConnected()
{
	return VAServerLauncherSocket!=nullptr;
}

bool FVAServerLauncher::SendReproductionInputSignalType(const EReproductionInput ReproductionInputType)
{
	const FString ProjectName = GetDefault<UGeneralProjectSettings>()->ProjectName;
	FString CommandMsg = "reproduction_input_type:" + EnumToString(ReproductionInputType);
	TArray<uint8> CommandMsgBinary = ConvertString(CommandMsg);

	int32 BytesSend;
	VAServerLauncherSocket->Send(CommandMsgBinary.GetData(), CommandMsgBinary.Num(), BytesSend);

	const int32 BufferSize = 16;
	int32 BytesRead = 0;
	uint8 Response[16];
	if (VAServerLauncherSocket->Recv(Response, BufferSize, BytesRead))
	{
		FString ResponseString = ByteArrayToString(Response, BytesRead);
		if (ResponseString == "ack")
		{
			FVAUtils::LogStuff("[FVAServerLauncher::SendReproductionInputSignalType()]: ReproductionInputType was successfully received by VAServerLauncher!", false);
			return true;
		}
		FVAUtils::LogStuff("[FVAServerLauncher::SendReproductionInputSignalType()]: ReproductionInputType not accepted by VAServerLauncher! Answer: " + ResponseString, false);
		return false;
	}
	FVAUtils::LogStuff("[FVAServerLauncher::SendReproductionInputSignalType()]: VAServerLauncher did not answer!", true);
	return false;
}

TArray<uint8> FVAServerLauncher::ConvertString(const FString& String)
{
	TArray<uint8> RequestData;
	for (TCHAR Character : String.GetCharArray())
	{
		const uint8 InByte = static_cast<uint8>(Character);
		if (InByte != 0)
		{
			RequestData.Add(static_cast<uint8>(Character));
		}
	}
	return RequestData;
}

FString FVAServerLauncher::ByteArrayToString(const uint8* In, int32 Count)
{
	FString Result;
	Result.Empty(Count);

	while (Count)
	{
		// Put the byte into an int16
		int16 Value = *In;

		Result += TCHAR(Value);

		++In;
		Count--;
	}
	return Result;
}

FString FVAServerLauncher::EnumToString(EReproductionInput Enum)
{
	switch (Enum)
	{
	case EReproductionInput::Binaural:
		return TEXT("binaural");
	case EReproductionInput::Ambisonics:
		return TEXT("ambisonics");
	case EReproductionInput::Custom:
		return TEXT("custom");
	default:
		return TEXT("invalid");
	}

}
