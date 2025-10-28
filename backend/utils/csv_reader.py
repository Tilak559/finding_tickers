import csv
import pandas as pd
import os
from os import path
from logs.log import get_logger
logger = get_logger()

def read_csv(file_path: str):
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV file: {file_path} with {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return None

def write_csv(df: pd.DataFrame, output_path: str):
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Updated CSV saved at: {output_path}")
    except Exception as e:
        logger.error(f"Error writing CSV file: {e}")

