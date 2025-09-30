import pandas as pd
import numpy as np
import sys
import os

# Add parent src directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.constants import KEY_LANDMARKS

class VelocityCalculator:
    '''
    This calculator takes the input of all of the points in a video of someone moving. 

    The output of this calculator gives all the speed values for each important point at each frame. 
    '''
    def __init__(self, fps=None):
        pass

    def calculate_from_csv(self, csv_path):
        pose_data = self._convert_csv(csv_path)

        # Get actual FPS from the CSV data
        fps = self._get_fps_from_data()
        velocity_data = self.calculate_velocities(pose_data, fps)
        
        # Validate the results
        validated_data = self.validate_velocities(velocity_data)
        # self.test_with_known_movement(validated_data)
        
        return validated_data
    
    def _get_fps_from_data(self):
        """Extract actual FPS from the CSV timestamps"""
        if hasattr(self, 'df') and 't_sec' in self.df.columns:
            time_diffs = np.diff(self.df['t_sec'].values)
            avg_frame_time = np.mean(time_diffs[time_diffs > 0])  # Remove zeros
            fps = 1.0 / avg_frame_time
            print(f"📊 Detected FPS: {fps:.2f}")
            return fps
        else:
            print("⚠️  Using default FPS: 30.0")
            return 30.0
    
    def _convert_csv(self, csv_path):
        self.df = pd.read_csv(csv_path)

        pose_data = {
            landmark.lower(): {
                coord: self.df[f'{coord}_world_{landmark}'].values 
                for coord in ['x', 'y', 'z']
                if f'{coord}_world_{landmark}' in self.df.columns
            }
            for landmark in KEY_LANDMARKS
            if f'x_world_{landmark}' in self.df.columns
        }

        return pose_data

    def calculate_velocities(self, pose_data, fps=30.0):
        """
        Calculate 3D velocities for all landmarks using vectorized NumPy operations.
        """
        velocity_data = {}
        
        for landmark, coords in pose_data.items():
            if all(coord in coords for coord in ['x', 'y', 'z']):
                # Get NumPy arrays sepperated into their own variables
                x = coords['x']
                y = coords['y'] 
                z = coords['z']
                
                #use numpy to calculate the differences while time progresses. These are the arrays with dx (change in time of x)
                dx = np.diff(x) * fps  # meters/second
                dy = np.diff(y) * fps
                dz = np.diff(z) * fps
                
                # 3D speed magnitude
                speed_3d = np.sqrt(dx**2 + dy**2 + dz**2)
                
                velocity_data[landmark] = {
                    'x': x,
                    'y': y,
                    'z': z,
                    'velocity_x': dx,
                    'velocity_y': dy,
                    'velocity_z': dz,
                    'speed_3d': speed_3d,
                    'timestamps': np.arange(len(x)) / fps
                }

        return velocity_data

                
    def validate_velocities(self, velocity_data):
        """
        Validate that calculated velocities are reasonable for human movement.
        """
        print("🔍 VELOCITY VALIDATION REPORT")
        print("=" * 50)
        
        for landmark, data in velocity_data.items():
            speeds = data['speed_3d']
            
            max_speed = np.max(speeds)
            avg_speed = np.mean(speeds)
            p95_speed = np.percentile(speeds, 95)
            
            print(f"\n{landmark.upper()}:")
            print(f"  Max speed: {max_speed:.3f} m/s ({max_speed*3.6:.1f} km/h)")
            print(f"  Avg speed: {avg_speed:.3f} m/s")
            print(f"  95th percentile: {p95_speed:.3f} m/s")
            
            # Sanity checks
            if max_speed > 10.0:  # 36 km/h is very fast for climbing
                print(f"  ⚠️  WARNING: Suspiciously high speed!")
            elif max_speed > 5.0:  # 18 km/h is fast but possible
                print(f"  🟡 CAUTION: High speed - check if realistic")
                return velocity_data

            else:
                print(f"  ✅ Speed range looks reasonable")
                return velocity_data


        
                
        
    # def test_with_known_movement(self, velocity_data):
    #     """
    #     Test velocities against known movement patterns in climbing videos.
    #     """
    #     print("\n🎯 MOVEMENT PATTERN TESTS")
    #     print("=" * 50)
        
    #     # Test 1: Check if hands move faster than feet (usually true in climbing)
    #     hand_landmarks = ['right_wrist', 'left_wrist']
    #     foot_landmarks = ['right_ankle', 'left_ankle']
        
    #     hand_speeds = []
    #     foot_speeds = []
        
    #     for landmark in hand_landmarks:
    #         if landmark in velocity_data:
    #             hand_speeds.extend(velocity_data[landmark]['speed_3d'])
                
    #     for landmark in foot_landmarks:
    #         if landmark in velocity_data:
    #             foot_speeds.extend(velocity_data[landmark]['speed_3d'])
        
    #     if hand_speeds and foot_speeds:
    #         avg_hand_speed = np.mean(hand_speeds)
    #         avg_foot_speed = np.mean(foot_speeds)
            
    #         print(f"Average hand speed: {avg_hand_speed:.3f} m/s")
    #         print(f"Average foot speed: {avg_foot_speed:.3f} m/s")
            
    #         if avg_hand_speed > avg_foot_speed:
    #             print("✅ Expected: Hands move faster than feet")
    #         else:
    #             print("🤔 Unexpected: Feet moving faster than hands")
        
    #     # Test 2: Check for zero-velocity periods (static holds)
    #     for landmark, data in velocity_data.items():
    #         speeds = data['speed_3d']
    #         still_frames = np.sum(speeds < 0.01)  # Very slow movement
    #         still_percentage = (still_frames / len(speeds)) * 100
            
    #         print(f"\n{landmark}: {still_percentage:.1f}% static frames")
            
    #     return velocity_data