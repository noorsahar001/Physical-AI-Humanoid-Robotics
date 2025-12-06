module.exports = {
  tutorialSidebar: [
    {
      type: "category",
      label: "Module 1: ROS2 Fundamentals",
      items: [
        "module1-ros2/ros2-fundamentals",
        "module1-ros2/ros2-nodes-topics-services",
        "module1-ros2/urdf-for-humanoids",
        "module1-ros2/python-agents-ros-controllers-rclpy",
      ],
    },

    {
      type: "category",
      label: "Module 2: Digital Twin & Simulation",
      items: [
        "module2-digital-twin/gazebo-physics-simulation",
        "module2-digital-twin/sensor-simulation",
        "module2-digital-twin/environment-human-robot-interaction",
        "module2-digital-twin/unity-visualization-rendering",
      ],
    },

    {
      type: "category",
      label: "Module 3: Navigation & Isaac",
      items: [
        "module3-nvidia-isaac/navigation-path-planning-nav2",
        "module3-nvidia-isaac/nvidia-isaac-sim-overview",
        "module3-nvidia-isaac/perception-vslam-pipelines",
        "module3-nvidia-isaac/reinforcement-learning-for-humanoid-control",
      ],
    },

    {
      type: "category",
      label: "Module 4: VLA & Cognitive Models",
      items: [
        "module4-vla/cognitive-planning-llms",
        "module4-vla/vla-pipeline-integration",
        "module4-vla/voice-to-action-whisper",
      ],
    },

    {
      type: "category",
      label: "Capstone Project",
      items: [
        "capstone-project/command-interpretation-workflow",
      ],
    },
  ],
};
