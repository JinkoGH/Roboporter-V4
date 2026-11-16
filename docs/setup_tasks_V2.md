# Repository Setup Tasks: Roboporter V4 (Phase 1)

This document outlines the tasks required to initialise, structure, and configure the `Roboporter-V4` GitHub repository for **Phase 1: Remote Control, Failsafe Arbitration & Base Platform Setup**, while establishing groundwork for **Phase 2: Autonomous Navigation (Nav2, SLAM Toolbox, BehaviorTree.CPP)**.

---

## Team Role & Skill Alignment

| Team Member | Discipline & Background | Primary Repository Responsibilities |
| :--- | :--- | :--- |
| **Ivan Gao** | MEng ECE *(ROS 2 Lead)* | Core ROS 2 packages (`bringup`, `teleop`, `safety`), `cmd_vel_mux` arbitration, CI/CD pipelines, and mandatory PR code reviews. |
| **Yuqi Guo** | MEng ECE *(Software & Simulation)* | Sensor driver wrappers (`roboporter_drivers`), URDF/Xacro modeling (`roboporter_description`), and Gazebo Mappin digital twin (`roboporter_gazebo`). |
| **Nurul Gasre** | MEng EEE *(Firmware & Control Signals)* | Arduino Mega 2560 R3 firmware scaffolding, gamepad YAML parameter tuning, and hardware pinout/serial documentation. |
| **Cenk Akan** | MEng EEE *(Power, Chassis & Diagnostics)* | Foxglove Studio diagnostic dashboard layout, GitHub Issue/PR templates, and hardware/power mapping verification. |

---

## Master Task Allocation & Priority Matrix

| Category | Task ID & Name | Summary Description | Priority | Owner | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Repo Admin & Governance** | **1.1–1.4 Repo & Branch Setup** | initialise repo, add license, ROS 2/Arduino `.gitignore`, and branch protections on `main` and `dev`. | **Completed** | **Ivan** | Done |
| **1. Repo Admin & Governance** | **1.5 GitHub Actions CI/CD** | Automate `colcon build`, `colcon test`, and linters (`flake8`, `cpplint`, `pep257`) on pull requests. | **High** | **Ivan** | Pending |
| **1. Repo Admin & Governance** | **1.6 Issue & PR Templates** | Create templates for Bug Reports, Feature Requests, and Hardware Integration Tests. | **Medium** | **Cenk** | Pending |
| **2. Core Control & Safety** | **2.1 Colcon Workspace Layout** | Establish root directory structure (`src/`, `firmware/`, `config/`, `docs/`, `Images/`). | **Completed** | **Ivan** | Done |
| **2. Core Control & Safety** | **2.2 Core ROS 2 Packages** | Scaffold `roboporter_bringup`, `roboporter_teleop`, and `roboporter_safety` (`watchdog_node`, `cmd_vel_mux`). | **Critical** | **Ivan** | Pending |
| **2. Core Control & Safety** | **2.3 MCU Firmware Scaffolding** | Set up `firmware/arduino_mega_control/` for PID loops, HEDS-5500 encoder ISRs, and Mtronics ESC PWM outputs. | **Critical** | **Nurul** | Pending |
| **2. Core Control & Safety** | **2.4 Multiplexer Rules Config** | Create `config/cmd_vel_mux.yaml` setting priorities: Failsafe (1), Teleop (2), Nav2 (3). | **Critical** | **Ivan** | Pending |
| **2. Core Control & Safety** | **2.5 Teleop Gamepad Config** | Create `config/teleop_config.yaml` with 8BitDo Ultimate button/axis mappings, deadzones, and velocity limits. | **High** | **Nurul** | Pending |
| **3. Diagnostics, Sensors & Sim** | **3.1 Foxglove Studio Layout** | Build and commit `config/foxglove_dashboard.json` for `/sys_health`, `/battery_status`, `/odom`, and `/scan`. | **High** | **Cenk** | Pending |
| **3. Diagnostics, Sensors & Sim** | **3.2 Sensor & Sim Packages** | Scaffold `roboporter_drivers`, `roboporter_description` (URDF/Xacro), and `roboporter_gazebo` (Mappin world). | **Low** *(Late Phase 1)* | **Yuqi** | Pending |
| **4. System Documentation** | **4.1 Architecture Diagrams** | Embed Mermaid.js sources and SVGs for Computation Graph and Layered Abstraction Diagram. | **Completed** | **Ivan** | Done |
| **4. System Documentation** | **4.2 Hardware & Topic Mapping** | Document MCU pinouts, serial device paths, and ROS 2 topic/service tables in `docs/hardware_mapping.md`. | **Medium** | **Nurul & Cenk** | Pending |

