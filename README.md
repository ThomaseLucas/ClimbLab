# Climbing Video Analysis System Design

## Overview & Scope

The system analyzes climbing videos using **MediaPipe Pose** to extract joint landmarks and applies movement analysis to assess climbing technique. It supports a **3D wall plane** model (angled wall) to compute distances such as hip-to-wall using single-camera calibration. Output is structured feedback highlighting strengths and weaknesses against six study-backed criteria.

## Requirements & Assumptions

### Functional Requirements

1. Extract human pose data from climbing videos (MediaPipe).
2. Transform raw pose data into wide-format CSV for analysis.
3. Identify climbing phases:

   * Preparation
   * Reaching
   * Stabilization
4. Evaluate movements against **six criteria**:

   1. Decoupling (arm straightness)
   2. Reaching Hand Supports (duration of support)
   3. Weight Shift (hips and knee alignment)
   4. Both Feet Set (foot stability)
   5. Shoulder Relaxing (post-grip relaxation)
   6. Hip Close to the Wall (hip-to-wall distance)
5. Generate feedback with clear error identification.

### Non-Functional Requirements

* Accuracy of detection ≥ 90% for visible joints.
* Usable on standard laptops with GPU support (CUDA optional).
* CSV storage for reproducibility and later ML integration.

### Assumptions

* Videos are recorded from a single camera, fixed viewpoint.
* The wall is approximately planar; its tilt (angle) can be estimated by calibration.
* At least one known scale is present (e.g., ArUco marker size or known hold spacing).
* MediaPipe’s 33 keypoints provide sufficient tracking fidelity.

## Architecture & Rationale

* **Data Capture Layer**: `pose_extract.py` extracts landmarks per frame.
* **Data Transformation Layer**: `widen_data.py` pivots to wide format for multi-joint analysis.
* **Calibration & Wall Plane Estimation (Per Session)**:

  * **Goal**: Recover 3D coordinates in a wall-aligned frame (X right, Y up, Z out-of-wall) and compute true **hip→wall** distance.
  * **Selected Approach** (**User Approved**): **ArUco board on wall** with known square size as the **scale source**.

    1. Each session includes a short wall clip with the ArUco board in view.
    2. Estimate camera intrinsics/extrinsics via `cv2.aruco` on that clip.
    3. Define wall plane Π with normal `n = R[:,2]` and point `p0` from a board corner.
    4. For each MediaPipe 2D keypoint `(u,v)`, back-project using intrinsics to a ray and intersect with Π → 3D `P`.
    5. Compute distances/angles in wall frame; **metric scale** derives from ArUco square length.
  * **Fallback**: **Manual 4-corner homography** using hold-grid spacing (lower accuracy).
* **Phase Detection Module**: Joint-velocity **z-score** segmentation for Preparation, Reaching, Stabilization.
* **Criteria Evaluation Engine**: Rule checks (angles, durations, distances) for the six criteria with thresholds below.
* **Feedback Generator**: Textual analysis + per-phase flags.

### Key Computations

* **Ray–Plane Intersection**: For camera center `C`, ray `r(t)=C + t·d`, plane `(P−p0)·n=0` ⇒ `t = (p0−C)·n / (d·n)`.
* **Hip→Wall**: `abs((P_hip−p0)·n)`.
* **Joint Angles**: Use 3D vectors; fallback to 2D if intersection fails.

### 2D→3D Integration Overview

1. **From MediaPipe (per frame)**: we have normalized image coords `(x_norm, y_norm)` and visibility for each landmark.
2. **Pixel mapping**: `(u, v) = (x_norm·width, y_norm·height)`.
3. **Back-projection ray**: Using intrinsics `K`, compute `d = normalize(K^{-1} [u, v, 1]^T)`; camera center `C` from extrinsics.
4. **Intersect with wall plane**: Use ray–plane to get `P_wall` for any landmark assumed to touch/hover near the wall (feet, hands, hips). Store also `P_com` if computing CoM.
5. **Transform to wall frame**: Apply `R` to express points in `(X_w, Y_w, Z_w)` where `Z_w` is out-of-wall.
6. **Temporal signals**: Differentiate `P_wall(t)` to get velocity/acceleration; compute z-score segmentation for phases.
7. **Criteria features**: Compute angles (e.g., elbow, shoulder), durations (contact times), and distances (hip→wall = `|Z_w|`).
8. **Quality gates**: If a landmark’s visibility < τ or intersection gives negative `t`, fall back to 2D heuristics for that frame.

