# CSV handling utilities
import pandas as pd
import os
from pathlib import Path
from typing import Generator, Tuple, Optional, Dict, Any
import io
from app.core.logging import get_logger
from app.core.exceptions import FileProcessingException

logger = get_logger(__name__)


class CSVHandler:
    """Handles CSV file operations with validation and streaming."""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
    
    def validate_csv_structure(self, file_path: str) -> Dict[str, Any]:
        """Validate CSV file structure and return metadata."""
        try:
            if not os.path.exists(file_path):
                raise FileProcessingException(
                    filename=file_path,
                    reason="File does not exist"
                )
            
            # Read first few rows to validate structure
            df_sample = pd.read_csv(file_path, nrows=5)
            
            if df_sample.empty:
                raise FileProcessingException(
                    filename=file_path,
                    reason="CSV file is empty"
                )
            
            # Check for required columns
            required_columns = ["Name"]
            missing_columns = [col for col in required_columns if col not in df_sample.columns]
            
            if missing_columns:
                raise FileProcessingException(
                    filename=file_path,
                    reason=f"Missing required columns: {missing_columns}"
                )
            
            # Get file metadata
            file_stats = os.stat(file_path)
            
            return {
                "columns": list(df_sample.columns),
                "total_rows": len(pd.read_csv(file_path)),
                "file_size": file_stats.st_size,
                "has_symbol_column": "Symbol" in df_sample.columns
            }
            
        except pd.errors.EmptyDataError:
            raise FileProcessingException(
                filename=file_path,
                reason="CSV file is empty or corrupted"
            )
        except pd.errors.ParserError as e:
            raise FileProcessingException(
                filename=file_path,
                reason=f"CSV parsing error: {str(e)}"
            )
        except Exception as e:
            raise FileProcessingException(
                filename=file_path,
                reason=f"Unexpected error: {str(e)}"
            )
    
    def read_csv_chunks(self, file_path: str) -> Generator[pd.DataFrame, None, None]:
        """Read CSV file in chunks for memory efficiency."""
        try:
            for chunk in pd.read_csv(file_path, chunksize=self.chunk_size):
                yield chunk
        except Exception as e:
            logger.error(f"Error reading CSV chunks from {file_path}: {e}")
            raise FileProcessingException(
                filename=file_path,
                reason=f"Error reading CSV: {str(e)}"
            )
    
    def read_csv_page(self, file_path: str, page: int, page_size: int) -> Tuple[pd.DataFrame, int]:
        """Read a specific page from CSV file."""
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Read the specific page
            df = pd.read_csv(file_path, skiprows=offset, nrows=page_size)
            
            # Get total rows for pagination info
            total_rows = len(pd.read_csv(file_path))
            
            return df, total_rows
            
        except Exception as e:
            logger.error(f"Error reading CSV page {page} from {file_path}: {e}")
            raise FileProcessingException(
                filename=file_path,
                reason=f"Error reading page: {str(e)}"
            )
    
    def write_csv(self, df: pd.DataFrame, output_path: str) -> None:
        """Write DataFrame to CSV file."""
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            df.to_csv(output_path, index=False)
            logger.info(f"CSV written successfully to {output_path}")
            
        except Exception as e:
            logger.error(f"Error writing CSV to {output_path}: {e}")
            raise FileProcessingException(
                filename=output_path,
                reason=f"Error writing CSV: {str(e)}"
            )
    
    def append_csv(self, df: pd.DataFrame, output_path: str) -> None:
        """Append DataFrame to existing CSV file."""
        try:
            if os.path.exists(output_path):
                # Append to existing file
                df.to_csv(output_path, mode='a', header=False, index=False)
            else:
                # Create new file
                self.write_csv(df, output_path)
            
            logger.info(f"CSV appended successfully to {output_path}")
            
        except Exception as e:
            logger.error(f"Error appending CSV to {output_path}: {e}")
            raise FileProcessingException(
                filename=output_path,
                reason=f"Error appending CSV: {str(e)}"
            )
    
    def create_temp_csv(self, df: pd.DataFrame, prefix: str = "temp") -> str:
        """Create temporary CSV file and return path."""
        try:
            import tempfile
            import uuid
            
            # Create temporary file
            temp_dir = Path("data")
            temp_dir.mkdir(exist_ok=True)
            
            temp_filename = f"{prefix}_{uuid.uuid4().hex}.csv"
            temp_path = temp_dir / temp_filename
            
            self.write_csv(df, str(temp_path))
            
            logger.info(f"Temporary CSV created: {temp_path}")
            return str(temp_path)
            
        except Exception as e:
            logger.error(f"Error creating temporary CSV: {e}")
            raise FileProcessingException(
                filename="temp",
                reason=f"Error creating temporary file: {str(e)}"
            )
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """Clean up temporary file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Error cleaning up temporary file {file_path}: {e}")
    
    def get_csv_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive CSV file information."""
        try:
            metadata = self.validate_csv_structure(file_path)
            
            # Read sample data
            df_sample = pd.read_csv(file_path, nrows=10)
            
            return {
                **metadata,
                "sample_data": df_sample.to_dict('records'),
                "column_types": df_sample.dtypes.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error getting CSV info for {file_path}: {e}")
            raise FileProcessingException(
                filename=file_path,
                reason=f"Error getting file info: {str(e)}"
            )
