import argparse
import numpy as np
import mediapipe as mp
import pathlib
import cv2
import pandas as pd

def extract_landmarks(video_path: str, out_csv: str, preview: bool = False ) -> None:
    """
    Read the video, run mediapipe on each frame, and write a csv of landmarks. 
    Optionally provide preview by drawing skeleton on poses. 

    Args:
        video_path (str): _description_
        out_csv (str): _description_
        preview (bool, optional): _description_. Defaults to False.
    """

    #code to open video file:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f'Could not open video: {video_path}')
    
    #grab metadata of the video. This will be used to parse frames and find pose/speed.
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    #helper funtions from mediapipe: pose model and drawing tools for skeleton
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5, 
    ) as pose:
        
        rows = []   #append one row per (frame, landmark)

        frame_idx = 0
        while True:
            ok, frame_bgr = cap.read()
            if not ok:
                break

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            result = pose.process(frame_rgb)

            if result.pose_landmarks and result.pose_world_landmarks:

                for i, lm_world in enumerate(result.pose_world_landmarks.landmark):
                    name = mp_pose.PoseLandmark(i).name


                    x_world = lm_world.x #in meters
                    y_world = lm_world.y #in meters
                    z_world = lm_world.z #in meters
                    vis_world = lm_world.visibility


                    rows.append({
                        "frame": frame_idx,
                        "t_sec": frame_idx / fps,
                        "landmark": name,
                        "x_world": x_world,
                        "y_world": y_world,
                        "z_world": z_world,
                        "visibility": vis_world,
                        "width": width,
                        "height": height,
                        "fps": fps,
                    })
            
            if preview:
                draw_frame = frame_bgr.copy()
                if result.pose_landmarks:
                    mp_drawing.draw_landmarks(
                        draw_frame,
                        result.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style(),
                    )
                
                cv2.imshow("Pose preview (press q to quit)", draw_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            frame_idx += 1

    cap.release()
    if preview:
        cv2.destroyAllWindows()

    out_path = pathlib.Path(out_csv)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f'Saved {len(rows)} rows to {out_path.resolve()}')

def main():
    p = argparse.ArgumentParser(description="Extract MediaPipe Pose Landmarks to CSV.")
    p.add_argument("video", type=str, help="Path to an input video file")
    p.add_argument("--out", type=str, default=None, help="Output CSV path (optional)")
    p.add_argument("--preview", action="store_true", help="Show live skeleton overlay while extracting")
    args = p.parse_args()

    video_path = pathlib.Path(args.video)
    out_csv = args.out or str(pathlib.Path("data") / (video_path.stem + ".pose.csv"))  
    extract_landmarks(str(video_path), out_csv, preview=args.preview)

if __name__ == "__main__":
    main()





