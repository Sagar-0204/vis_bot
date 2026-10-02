import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_description = get_package_share_directory("vis_bot")

    xacro_file = os.path.join(pkg_description, "urdf", "ugv.urdf.xacro")
    rviz_config = os.path.join(pkg_description, "rviz2", "path.rviz")
    world = os.path.join(pkg_description, "world", "sih_field_world.sdf")

    # Path to the models parent folder in install/
    models_dir = os.path.join(pkg_description, "models")

    # Expose model directory to Gazebo
    set_gz_resource_path = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", models_dir
    )

    robot_description_config = xacro.process_file(xacro_file)
    robot_description = {
        "robot_description": robot_description_config.toxml(),
        "use_sim_time": True,
    }

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"),
                "launch",
                "gz_sim.launch.py",
            )
        ),
        launch_arguments={"gz_args": f"-r {world}"}.items(),
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "mobrob" ,"-x", "-4.495",
            "-y", "4.495"],
        output="screen",
    )

    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        output="screen",
        arguments=[
            "/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry",
            "/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
            "/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model",
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",

            # ====== RealSense D435i Camera Bridges ======
            # Gazebo topic: /camera/image_raw/image -> ROS 2: /camera/image_raw
            "/camera/image_raw/image@sensor_msgs/msg/Image[gz.msgs.Image",

            # Gazebo topic: /camera/image_raw/depth_image -> ROS 2: /camera/depth_image
            "/camera/image_raw/depth_image@sensor_msgs/msg/Image[gz.msgs.Image",

            # Gazebo topic: /camera/image_raw/camera_info -> ROS 2: /camera/camera_info
            "/camera/image_raw/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",

            # Gazebo topic: /camera/image_raw/points -> ROS 2: /camera/points
            "/camera/image_raw/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",

            # ====== IMU Bridge ======
            "/camera/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
        ],
        remappings=[
            ("/camera/image_raw/image", "/camera/image_raw"),
            ("/camera/image_raw/depth_image", "/camera/depth_image"),
            ("/camera/image_raw/camera_info", "/camera/camera_info"),
            ("/camera/image_raw/points", "/camera/points"),
        ],
        parameters=[
            {"use_sim_time": True},

        ],
    )
    rviz2 = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": True}],
    )

    return LaunchDescription(
        [
            set_gz_resource_path,  # Must be loaded before Gazebo launches
            robot_state_publisher,
            gazebo,
            spawn_entity,
            ros_gz_bridge,
            rviz2,
        ]
    )