## Mermaid Diagrams

### Component Architecture

%% diagram: climbing-arch
flowchart TD
    A[Video Input] --> B[Pose Extraction (MediaPipe)]
    B --> C[Landmark CSV (long form)]
    C --> D[Data Transformation]
    D --> E[Session Calibration (ArUco)]
    E --> F[3D Reconstruction (ray-plane)]
    F --> G[Phase Detection]
    G --> H[Criteria Evaluation]
    H --> I[Feedback Generator]
    I --> J[Report Output]


### Sequence of Analysis

````mermaid
%% diagram: climbing-seq
sequenceDiagram
    participant User
    participant System
    participant MediaPipe
    participant Analyzer

    User->>System: Upload climbing video + ArUco wall clip (same session)
    System->>MediaPipe: Extract pose landmarks
    MediaPipe-->>System: Landmark CSV
    System->>Analyzer: Transform data (wide CSV)
    Analyzer->>Analyzer: Estimate intrinsics+wall pose from session clip
    Analyzer->>Analyzer: Back-project 2D joints to 3D wall frame
    Analyzer->>Analyzer: Detect phases (prep/reach/stabilize)
    Analyzer->>Analyzer: Apply 6 criteria rules
    Analyzer-->>System: Feedback results
    System-->>User: Report with errors & advice
````

### Criteria Thresholds (initial)

* **Decoupling**: elbow and shoulder angles of *holding* arm ≥ **150°** during foot setup.
* **Reaching Hand Supports**: supporting-hand contact maintained ≥ **1.0 s** before release.
* **Weight Shift**: knee passes vertically in front of toe on opposite leg; hip projects over that foot before upward drive.
* **Both Feet Set**: both feet in wall contact during stand-up; non-contact > **200 ms** flags error.
* **Shoulder Relaxing**: after grip, elbow & shoulder reopen to ≥ **150°** within **0.7 s**.
* **Hip Close to Wall**: hip→plane distance within **≤5 cm** of reference/coach-set target.

## Non-Functional Concerns

* **Performance**: Pose extraction O(N). Per-session calibration: short extra step; cached for that session.
* **Portability**: Works across different cameras/locations without reusing old intrinsics.
* **Security**: Local-only execution; videos not uploaded externally.
* **Reliability**: Smooth velocities (low-pass) and reject low-visibility keypoints; fall back to 2D heuristics if 3D fails.
* **Testability**: Unit tests for calibration math (ray–plane, angle calc) and per-criterion thresholds.

## Open Issues

1. **Session packaging**: store calibration parameters with each session’s analysis artifact (JSON schema below).

## Interfaces & Data Schemas

### Calibration Module API (proposed)

* `calibrate_session(aruco_clip: Path, board: ArUcoBoardSpec) -> CalibrationParams`

  * **Input**: short video or images of the ArUco board; board spec (square_length, markersX,Y, dictionary).
  * **Output** `CalibrationParams`:

    ```json
    {"K": [[...]], "dist": [...], "R": [[...]], "t": [...], "plane_normal": [nx,ny,nz], "plane_point": [x0,y0,z0], "scale_m_per_px": s}
    ```
* `backproject(keypoints_2d: ndarray, calib: CalibrationParams) -> ndarray[N, 3]`
* `hip_to_wall(P_hip: vec3, plane_normal: vec3, plane_point: vec3) -> float`

### Session Artifact

`session.json`

