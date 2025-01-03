#!/usr/bin/python3
# Import libraries:
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler, DeclareLaunchArgument, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
import xacro
import yaml

# LOAD FILE:
def load_file(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    try:
        with open(absolute_file_path, 'r') as file:
            return file.read()
    except EnvironmentError:
        # parent of IOError, OSError *and* WindowsError where available.
        return None
# LOAD YAML:
def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    try:
        with open(absolute_file_path, 'r') as file:
            return yaml.safe_load(file)
    except EnvironmentError:
        # parent of IOError, OSError *and* WindowsError where available.
        return None

# ========== **GENERATE LAUNCH DESCRIPTION** ========== #
def generate_launch_description():


    # *********************** Gazebo *********************** # 
    
    # DECLARE Gazebo WORLD file:
    panda_ros2_gazebo = os.path.join(
        get_package_share_directory('panda_ros2_gazebo'),
        'worlds',
        'panda.world')
    # DECLARE Gazebo LAUNCH file:
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('gazebo_ros'), 'launch'), '/gazebo.launch.py']),
                launch_arguments={'world': panda_ros2_gazebo}.items(),
             )
    


    # ========== COMMAND LINE ARGUMENTS ========== #
    print("ros2_RobotSimulation --> PANDA ROBOT")
    print("Launch file -> panda_interface.launch.py")
    print("Robot configuration:")

    print("PANDA ROBOT alone.")
    cell_layout_1 = "true"

    # End-Effector:
    print("End-effector")
    EE_no = "true"
    

    # ***** ROBOT DESCRIPTION ***** #
    # PANDA ROBOT Description file package:
    panda_description_path = os.path.join(
        get_package_share_directory('panda_ros2_gazebo'))
    # FANUC LBR-panda ROBOT urdf file path:
    xacro_file = os.path.join(panda_description_path,
                              'urdf',
                              'panda.urdf.xacro')
    # Generate ROBOT_DESCRIPTION for PANDA ROBOT:
    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc, mappings={
        "cell_layout_1": cell_layout_1,
        "EE_no": EE_no,
        })
    robot_description_config = doc.toxml()
    robot_description = {'robot_description': robot_description_config}

    # SPAWN ROBOT TO GAZEBO:
    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description',
                                   '-entity', 'panda'],
                        output='screen')
    
    spawn_table = Node(
    package='gazebo_ros', 
    executable='spawn_entity.py',
    arguments=[
        '-entity', 'table',
        '-database', 'table',  
        '-x', '0.297058',
        '-y', '0.841397',
        '-z', '-0.394127'
    ],
    output='screen'
    )

    spawn_coke_can = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'coke_can',
            '-database', 'coke_can',
            '-x', '0.208586',
            '-y', '0.756959',
            '-z', '0.617540',
            '-R', '0.024772',
            '-P', '-0.013618',
            '-Y', '0.000515'
        ],
        output='screen'
    )

    # Camera nodes
    spawn_camera1 = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-file', os.path.join(get_package_share_directory('ros2_data'), 'urdf', 'camera1.urdf'),
            '-entity', 'camera1',
            '-x', '0.75',
            '-y', '1.8',
            '-z', '1.0',
            '-R', '-0.5',
            '-P', '0.0',
            '-Y', '-2.356',
            '-reference_frame', 'world'
        ],
    
        output='screen'
    )

    spawn_camera2 = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-file', os.path.join(get_package_share_directory('ros2_data'), 'urdf', 'camera2.urdf'),
            '-entity', 'camera2',
            '-x', '-0.75',
            '-y', '0.4',
            '-z', '1.0',
            '-R', '-0.5',
            '-P', '0.0',
            '-Y', '0.785'
        ],
        output='screen'
    )

    camera_tf = Node(
    package="tf2_ros",
    executable="static_transform_publisher",
    name="camera_tf",
    arguments=["0.75", "1.8", "1.0", "-0.5", "0.0", "-2.356", "world", "camera_link"]
    )
    
    camers_tf2 = Node(
    package="tf2_ros",
    executable="static_transform_publisher",
    name="camera_tf2",
    arguments=["-0.75", "0.4", "1.0", "-0.5", "0.0", "0.785", "world", "camera_link2"]
    )



  

    # ***** STATIC TRANSFORM ***** #
    # NODE -> Static TF:
    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        output="log",
        arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "base_link"],
    )
    # Publish TF:
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[
            robot_description,
            {"use_sim_time": True},
        ]
    )

    tf_buffer_server = Node(
        package='tf2_ros',
        executable='buffer_server',
        parameters=[
            {'use_sim_time': True},
            {'buffer_size': 120.0}
        ]
    )



    # ***** ROS2_CONTROL -> LOAD CONTROLLERS ***** #

    # Joint STATE BROADCASTER:
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )
    # Joint TRAJECTORY Controller:
    joint_trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["panda_arm_controller", "-c", "/controller_manager"],
    )
    
    # === Panda HAND === #
    panda_handleft_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["panda_handleft_controller", "-c", "/controller_manager"],
    )
    panda_handright_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["panda_handright_controller", "-c", "/controller_manager"],
    )


    # *********************** MoveIt!2 *********************** #   
    
    # Command-line argument: RVIZ file?
    rviz_arg = DeclareLaunchArgument(
        "rviz_file", default_value="True", description="Load RVIZ file."
    )

    # *** PLANNING CONTEXT *** #
    # Robot description, SRDF:
    robot_description_semantic_config = load_file("panda_ros2_moveit2", "config/panda.srdf")
    robot_description_semantic = {"robot_description_semantic": robot_description_semantic_config }
    
    # Kinematics.yaml file:
    kinematics_yaml = load_yaml("panda_ros2_moveit2", "config/kinematics.yaml")
    robot_description_kinematics = {"robot_description_kinematics": kinematics_yaml}

    # Move group: OMPL Planning.
    ompl_planning_pipeline_config = {
        "move_group": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
            "request_adapters": """default_planner_request_adapters/AddTimeOptimalParameterization default_planner_request_adapters/FixWorkspaceBounds default_planner_request_adapters/FixStartStateBounds default_planner_request_adapters/FixStartStateCollision default_planner_request_adapters/FixStartStatePathConstraints""",
            "start_state_max_bounds_error": 0.1,
        }
    }
    ompl_planning_yaml = load_yaml("panda_ros2_moveit2", "config/ompl_planning.yaml")
    ompl_planning_pipeline_config["move_group"].update(ompl_planning_yaml)

    # MoveIt!2 Controllers:
    moveit_simple_controllers_yaml = load_yaml("panda_ros2_moveit2", "config/panda_controllers.yaml")
    moveit_controllers = {
        "moveit_simple_controller_manager": moveit_simple_controllers_yaml,
        "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager",
    }
    trajectory_execution = {
        "moveit_manage_controllers": True,
        "trajectory_execution.allowed_execution_duration_scaling": 1.2,
        "trajectory_execution.allowed_goal_duration_margin": 0.5,
        "trajectory_execution.allowed_start_tolerance": 0.01,
    }
    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
    }

    # START NODE -> MOVE GROUP:
    run_move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            ompl_planning_pipeline_config,
            trajectory_execution,
            moveit_controllers,
            planning_scene_monitor_parameters,
            {"use_sim_time": True}, 
        ],
    )

    # RVIZ:
    load_RVIZfile = LaunchConfiguration("rviz_file")
    rviz_base = os.path.join(get_package_share_directory("panda_ros2_moveit2"), "config")
    rviz_full_config = os.path.join(rviz_base, "panda_moveit2.rviz")
    rviz_node_full = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_full_config],
        parameters=[
            robot_description,
            robot_description_semantic,
            ompl_planning_pipeline_config,
            kinematics_yaml,
            {"use_sim_time": True}, 
        ],
        condition=UnlessCondition(load_RVIZfile),
    )


    # *********************** ROS2.0 Robot/End-Effector Actions/Triggers *********************** #
    # MoveJ ACTION:
    moveJ_interface = Node(
        name="moveJs_action",
        package="ros2_actions",
        executable="moveJs_action",
        output="screen",
        parameters=[robot_description, robot_description_semantic, kinematics_yaml, {"use_sim_time": True}, {"ROB_PARAM": 'panda_arm'}],
    )
    # MoveG ACTION:
    moveG_interface = Node(
        name="moveG_action",
        package="ros2_actions",
        executable="moveG_action",
        output="screen",
        parameters=[robot_description, robot_description_semantic, kinematics_yaml, {"use_sim_time": True}, {"ROB_PARAM": 'panda_gripper'}],
    )
    # MoveXYZW ACTION:
    moveXYZW_interface = Node(
        name="moveXYZW_action",
        package="ros2_actions",
        executable="moveXYZW_action",
        output="screen",
        parameters=[robot_description, robot_description_semantic, kinematics_yaml, {"use_sim_time": True}, {"ROB_PARAM": 'panda_arm'}],
    )
    # MoveL ACTION:
    moveL_interface = Node(
        name="moveL_action",
        package="ros2_actions",
        executable="moveL_action",
        output="screen",
        parameters=[robot_description, robot_description_semantic, kinematics_yaml, {"use_sim_time": True}, {"ROB_PARAM": 'panda_arm'}],
    )
    # MoveR ACTION:
    moveR_interface = Node(
        name="moveRs_action",
        package="ros2_actions",
        executable="moveRs_action",
        output="screen",
        parameters=[robot_description, robot_description_semantic, kinematics_yaml, {"use_sim_time": True}, {"ROB_PARAM": 'panda_arm'}],
    )
    # MoveXYZ ACTION:
    moveXYZ_interface = Node(
        name="moveXYZ_action",
        package="ros2_actions",
        executable="moveXYZ_action",
        output="screen",
        parameters=[robot_description, robot_description_semantic, kinematics_yaml, {"use_sim_time": True}, {"ROB_PARAM": 'panda_arm'}],
    )
    # MoveYPR ACTION:
    moveYPR_interface = Node(
        name="moveYPR_action",
        package="ros2_actions",
        executable="moveYPR_action",
        output="screen",
        parameters=[robot_description, robot_description_semantic, kinematics_yaml, {"use_sim_time": True}, {"ROB_PARAM": 'panda_arm'}],
    )
    # MoveROT ACTION:
    moveROT_interface = Node(
        name="moveROT_action",
        package="ros2_actions",
        executable="moveROT_action",
        output="screen",
        parameters=[robot_description, robot_description_semantic, kinematics_yaml, {"use_sim_time": True}, {"ROB_PARAM": 'panda_arm'}],
    )
    # MoveRP ACTION:
    moveRP_interface = Node(
        name="moveRP_action",
        package="ros2_actions",
        executable="moveRP_action",
        output="screen",
        parameters=[robot_description, robot_description_semantic, kinematics_yaml, {"use_sim_time": True}, {"ROB_PARAM": 'panda_arm'}],
    )

    Attacher = Node(
        name="ATTACHER_action",
        package="ros2_data",
        executable="attacher_action.py",
        output="screen",
    )

    
    
    return LaunchDescription(
        [
            # Gazebo nodes:
            gazebo, 
            spawn_entity,
    
            # ROS2_CONTROL:
            static_tf,
            robot_state_publisher,
            spawn_table,
            spawn_coke_can,
            spawn_camera1,
            spawn_camera2,
            camera_tf,
            camers_tf2,
            
          
            # ROS2 Controllers:
            RegisterEventHandler(
                OnProcessExit(
                    target_action = spawn_entity,
                    on_exit = [
                        joint_state_broadcaster_spawner,
                    ]
                )
            ),
            RegisterEventHandler(
                OnProcessExit(
                    target_action = joint_state_broadcaster_spawner,
                    on_exit = [
                        joint_trajectory_controller_spawner,
                    ]
                )
            ),
            RegisterEventHandler(
                OnProcessExit(
                    target_action = joint_trajectory_controller_spawner,
                    on_exit = [
                        panda_handleft_controller_spawner,
                    ]
                )
            ),
            RegisterEventHandler(
                OnProcessExit(
                    target_action = panda_handleft_controller_spawner,
                    on_exit = [
                        panda_handright_controller_spawner,
                    ]
                )
            ),

            RegisterEventHandler(
                OnProcessExit(
                    target_action = panda_handright_controller_spawner,
                    on_exit = [

                        # MoveIt!2:
                        TimerAction(
                            period=5.0,
                            actions=[
                                rviz_arg,
                                rviz_node_full,
                                run_move_group_node
                            ]
                        ),

                        # ROS2.0 Actions:
                        TimerAction(
                            period=2.0,
                            actions=[
                                moveJ_interface,
                                moveG_interface,
                                moveL_interface,
                                moveR_interface,
                                moveXYZ_interface,
                                moveXYZW_interface,
                                moveYPR_interface,
                                moveROT_interface,
                                moveRP_interface,
                                Attacher,
                            ]
                        ),

                    ]
                )
            )
        ]
    )