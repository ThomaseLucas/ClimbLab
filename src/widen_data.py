import pandas as pds
from pathlib import Path

def widen_pose(long_csv, wide_csv):
    """
    Convert long form data into wide form data so we have every coordinate of every landmark at each frame in the video. 


    Args:
        long_csv (_type_): _description_
        wide_csv (_type_): _description_
    """

    df = pds.read_csv(long_csv)

    df_wide = df.pivot_table(       
        index=["frame", "t_sec"],
        columns="landmark",
        values=["x_world", "y_world", "z_world", "visibility" ]
    )

    df_wide.columns = [f"{c1}_{c2}" for c1, c2 in df_wide.columns]
    df_wide = df_wide.reset_index()

    df_wide.to_csv(get_data_output_path(wide_csv), index=False)
    print(f"Wrote wide data -> {wide_csv} (shape={df_wide.shape})")
    # Modify output path to be ../data/<filename>.wide.csv

def get_data_output_path(input_path):
    input_path = Path(input_path)
    # Go one directory up, then into 'data'
    data_dir = input_path.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    out_file = input_path.stem + ".csv"
    return str(data_dir / out_file)
    
if __name__ == "__main__":
    import sys, pathlib
    import os
    from pathlib import Path
    inp = pathlib.Path(sys.argv[1])
    out = get_data_output_path(str(inp.with_suffix(".wide.csv")))
    widen_pose(str(inp), out)