```json
{
  "video_id": "...",
  "calibration": { /* CalibrationParams */ },
  "frames": {
    "fps": 30.0,
    "landmarks_path": "...pose.csv",
    "wide_path": "...pose.wide.csv"
  },
  "analysis": { "phases": "...", "criteria": "..." }
}
```

### Dev Handoff Checklist

* [x] Data flow defined with per-session calibration
* [x] 2D→3D integration steps specified
* [x] Module interfaces + artifact schema
* [x] Algorithmic checks spec (below)
* [ ] Acceptance tests & metrics thresholds

---

## Dev Review & Test Plan (Maya & Liam)

### Feasibility & Risks

* **Calibration drift**: per-session solves portability but needs checks on reprojection error < **0.8 px**; else re-shoot.
* **Back-projection stability**: reject rays with `d·n ≈ 0` (grazing angles); fall back to 2D heuristics.
* **Visibility gaps**: interpolate only if gaps ≤ **5 frames** and visibility ≥ **0.6** at endpoints.

### Clarifications Resolved

* **CoM**: **Pelvis proxy**.
* **Smoothing**: **Butterworth** (2nd order, **6 Hz cutoff @ 30 fps**), applied to positions; numerical differentiate for velocity/acc.

### Acceptance Criteria (initial)

* Calibration JSON stored per session; reprojection RMSE ≤ **0.8 px**.
* Hip→wall RMSE ≤ **2 cm** on a taped validation path.
* Phase detection F1 ≥ **0.85** on labeled clips.
* Each criterion precision/recall ≥ **0.8** on annotated set.

### Algorithmic Checks Spec

Let wall frame be `(X_w, Y_w, Z_w)` with `Z_w` normal (out of wall). Use Butterworth-filtered trajectories. Phase windows come from z-score segmentation.

1. **Decoupling (prep)**

* Identify **holding hand**: hand with higher Y_w and lower velocity; **supporting hand** is the other.
* During foot-setup (feet |v| > τ_foot, hands near-static), compute angles:

  * `θ_elbow = ∠(wrist–elbow, shoulder–elbow)`, `θ_shoulder = ∠(elbow–shoulder, torso_up)`.
* **Error** if `θ_elbow < 150°` **and** `θ_shoulder < 150°` for ≥ 200 ms.

2. **Reaching Hand Supports (reach)**

* Supporting hand must remain in contact until just before release of reach.
* Model contact when hand speed < τ_hand and `Z_w` within ε of wall for consecutive frames.
* **Error** if pre-release continuous contact < **1.0 s**.

3. **Weight Shift (reach)**

* Determine supporting leg opposite supporting hand.
* Check knee passes vertically ahead of toe (`X_w` alignment in wall frame) and hip projection moves over that foot before upward drive (increase in `Y_w`).
* **Error** if knee never crosses toe line **or** hip never projects over supporting foot within reach window.

4. **Both Feet Set (reach/stand-up)**

* Contact state per foot like hands (speed & `Z_w`).
* **Error** if any gap with a single foot in contact during stand-up exceeds **200 ms**.

5. **Shoulder Relaxing (stabilize)**

* On grip acquisition (velocity peak → zero on reaching hand), within **0.7 s** ensure unlocking:

  * `θ_elbow ≥ 150°` and `θ_shoulder ≥ 150°`.
* **Error** if thresholds unmet.

6. **Hip Close to Wall (reach)**

* Compute `d_hip = |Z_w(hip)|`. Target threshold `d_target` set in config (e.g., **≤10 cm** or coach reference – 5 cm).
* **Error** if `d_hip > d_target` for ≥ 300 ms within reach.

### Deliverables

* Scripts: `calibrate_session.py`, `backproject.py`, `analyze_phases.py`, `evaluate_criteria.py`.
* Reports: per-session HTML/MD summary + CSV of flags.

## Golden Test Cases

Each case ships with: short ArUco clip, 8–12 s action video, annotated truth JSON.

### T1 – Decoupling Violation (prep)

