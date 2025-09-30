#!/usr/bin/env python3
"""
ClimbLab Main Application
Simple pipeline for testing climbing video analysis
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent src directory to path so we can import our modules
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(src_dir)

from pose_extract import extract_landmarks
from widen_data import widen_pose
# from analysis.velocitycalculator import VelocityCalculator  # We'll add this later

from analysis.velocitycalculator import VelocityCalculator

def create_parser():
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="ClimbLab: Analyze climbing videos for movement patterns and technique",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py video.mp4                    # Full analysis
  python main.py video.mp4 --preview          # Preview pose detection only
  python main.py video.mp4 --output results/  # Custom output directory
        """
    )
    
    # Required argument: video file path
    parser.add_argument(
        'video_path',
        type=str,
        help='Path to the climbing video file to analyze'
    )
    
    # Optional arguments
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Show pose detection preview instead of full analysis'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data',
        help='Output directory for analysis results (default: data)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output for debugging'
    )
    
    return parser

def calculate_velocities(csv_path):
    calc = VelocityCalculator(fps=30)

    calc.calculate_from_csv(csv_path)

def main():
    """Main application entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate video file exists
    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"Error: Video file '{video_path}' not found!")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    if args.verbose:
        print(f"Video: {video_path}")
        print(f"Output: {output_dir}")
        print(f"Preview mode: {args.preview}")
    
    try:
        if args.preview:
            print("🎬 Running pose detection preview...")
            # Run pose extraction with preview (needs dummy output path)
            temp_csv = output_dir / f"temp_{video_path.stem}.pose.csv"
            extract_landmarks(str(video_path), str(temp_csv), preview=True)
            print("Preview complete! Check the video window.")
            
        else:
            print("🚀 Starting full climbing analysis pipeline...")
            
            # Step 1: Extract poses
            print("📊 Step 1: Extracting pose landmarks...")
            pose_csv = output_dir / f"{video_path.stem}.pose.csv"
            extract_landmarks(str(video_path), str(pose_csv), preview=False)
            print(f"✅ Poses saved to: {pose_csv}")
            
            # Step 2: Convert to wide format
            print("📈 Step 2: Converting to wide format...")
            wide_csv = output_dir / f"{video_path.stem}.pose.wide.csv"
            widen_pose(str(pose_csv), str(wide_csv))
            print(f"✅ Wide format saved to: {wide_csv}")
            
            # Step 3: Calculate velocities (placeholder for now)
            print("🏃 Step 3: Calculating movement velocities...")
            calculate_velocities(csv_path=wide_csv)
            print("⚠️  Velocity analysis coming soon!")
            
            # Step 4: Detect movement phases (placeholder for now)
            print("🎯 Step 4: Detecting movement phases...")
            print("⚠️  Phase detection coming soon!")
            
            print("🎉 Analysis complete!")
            
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

