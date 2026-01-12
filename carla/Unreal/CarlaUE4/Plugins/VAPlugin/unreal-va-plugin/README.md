# Unreal Virtual Acoustics Plugin

This Plugin allows the user to use the [VA Server](http://www.virtualacoustics.org/) from the [Institute of Acoustics](https://www.akustik.rwth-aachen.de/cms/~dwma/Technische-Akustik/lidx/1/) (ITA) of the RWTH Aachen to playback sounds in Unreal.

## Installation 
If you used the [RWTH VR Project Template](https://devhub.vr.rwth-aachen.de/VR-Group/unreal-development/unrealprojecttemplate) to create your project you can use the setup script to add the Virtual Acoustics Plugin.
Otherwise, add repository as submodule in the "Plugins" folder of your Unreal Engine 4 Project (``git submodule add https://git-ce.rwth-aachen.de/vr-vis/VR-Group/unreal-development/plugins/unreal-va-plugin.git Plugins/VAPlugin``.

Moreover make sure to have the VAServer prepared:

While the VAServer can be used in its original form ([Link](http://www.virtualacoustics.org/)) we highly recommend using the [VAServerLauncher](https://git-ce.rwth-aachen.de/vr-vis/VR-Group/vaserverlauncher) script (Recommended), an especially for this Plugin optimized Python script including a lot of config possibilities and providing VAServer binaries.
Using the [VAServerLauncher](https://git-ce.rwth-aachen.de/vr-vis/VR-Group/vaserverlauncher) has following the advantages:
* You don't need to (re)start the VAServer all the time manually. Even the VAServerLauncher script is (if configured correctly, see below) started automatically by Unreal.
* The VAServerLauncher can transfer used audio files from you Unreal project to the VAServer (even in networked environments), so you don't have to do this manually. Just use audio paths relative to your Content folder. (:warning: when using packaged builds, e.g., in the CAVE, make sure to have the paths where your audio files are packed as nonUFS, so not added to the pak files, this can be configured in the project settings at ``DirectoriesToAlwaysStageAsNonUFS``).
* This copying over is also true for VAServer ini files (e.g., having different acoustical renderers in different scenes), see [VAServerLAuncher documentation](https://git-ce.rwth-aachen.de/vr-vis/VR-Group/VAServerLauncher/-/blob/master/README.md) for more information.

If you are using the automatic VAServerLauncher either have VAServerLauncher cloned next to the folder of your project or specify the VALauncher Path in the Engine/Virtual Acoustics(VA) section of the project settings. 
Make sure to follow the instructions which are currently in [its Readme file](https://git-ce.rwth-aachen.de/vr-vis/VR-Group/VAServerLauncher/-/blob/master/README.md).

The Plugin requires to have the [RWTH VR Toolkit](https://git-ce.rwth-aachen.de/vr-vis/VR-Group/unreal-development/plugins/rwth-vr-toolkit) used in your project.



## Usage 
For a more detailed C++ / Blueprint usage and a Documentation of the Plugins public functions, please check out the matching [wiki page](https://git-ce.rwth-aachen.de/vr-vis/VR-Group/unreal-development/plugins/unreal-va-plugin/-/wikis/home) for each public class: 
* [VAReceiverActor](https://git-ce.rwth-aachen.de/vr-vis/VR-Group/unreal-development/plugins/unreal-va-plugin/-/wikis/Documentation/VAReceiverActor) 
  * Actor handling the Connection and Scene Settings for the current world, as well as the Position updates for the Receiver. If there is no Receiver Actor placed in the Scene, there will be created a new one with Default values at Runtime. 
* [VASoundSourceComponent](https://git-ce.rwth-aachen.de/vr-vis/VR-Group/unreal-development/plugins/unreal-va-plugin/-/wikis/Documentation/VASoundSourceComponent)
  * Actor Component representing a Sound Source. Has to be attatched to something. It can have a graphical representation and reflections, which can be created with the [VAReflectionWall](https://git-ce.rwth-aachen.de/vr-vis/VR-Group/unreal-development/plugins/unreal-va-plugin/-/wikis/Documentation/VAReflectionWall)
