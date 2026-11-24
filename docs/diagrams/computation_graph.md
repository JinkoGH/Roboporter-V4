Vscode and github fails to render mermiad graph properly. Use https://mermaid.live/edit

```mermaid
---
title: Hardware-Bounded ROS 2 Computation Graph
---
flowchart TB
    subgraph PC ["Operator PC (Remote Base Station)"]
        subgraph Services ["ROS 2 Service Interfaces"]
            srv_toggle_scan(["/toggle_scan"])
            srv_reset_failsafe(["/reset_failsafe"])
            srv_op_mode(["/set_operation_mode"])
            srv_reset_odom(["/reset_odometry"])
            srv_calibrate(["/calibrate_encoders"])
        end
        subgraph PC_Nodes ["User Nodes & UI"]
            joy_node["joy_node"]
            teleop_node["teleop_twist_joy_node"]
            foxglove_studio["Foxglove Studio (Diagnostic UI)"]
        end
    end

    subgraph Robot ["Onboard Robot Physical System"]
        subgraph RPi ["Raspberry Pi 4B (ROS 2 Host System)"]
            subgraph DriverLayer ["Sensor Driver Layer"]
                rplidar_node["rplidar_node"]
                ultrasonic_node["ultrasonic_driver_node"]
            end

            subgraph SafetyLayer ["Safety & Arbitration Layer"]
                watchdog_node["watchdog_node"]
                cmd_vel_mux["cmd_vel_mux"]
            end

            subgraph BridgeLayer ["Microcontroller Bridge Layer"]
                arduino_bridge["arduino_bridge_node"]
            end

            subgraph TelemetryLayer ["Telemetry Gateway"]
                foxglove_bridge["foxglove_bridge"]
            end
        end

        subgraph Control ["Control Subsystem & Hardware"]
            subgraph MCU ["Arduino Mega 2560 R3"]
                embedded_loop["embedded_control_loop"]
            end

            subgraph Hardware ["Drive & Feedback Hardware"]
                escs["Mtronics Viper Marine 15A ESCs"]
                encoders["HEDS-5500 Encoders"]
            end
        end
    end

    %% Internal Operator PC Topic
    joy_node -->|"/joy [sensor_msgs/Joy]"| teleop_node

    %% Network Boundary (Wi-Fi DDS)
    teleop_node -.->|"/teleop_cmd_vel<br>(Wi-Fi DDS)"| cmd_vel_mux

    %% Safety Layer Topics & Services
    watchdog_node -->|"/failsafe_cmd_vel"| cmd_vel_mux
    watchdog_node -->|"/sys_health"| TelemetryLayer
    srv_reset_failsafe -.->|"Service Request"| watchdog_node
    srv_op_mode -.->|"Service Request"| cmd_vel_mux

    %% Arbitrated Command Stream
    cmd_vel_mux -->|"/cmd_vel"| BridgeLayer

    %% Sensor Driver Streams & Services
    rplidar_node -->|"/scan"| TelemetryLayer
    ultrasonic_node -->|"/ultrasonic/ranges"| watchdog_node
    srv_toggle_scan -.->|"Service Request"| rplidar_node

    %% Microcontroller Bridge Streams & Services
    BridgeLayer -->|"/odom"| TelemetryLayer
    BridgeLayer -->|"/battery_status"| watchdog_node
    srv_reset_odom -.->|"Service Request"| BridgeLayer
    srv_calibrate -.->|"Service Request"| BridgeLayer

    %% Telemetry WebSocket Stream (Wi-Fi)
    TelemetryLayer -.->|"WebSocket Stream<br>ws://<rpi_ip>:8765 (Wi-Fi)"| foxglove_studio

    %% Hardware & Serial Interfacing
    BridgeLayer ==>|"USB Serial UART (/dev/ttyACM1)"| embedded_loop
    embedded_loop ==>|"Dual PWM Signals"| escs
    encoders ==>|"Pulse Ticks (ISRs)"| embedded_loop

    %% Styling for Services
    classDef serviceNode fill:#e1f5fe,stroke:#0288d1,stroke-width:1px;
    class srv_reset_failsafe,srv_op_mode,srv_toggle_scan,srv_reset_odom,srv_calibrate serviceNode;
```