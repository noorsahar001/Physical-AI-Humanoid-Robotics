# ROS 2 Communication: Nodes, Topics, and Services

## Objective
This chapter delves into the core communication mechanisms of ROS 2, focusing on Nodes, Topics, and Services. Understanding these fundamental building blocks is essential for designing and implementing distributed robotic applications, especially for complex humanoid systems where multiple software components must interact seamlessly.

## Nodes: The Workers of ROS 2
In ROS 2, a **node** is an executable process that performs a specific computation. Each node is typically responsible for a single, well-defined task, promoting modularity and reusability. For example, a humanoid robot might have separate nodes for:
*   Reading sensor data (e.g., a camera node, an IMU node)
*   Processing perception data (e.g., an object detection node)
*   Controlling motors (e.g., a joint controller node)
*   Planning movements (e.g., a navigation node)

This modular design allows developers to debug, modify, and replace individual components without affecting the entire robot system. Nodes are isolated processes, communicating over the network, which enhances the robustness and scalability of the robotic system.

## Topics: Asynchronous Data Streaming
**Topics** are the most common way for nodes to exchange data asynchronously in ROS 2. They act as named buses over which messages are published and subscribed.
*   **Publisher**: A node that sends messages to a topic.
*   **Subscriber**: A node that receives messages from a topic.

When a node publishes data to a topic, any node subscribed to that topic will receive the messages. This one-to-many communication model is ideal for continuous data streams like sensor readings (e.g., camera images, LiDAR scans), odometry data, or joint states. The asynchronous nature of topics ensures that nodes can operate independently, processing data at their own rates without blocking other parts of the system. For a humanoid, this means a vision system can continuously publish camera frames while a motor controller subscribes to joint commands, all happening in parallel.

## Services: Synchronous Request/Reply
**Services** provide a synchronous request/reply communication mechanism in ROS 2. Unlike topics, which are for continuous data streams, services are used when a node needs to request a specific action or piece of information from another node and then wait for a response.
*   **Service Server**: A node that offers a service and processes requests.
*   **Service Client**: A node that sends a request to a service server and waits for a reply.

Examples of service usage in humanoid robotics include:
*   A client node requesting a map update from a mapping service server.
*   A client requesting the robot to perform a specific action, like picking up an object, and waiting for confirmation.
*   A client querying the robot's current battery status from a power management service.

Services are crucial for tasks that require a guaranteed response and specific action, ensuring that operations are completed before proceeding with dependent tasks.

## Tools and Software Context
The `ros2` command-line interface is vital for inspecting and interacting with nodes, topics, and services:
*   `ros2 node list`: Lists all active nodes.
*   `ros2 topic list`: Shows all active topics.
*   `ros2 topic echo <topic_name>`: Displays messages being published on a topic.
*   `ros2 service list`: Lists available services.
*   `ros2 service call <service_name> <service_type> <arguments>`: Calls a service.

Python (`rclpy`) and C++ (`rclcpp`) are the primary languages for developing ROS 2 nodes, publishers, subscribers, and service clients/servers.

## Hardware Context
The communication principles of nodes, topics, and services are hardware-agnostic. However, their performance and reliability are directly influenced by the underlying network infrastructure and the computational power of the robot's hardware. Low-latency networks and powerful processing units (e.g., NVIDIA Jetson, workstations) are beneficial for ensuring smooth and responsive communication in complex humanoid robot systems.

Understanding these communication patterns forms the bedrock for building sophisticated and reactive Physical AI applications.
