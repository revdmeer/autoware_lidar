from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        ExecuteProcess(
            cmd=[
                "ros2", "launch", "autoware_launch", "autoware.launch.xml",
                "map_path:=/home/aw/autoware_data/maps",
                "vehicle_model:=sample_vehicle",
                "sensor_model:=sample_sensor_kit",
                "perception_mode:=lidar",
                "lidar_detection_model:=centerpoint",
                "launch_sensing:=false",
                "launch_localization:=false",
                "launch_perception:=true",
                "launch_planning:=false",
                "launch_control:=false",
                "launch_system:=false",
                "use_pointcloud_map:=false",
                "use_vector_map:=false",
                "use_object_filter:=false",
                "use_object_validator:=false",
                "use_cuda_ground_segmentation:=false",
                "cuda_ground_segmentation_node_param_path:=/home/aw/autoware/install/autoware_ground_segmentation/share/autoware_ground_segmentation/config/scan_ground_filter.param.yaml",
            ],
            output="screen",
        ),

        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="base_link_to_velodyne_tf",
            arguments=["0", "0", "1.8", "0", "0", "0", "base_link", "velodyne"],
            output="screen",
        ),

        Node(
            package="autoware_lidar_perception",
            executable="velodyne_to_autoware",
            name="velodyne_to_autoware",
            output="screen",
        ),
        
        Node(
            package="topic_tools",
            executable="relay",
            name="relay_obstacle_segmentation_pointcloud",
            arguments=[
                "/perception/obstacle_segmentation/single_frame/pointcloud",
                "/perception/obstacle_segmentation/pointcloud",
            ],
            output="screen",
        ),

        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="map_to_base_link_tf",
            arguments=["0", "0", "0", "0", "0", "0", "map", "base_link"],
            output="screen",
        ),

        Node(
            package="topic_tools",
            executable="relay",
            name="relay_clustering_objects",
            arguments=[
                "/perception/object_recognition/detection/clustering/objects",
                "/perception/object_recognition/detection/objects",
            ],
            output="screen",
        ),
        Node(
            package="topic_tools",
            executable="relay",
            name="relay_clustering_detections",
            arguments=[
                "/perception/object_recognition/detection/clustering/objects",
                "/perception/object_recognition/detection/centerpoint/objects",
            ],
            output="screen",
        ),
    ])
