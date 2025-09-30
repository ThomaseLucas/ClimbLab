import pandas as pd
import matplotlib.pyplot as plt

'''
Practicing using pandas library.
'''

def Convert_CSV(csv_path):
    df = pd.read_csv(csv_path)
    key_landmarks = ['RIGHT_SHOULDER', 'RIGHT_ELBOW', 'RIGHT_WRIST','LEFT_SHOULDER', 'LEFT_ELBOW', 'LEFT_WRIST', 'RIGHT_HIP', 'RIGHT_KNEE', 'RIGHT_ANKLE', 'LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE']

    pose_data = {
        landmark.lower(): {
            coord: df[f'{coord}_world_{landmark}'].values
            for coord in ['x', 'y', 'z']
            if f'{coord}_world_{landmark}' in df.columns
        }
        for landmark in key_landmarks
        if f'x_world_{landmark}' in df.columns
    }

    return pose_data

def main():
    Convert_CSV('data/testvid1.pose.wide.csv')

if __name__ == '__main__':
    main()