---

## Task Breakdown

### 1. Repository Administration, Governance & CI/CD
*Tasks focused on version control hygiene, branch protection, automated testing, and team collaboration workflows.*

- [X] **1.1 Create Repository** — `[Priority: Completed]` | **Owner:** Ivan
  - initialise the `Roboporter-V4` GitHub repository under the team organization/account.
- [X] **1.2 License & Metadata** — `[Priority: Completed]` | **Owner:** Ivan
  - Add project description, repository topics (`ros2`, `robotics`, `raspberry-pi`, `arduino`, `teleoperation`, `gazebo`), and open-source `LICENSE`.
- [X] **1.3 Baseline `.gitignore`** — `[Priority: Completed]` | **Owner:** Ivan
  - Configure ignore rules for ROS 2 (`build/`, `install/`, `log/`), Python (`__pycache__/`, `*.pyc`, `.venv/`), IDE metadata (`.vscode/`), and Arduino build artifacts.
- [X] **1.4 Branch Protection Rules** — `[Priority: Completed]` | **Owner:** Ivan
  - Protect `main` (stable releases) and `dev` (integration branch), enforcing pull request (PR) reviews before merging.
- [ ] **1.5 GitHub Actions CI/CD Workflow (`.github/workflows/ros_ci.yml`)** — `[Priority: High]` | **Owner:** Ivan
  - Automate ROS 2 Lyrical workspace compilation (`colcon build`) on every PR into `dev` or `main`.
  - Execute automated unit tests (`colcon test`) and code linters (`ament_flake8`, `ament_cpplint`, `ament_pep257`) to maintain consistent code quality across the team.
- [ ] **1.6 Issue & Pull Request Templates (`.github/`)** — `[Priority: Medium]` | **Owner:** Cenk
  - Add standardized markdown templates for **Bug Reports**, **Feature Requests**, and **Hardware Integration Test Logs**, plus a PR verification checklist.

---

### 2. Core Control, Teleoperation & Safety Architecture (Phase 1 Critical Path)
*High-priority scaffolding and configuration required to achieve manual gamepad driving and automatic watchdog failsafe overrides on the physical robot.*

- [X] **2.1 Colcon Workspace Root Layout** — `[Priority: Completed]` | **Owner:** Ivan
  - Establish top-level directories (`src/`, `firmware/`, `config/`, `docs/`, `Images/`).
- [ ] **2.2 Core ROS 2 Packages (`src/`)** — `[Priority: Critical]` | **Owner:** Ivan
  - `roboporter_bringup`: Launch files for Operator PC and onboard Raspberry Pi 4B (`ros_domain_id` unified).
  - `roboporter_teleop` *(Python / `ament_python`)*: 8BitDo Ultimate gamepad parsing (`joy_node`) and velocity command generation (`teleop_twist_joy`).
  - `roboporter_safety` *(Python / `ament_python`)*: `watchdog_node` (comms heartbeat, sensor health, and battery voltage monitor) and `cmd_vel_mux` priority arbitration.
- [ ] **2.3 Embedded Microcontroller Firmware (`firmware/arduino_mega_control/`)** — `[Priority: Critical]` | **Owner:** Nurul
  - Establish Arduino IDE / PlatformIO project structure for the **Arduino Mega 2560 R3**.
  - Define hardware abstraction stubs for serial command parsing (`/dev/ttyACM1`), **HEDS-5500** quadrature encoder interrupts (ISRs), closed-loop PID velocity control, and dual 5V PWM outputs to the **Mtronics Viper Marine 15A ESCs**.
