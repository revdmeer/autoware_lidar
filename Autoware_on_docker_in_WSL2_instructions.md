---
title: Autoware on docker in WSL2 instructions
filters:
  - pandoc-crossref
numbersections: true
autoSectionLabels: True
secPrefix:
  - "section"
  - "sections"
---

# Introduction

This describes the steps to install autoware in Windows Subsystem for Linux 2 (WSL2) and using a modified autoware docker image and run a basic perception pipeline or pre-recorded Velodyne LiDAR ros2 bags.

## Background info
There is a youtube video on autoware perception. But it just launches a demo that is pretty far from what wee need as far as I can see.
<https://www.youtube.com/watch?v=xSGCpb24dhI&list=PLL57Sz4fhxLpCXgN0lvCF7aHAlRA5FoFr&index=9>

Autoware perception documentation:
<https://autowarefoundation.github.io/autoware-documentation/main/tutorials/integrating-autoware/launch-autoware/perception/#overview>


These instructions are partially loosely based on: <https://autowarefoundation.github.io/autoware-documentation/main/installation/autoware/docker-installation/#how-to-set-up-a-workspace>



# Install and configure WSL2 Ubuntu environment

## Install WSL2 / Ubuntu 24
In a powershell do:
```batch
wsl --install
```
Go though all the steps to create user, reboot if needed etc. **And remember the root password you entered, and make sure you can easily enter it**, you'll need it a few times later on for the `sudo` command.

## WSL automount
Make sure **automount** is enabled in WSL. Add the following section to `/etc/wsl.conf`:

```ini
[automount]
enabled=true
root=/mnt/
```

This will give you access to your C drive, including onedrive/sharepoint stuff like e.g.:

```bash
cd /mnt/c/Users/username/
```

This is very usefull for playing ros bags from the Windows filesystem including onedrive/sharepoint.

## increase WSL2 swap size

Compiling autoware is memory intensive. By default WSL2 does not allocate a lot of physical memory and the default swap size is small. This will result in compilation errors that unfortunately are very hard to recognize as being causes by memory shortage.

Therefore is increase swap size on WSL2 by adding this to `C:\Users\<WindowsUser>\.wslconfig:`

```ini
[wsl2]
swap=16GB
```

# Install Docker Desktop

Install the Windows version of Docker Desktop:
<https://www.docker.com/products/docker-desktop/>

## Start Docker Desktop

Start Docker Desktop and keep it running to use it in WSL2. You can do that from the Windows start menu, or within a WSL session with:

```bash
"/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe"
```

# Install autoware using an autoware docker image

## Clone autoware repo from GitHub

Make sure:

- automount is enabled and windows c-drive is mounted in /mnt/c (see @sec:wsl-automount)
- Docker Desktop is installed and running (see @sec:install-docker-desktop and @sec:start-docker-desktop)

Start a Ubuntu jazzy (24) terminal and do:

```bash
sudo apt update
sudo apt install -y git curl python3-vcstool python3-colcon-common-extensions
cd ~
mkdir autoware_data
git clone https://github.com/autowarefoundation/autoware.git
cd autoware

mkdir -p src
vcs import src < repositories/autoware.repos

```

## Modify / configure docker 

edit docker/examples/basic/dev-cpu.compose.yaml :
Make sure to edit the `username` and the rest of that path to make it point to the location you stored your ros2 bags.

```yaml
services:
  autoware:
    image: ghcr.io/autowarefoundation/autoware:universe-devel-jazzy
    privileged: true
    stdin_open: true
    tty: true
    # This is important so multiple instances of the container can see each others ros2 topics
    network_mode: host
    ipc: host
    pid: host
    environment:
      - DISPLAY=${DISPLAY}
      - HOST_UID=${HOST_UID:-1000}
      - HOST_GID=${HOST_GID:-1000}
      - QT_X11_NO_MITSHM=1
      - LIBGL_ALWAYS_SOFTWARE=1
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ${HOME}/autoware_data/maps:/home/aw/autoware_data/maps
      - ${HOME}/autoware_data/ml_models:/home/aw/autoware_data/ml_models
      - ${HOME}/autoware:/home/aw/autoware
      - "/mnt/c/Users/username/HAN/AEA-ES-MES Embedded Control-Minor Project Group 3 - Documents/Shared_data_with_group_3_4:/bags"
    command: bash
```
## Prepare WSL2 Ubuntu session for running autoware docker

Before starting the docker image do this:

```bash
sudo sysctl -w net.core.rmem_max=2147483647
sudo sysctl -w net.core.rmem_default=2147483647
```

This will prevent error like: `ros2: failed to increase socket receive buffer size to at least 10485760 bytes, current is 425984 bytes`

# Start the docker image

```bash
cd autoware
HOST_UID=$(id -u) HOST_GID=$(id -g) \
docker compose -f docker/examples/basic/dev-cpu.compose.yaml \
  run --rm autoware
```

