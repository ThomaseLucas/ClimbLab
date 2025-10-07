import numpy as np
import pandas as pd
import math as m
import matplotlib.pyplot as plt
from analysis.velocitycalculator import VelocityCalculator

class MovementPhaseDetector:
    def __init__(self):
        pass

    def segment_motions(self, csv_path):
        calc = VelocityCalculator(fps=30, smoothing_method='savgol', smoothing_strength='aggressive')
        vel_data =calc.calculate_from_csv(csv_path)

        self.find_z_score_at_joint('left_knee', vel_data)

        z_scores = {}

        for landmark in vel_data.keys():  # Use .keys() instead of .items()
            z_scores[landmark] = self.find_z_score_at_joint(landmark, vel_data)

        windows = {}

        for landmark in z_scores.keys():
            windows[landmark] = self.find_movement_intervals(z_scores[landmark])

        print(windows)



        

        
    def find_movement_intervals(self, z_score_array):
        threshold = 0.5 * max(z_score_array)
        intervals = []
        start = None
        
        for i in range(1, len(z_score_array)):
            # Check for crossing above threshold
            if (z_score_array[i-1] <= threshold) and (z_score_array[i] > threshold):
                start = i
            
            # Check for crossing below threshold
            if (z_score_array[i-1] > threshold) and (z_score_array[i] <= threshold) and (start is not None):
                duration = i - start
                if duration >= 7:
                    intervals.append([start, i])
                    start = None  # Only reset after checking
        
        return intervals

    def find_z_score_at_joint(self, landmark_name, velocity_data):
        speeds = velocity_data[landmark_name]['speed_3d']

        # Debug: Check the actual velocity values
        print(f"\n🔍 DEBUG for {landmark_name}:")
        print(f"   Speed range: {np.min(speeds):.6f} to {np.max(speeds):.6f} m/s")
        print(f"   Speed mean: {np.mean(speeds):.6f} m/s")
        print(f"   Speed std: {np.std(speeds):.6f} m/s")
        print(f"   First 5 speeds: {speeds[:5]}")
        

        mean = np.mean(speeds)
        standard_dev = np.std(speeds)

        z_scores = [(speed - mean) / standard_dev for speed in speeds]

        print(f"   Z-score range: {np.min(z_scores):.3f} to {np.max(z_scores):.3f}")
        print(f"   Z-scores > 2: {np.sum(np.array(z_scores) > 2)}")
        print(f"   Z-scores > 5: {np.sum(np.array(z_scores) > 5)}")

        # timestamps = velocity_data[landmark_name]['timestamps'][1:]  # Remove first timestamp
        
        # plt.plot(z_scores)
        # plt.title(f"Z-scores over time for {landmark_name}")
        # plt.xlabel("Frame")
        # plt.ylabel("Z-score")
        # plt.grid(True)  # Makes it easier to read
        # plt.show()

        return z_scores