- [ ] **2.4 Command Multiplexer Configuration (`config/cmd_vel_mux.yaml`)** — `[Priority: Critical]` | **Owner:** Ivan
  - Configure strict channel priority rules and timeout thresholds:
    1. `/failsafe_cmd_vel` *(Priority 1 — Watchdog Emergency Override)*
    2. `/teleop_cmd_vel` *(Priority 2 — Manual Operator Control)*
    3. `/nav_cmd_vel` *(Priority 3 — Reserved for Phase 2 Nav2 Autonomy)*
- [ ] **2.5 Gamepad Teleoperation Configuration (`config/teleop_config.yaml`)** — `[Priority: High]` | **Owner:** Nurul
  - Define button index mappings (including deadman enable switch), analog stick deadzones, and safe maximum linear/angular velocity scaling for the **8BitDo Ultimate Gamepad**.

---

### 3. Telemetry Diagnostics, Sensor Drivers & Simulation Groundwork
*Tooling for wireless operator monitoring during Phase 1 testing, alongside lower-priority sensor and Gazebo simulation setup in preparation for Phase 2.*

- [ ] **3.1 Foxglove Studio Dashboard Layout (`config/foxglove_dashboard.json`)** — `[Priority: High]` | **Owner:** Cenk
  - Configure and export a pre-built Foxglove Studio layout connecting to `foxglove_bridge` (`ws://<rpi_ip>:8765`) with diagnostic panels for `/sys_health`, `/battery_status`, `/odom`, `/ultrasonic/ranges`, and `/scan`.
- [ ] **3.2 Sensor & Simulation Packages (`src/`)** — `[Priority: Low — Late Phase 1]` | **Owner:** Yuqi
  - `roboporter_drivers` *(Hybrid C++/Python)*: Serial bridge (`arduino_bridge_node`), **HC-SR04** ultrasonic array driver (`ultrasonic_driver_node`), and **Slamtec RPLiDAR A1M8** launch wrappers (`rplidar_node`).
  - `roboporter_description`: URDF/Xacro kinematic model, wheel/sensor TF frames (`base_link`, `laser_frame`), and collision geometries.
  - `roboporter_gazebo`: 3D simulation world files (Mappin Building corridor test environment) and differential-drive Gazebo plugins for Phase 2 Nav2 benchmarking.

---

### 4. System Architecture & Hardware Documentation
*Reference documentation mapping physical wiring, serial interfaces, and software communication graphs.*

- [X] **4.1 Software Architecture & Computation Diagrams (`docs/diagrams/`, `Images/`)** — `[Priority: Completed]` | **Owner:** Ivan
  - Commit Mermaid.js source files and rendered SVGs for the **Hardware-Bounded ROS 2 Computation Graph** and **Layered Software Abstraction Diagram**.
- [ ] **4.2 Hardware Pinout & ROS Interface Mapping (`docs/hardware_mapping.md`)** — `[Priority: Medium]` | **Owner:** Nurul & Cenk
  - Consolidate physical wiring assignments (Arduino PWM/ISR pins, ultrasonic GPIO pins, battery voltage divider pins), Linux udev/serial device paths (`/dev/ttyUSB0`, `/dev/ttyACM0`, `/dev/ttyACM1`), and ROS 2 topic/service interface tables.

## Workflow & dependencies

#### Stage 1: Foundation & Hardware Audit

* **Software Foundation (Done):** Repo governance (`1.1–1.4`), workspace structure (`2.1`), and architecture diagrams (`5.1`) are complete, unblocking all coding and CI/CD tasks.
* **Physical Audit & Repair (Gate):** Inspect and bench-test existing batteries, 12V-to-5V buck converters, Mtronics ESCs, HEDS-5500 encoders, Raspberry Pi 4B, and Arduino Mega. Replace or repair missing/faulty hardware before powering any actuators.


#### Stage 2: Interface Definition & Core Scaffolding