if you build autoware earlier, skip to @sec:setup-autoware

## Build autoware (needed only once){#sec:build-autoware}

Inside the docker image do this once (takes a long time !):
```bash
cd /home/aw/autoware
source /opt/ros/jazzy/setup.bash
sudo apt update
rosdep update
rosdep install -y --from-paths src --ignore-src --rosdistro jazzy
colcon build --symlink-install \
  --parallel-workers 1 \
  --executor sequential \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
```

Result should be something like::
```bash
Summary: 479 packages finished [4h 1min 0s]
```



## Setup environment for ros2 + autoware use{#sec:setup-autoware}

This needs to be entered each time after starting a new docker shell:

```bash
cd /home/aw/autoware
source /opt/ros/jazzy/setup.bash
source install/setup.bash 2>/dev/null || true
```

As a sanity check: make sure this lists autoware_launch:
```bash
ros2 pkg list | grep autoware_launch
```
When this returns `autoware_launch` most likely autoware build properly. If not see @sec:build-autoware.

Another sanity check:
```bash
ros2 pkg list | grep autoware_lidar_centerpoint
```
When this returns `autoware_lidar_centerpoint` most likely autoware build properly. If not see @sec:build-autoware.

## Prepare autoware artifact stuff (needed only once)
Do this once to download / install Autoware's artifact stuff:

Make sure the ~/autoware_data directory is NOT owned by root, but the current user (in this case ronald). To fix this do:

```bash
sudo chown -R ronald autoware_data
sudo chgrp -R ronald autoware_data
```

Do the following to: This will take a while (like > an hour):

```bash
cd ~/autoware

ansible/scripts/install-ansible.sh
ansible-galaxy collection install -f -r ansible-galaxy-requirements.yaml
ansible-playbook autoware.dev_env.install_dev_env --tags artifacts
```


Now that the autoware stuff is all build, in a new shell do:
```bash
cd /home/aw/autoware
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```














At minimum, Autoware must know the transform from LiDAR frame to base_link. If your bag only contains /velodyne_points and no TF, you need to publish a static transform, for example:

```
ros2 run tf2_ros static_transform_publisher \
  0 0 1.8 0 0 0 base_link velodyne
```
 
ros2 bag play rosbag2_2026_04_23-18_07_40_stationary_cart_random_walking_person --clock \
  --remap /velodyne_points:=/sensing/lidar/concatenated/pointcloud_raw	
  
  Or, if your preprocessing expects rectified data:



  











```bash
ros2 bag play /bags/rosbag2_2026_04_23-18_07_40_stationary_cart_random_walking_person
```



# Start the modified autoware perception pipeline{#sec:modified-pipeline}

A heavily modified pipeline is available in a launch file in the `autoware_lidar_perception` package.

Check out the `autoware_lidar_perception/launch/autoware_perception_only.launch.py` file to see all the steps.

Among other this it will:

- Launch autoware with perception only
- Start `velodyne_to_autoware` node in this package to convert Velodyne LiDAR pointclound format from topic `/velodyne_points` to autoware pointcloud format in `/sensing/lidar/concatenated/pointcloud`
- Do some transforms
- Do some relays

Copy the `autoware_lidar_perception` folder to the WSL2 location `~/autoware/`.

## Build package (needed only once)

In the docker image do:

```bash
cd /home/aw/autoware
colcon build --packages-select autoware_lidar_perception
source install/setup.bash
```

## Start launch file in autoware_lidar_perception package

```bash
ros2 launch autoware_lidar_perception autoware_perception_only.launch.py
```

Launching may take a bit of time, but eventually an rvis2 gui should be launched

# Play a ros2 bag

Now that the pipeline from @sec:modified-pipeline is running, we can "feed" it with recorded Velodyne LiDAR data:

Play in a loop e.g.:
```bash
ros2 bag play /bags/rosbag2_2026_04_23-18_07_40_stationary_cart_random_walking_person -l
```
Please note when playing in a loop that the tracking will remember the tracked objects from the end of the previous loop. So don't be surprised if things get messy when looping.

## View tracked objects
Tracked objects with unique ID's are in topic `/perception/object_recognition/tracking/objects`. You can have a look at the raw data with:

```bash 
ros2 topic echo /perception/object_recognition/tracking/objects --once
```
You can also enable this view in the the rvis2 gui.

In rvis2, change view to ThirdPersonView 

# rqt_graph

The `rqt_graph` utility (see <https://wiki.ros.org/rqt_graph>) unfortunately is not included in the docker image.
To use it, you have to install it. And because the docker will be reset at next launch, you need to do this after each docker launch.:

```bash
sudo apt update
sudo apt install ros-${ROS_DISTRO}-rqt-graph
```

I was able to start it with:
```bash
rqt_graph --force-discover
```

