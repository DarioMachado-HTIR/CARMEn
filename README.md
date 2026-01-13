# CARMEn: An Immersive Multi-Agent XR Framework for Urban Mobility Simulation 

## Description

CARMEn is an open-source immersive road environment simulation framework designed to support advanced research in urban mobility and transportation, with a particular focus on scenarios involving interactions between drivers and pedestrians. By combining extended reality (XR), multi-agent networking, and realistic spatial audio, CARMEn enables controlled, repeatable, and safe experimentation within complex virtual environments that closely resemble real-world urban settings. 

The framework is built on top of the CARLA open-source driving simulator and Unreal Engine, leveraging their strengths while extending their capabilities to support immersive human-in-the-loop experimentation. CARMEn employs a modular architecture in which Unreal Engine is responsible for audiovisual rendering, including XR visualization and acoustic simulation, while CARLA’s Python API manages simulation logic such as ego vehicle control, traffic behavior, pedestrian agents, and scenario configuration. 

A core feature of CARMEn is its networked multi-agent functionality. Using Unreal Engine’s native multiplayer replication system, multiple agents - drivers, pedestrians, and spectators - can coexist and interact within the same virtual environment, each running on a separate workstation. The framework follows a client-server model, where one instance operates as a listen-server hosting the simulation, and other instances join as clients. Simulation control commands issued via the Python API are routed to the server and replicated across all connected clients, ensuring consistency of the simulation state. This architecture is both operating system–agnostic and role-agnostic, allowing Windows and Linux instances to participate in the same session. 

CARMEn further integrates augmented virtuality to enhance immersion for driver agents. Using an XR head-mounted display, the OpenXR API and the SteamVR runtimes, the framework merges real-world elements, such as the driver’s hands and physical steering wheel, into a high-fidelity virtual cockpit. A physical driving rig equipped with a steering wheel, pedals, and a green-screen panel enables chroma keying and masking techniques to isolate real objects and seamlessly blend them with the virtual environment. The virtual cockpit includes a remodeled vehicle interior, dynamic instrumentation displaying real-time vehicle data, and rear-view mirrors implemented via virtual cameras. 

To complement the visual immersion, CARMEn incorporates realistic acoustic simulation using Unreal Engine’s Steam Audio plugin. The system simulates a dynamic virtual acoustic environment with physics-based sound propagation, including attenuation, occlusion, and reflections based on scene geometry and material properties. Binaural rendering is applied to produce accurate spatial audio for each agent’s point of view. Environmental sounds, vehicle engine and tire noise, and ambisonic background ambience contribute to a coherent auditory scene, while audio filtering inside the vehicle simulates the acoustic characteristics of a real cockpit.

## Licenses

CARMEn specific code is distributed under MIT License.

CARMEn specific assets are distributed under CC-BY License.

### CARMEN Dependency and Integration licenses

CARMEn uses CARLA as its foundation:
- CARLA follows MIT ( Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB) ) and CC-BY License. 
- CARLA Licences Dependecies and Integration follow the licences defined in its own README [https://github.com/carla-simulator/carla/blob/master/README.md].

CARLA was developed and is meing mantained by the Computer Vision Centre and the Embodied AI Foundation.

[Homepage](http://carla.org)

[Paper](http://proceedings.mlr.press/v78/dosovitskiy17a/dosovitskiy17a.pdf)

Unreal Engine 4 follows its [own license terms](https://www.unrealengine.com/en-US/faq).

CARMEN uses on dependecy as part of its GUI integration:
- [PyGameWidgets](https://github.com/EricsonWillians/PyGameWidgets), a straightforward widget toolkit for Pygame, whihc uses the [GPL-3.0 license](http://fsf.org/)