* **Hardware Wiring & Pinouts $\rightarrow$ Docs (`4.2`) & Firmware (`2.3`):** Finalising physical pin connections, serial ports (`/dev/ttyACM*`), and fitting the hardware Emergency Stop button directly unblocks `docs/hardware_mapping.md` (`4.2`) and Arduino firmware (`2.3`).
* **Core ROS 2 Packages (`2.2`, `2.4`, `2.5`):** `roboporter_bringup`, `roboporter_teleop`, and `roboporter_safety` depend on the workspace structure (`2.1`) and define the topic contracts (`cmd_vel_mux.yaml`, `teleop_config.yaml`).
* **Repo Tooling (`1.5`, `1.6`, `3.1`):** GitHub Actions CI (`1.5`) and Issue/PR templates (`1.6`) can be set up immediately after `2.2` to enforce build/lint checks on PRs. The Foxglove layout (`3.1`) depends on knowing the topic names from `2.2`.

#### Stage 3: Wheels-Off Bench Integration & Safety Verification

* **Convergence Point:** Requires **Physical E-Stop & Power**, **Arduino Firmware (`2.3`)**, and **Core ROS 2 Teleop/Safety (`2.2`, `2.4`, `2.5`)**.
* **Verification:** Flash the Arduino, verify 8BitDo $\rightarrow$ Pi 4B $\rightarrow$ Arduino $\rightarrow$ ESC motor response and encoder ticks with wheels elevated, and validate watchdog failsafes (comms drop, low battery) via Foxglove (`3.1`).



#### Stage 4: Live Floor Trials & Phase 2 Prep

* **Physical Floor Testing:** Depends on passing Stage 3 safety checks. Conduct live remote driving tests in Mappin Building (<250 ms latency target).
* **Sensors & Digital Twin (`3.2`):** Mounting/wiring the RPLiDAR A1M8 and HC-SR04 sensors unlocks `roboporter_drivers`, while `roboporter_description` (URDF) and `roboporter_gazebo` (Mappin world) are built in parallel to prepare for Phase 2 SLAM/Nav2.


### Dependency & Workflow Diagram

```mermaid
flowchart TD
    subgraph Done ["Completed Baseline"]
        repo["1.1–1.4 Repo & Workspace (2.1)"]
        diag["5.1 Architecture Diagrams"]
    end

    subgraph HW ["Physical Robot Track (Hardware)"]
        audit["HW-1: Hardware Audit & Repair<br>(Due 30/11/26 Entry Gate)"]
        wiring["HW-2: Power Rails, E-Stop & Pinouts"]
        sensors_hw["HW-3: Mount RPLiDAR & HC-SR04"]
    end

    subgraph SW ["Software & Repo Track"]
        core_ros["2.2 / 2.4 / 2.5 Core ROS 2<br>(Teleop, Safety & Mux)"]
        ci["1.5 CI/CD & 1.6 PR Templates"]
        firmware["2.3 Arduino Mega Firmware"]
        docs_ui["3.1 Foxglove UI & 4.2 Pinout Docs"]
        sim_drv["3.2 Sensor Drivers, URDF & Gazebo"]
    end

    subgraph Test ["Integration & Verification"]
        bench["Bench Test (Wheels-Off)<br>Teleop + Watchdog Failsafe"]
        floor["Mappin Floor Trials (<250ms)<br>& Phase 2 Readiness"]
    end

    %% Dependencies
    repo --> core_ros
    core_ros --> ci
    core_ros --> docs_ui
    core_ros --> sim_drv

    audit --> wiring
    audit --> sensors_hw
    wiring --> firmware
    wiring --> docs_ui

    firmware --> bench
    core_ros --> bench
    docs_ui --> bench

    bench --> floor
    sensors_hw --> sim_drv
    sim_drv --> floor

    %% Styling
    style Done fill:#e8f5e9,stroke:#2e7d32
    style HW fill:#fff3e0,stroke:#ef6c00
    style SW fill:#e3f2fd,stroke:#1565c0
    style Test fill:#f3e5f5,stroke:#6a1b9a

```