* **Setup**: Climber keeps holding arm bent while setting feet.
* **Expect**: Phase detection finds **prep**; `Decoupling` = FAIL (≥200 ms with elbow & shoulder <150°); others = PASS.

### T2 – Reaching Hand Supports Violation

* **Setup**: Supporting hand releases early (<1.0 s before reach completes).
* **Expect**: `Reaching Hand Supports` = FAIL; accurate grip timing; no false `Both Feet Set` fail.

### T3 – Weight Shift Violation

* **Setup**: Climber pulls with holding arm; knee never crosses toe; hip never projects over supporting foot.
* **Expect**: `Weight Shift` = FAIL; reach phase correctly segmented.

### T4 – Both Feet Set Violation

* **Setup**: One foot swings during stand-up (>200 ms without wall contact); hands nominal.
* **Expect**: `Both Feet Set` = FAIL; others PASS.

### T5 – Shoulder Relaxing Violation (stabilize)

* **Setup**: After grip, elbow/shoulder do not reopen to ≥150° within 0.7 s.
* **Expect**: `Shoulder Relaxing` = FAIL; stabilization phase identified.

### T6 – Hip Close to Wall Violation

* **Setup**: Reach performed with hips > `d_target+5cm` for ≥300 ms.
* **Expect**: `Hip Close to Wall` = FAIL; metric hip→wall within ±2 cm of tape.

### T7 – Clean Reference (all pass)

* **Setup**: Expert clip on easy route.
* **Expect**: All six criteria = PASS; Phase F1 ≥0.9; calibration RMSE ≤0.8 px.

### T8 – Low-Visibility/Edge Cases

* **Setup**: Brief occlusion; extreme camera angle (grazing ray).
* **Expect**: Graceful fallback to 2D where `d·n≈0`; no spurious FAILs; gaps >5 frames are not interpolated.

## Decision Log

* **2025-09-23 • Anna • Approved** – Defined layered architecture with extraction, transformation, detection, evaluation, and feedback stages. Rationale: modularity and testability. Impact: clear separation of responsibilities.

* **2025-09-23 • Noah • Approved** – Adopted **z-score** velocity segmentation for motion phases. Rationale: aligns with study methods. Impact: provides phase boundaries needed for error detection.

* **2025-09-30 • User • Approved** – Use **ArUco-based wall-plane model** with marker size as scale source. Rationale: robust pose of planar wall, metric outputs. Impact: enables accurate hip-to-wall distance and angles.

* **2025-09-30 • User • Approved** – **Per-session calibration** (intrinsics & extrinsics estimated every session). Rationale: portability across cameras & setups. Impact: store calibration with analysis; slight runtime overhead.

* **2025-09-30 • Maya • Approved** – **CoM: pelvis proxy** and **Smoothing: Butterworth (2nd order, 6 Hz)**. Rationale: stable signals with minimal lag. Impact: thresholds and detectors finalized for implementation.

* **2025-09-30 • Liam • Pending** – Curate/record the 8 golden clips and truth JSONs. Rationale: enables CI.

* **2025-09-23 • Anna • Approved** – Defined layered architecture with extraction, transformation, detection, evaluation, and feedback stages. Rationale: modularity and testability. Impact: clear separation of responsibilities.

* **2025-09-23 • Noah • Approved** – Adopted **z-score** velocity segmentation for motion phases. Rationale: aligns with study methods. Impact: provides phase boundaries needed for error detection.

* **2025-09-30 • User • Approved** – Use **ArUco-based wall-plane model** with marker size as scale source. Rationale: robust pose of planar wall, metric outputs. Impact: enables accurate hip-to-wall distance and angles.

* **2025-09-30 • User • Approved** – **Per-session calibration** (intrinsics & extrinsics estimated every session). Rationale: portability across cameras & setups. Impact: store calibration with analysis; slight runtime overhead.

* **2025-09-30 • Maya • Approved** – **CoM: pelvis proxy** and **Smoothing: Butterworth (2nd order, 6 Hz)**. Rationale: stable signals with minimal lag. Impact: thresholds and detectors finalized for implementation.
