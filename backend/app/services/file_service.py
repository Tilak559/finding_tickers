# File service for handling file operations
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import UploadFile
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import FileProcessingException, ValidationException
from app.utils.validators import InputValidator
from app.utils.csv_handler import CSVHandler

logger = get_logger(__name__)


class FileService:
    """Service for handling file operations."""
    
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.upload_dir = Path(settings.upload_dir)
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.allowed_extensions = settings.allowed_extensions
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_upload_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file.
        
        Args:
            file: Uploaded file
            
        Raises:
            ValidationException: If validation fails
            FileProcessingException: If file processing fails
        """
        # Validate filename
        validated_filename = InputValidator.validate_file_extension(
            file.filename, 
            self.allowed_extensions
        )
        
        # Check file size (if available)
        if hasattr(file, 'size') and file.size:
            if file.size > self.max_file_size:
                raise FileProcessingException(
                    filename=file.filename,
                    reason=f"File too large: {file.size / (1024*1024):.2f}MB > {settings.max_file_size_mb}MB"
                )
        
        logger.info(f"File validation passed for: {validated_filename}")
    
    def save_uploaded_file(self, file: UploadFile) -> str:
        """
        Save uploaded file to disk.
        
        Args:
            file: Uploaded file
            
        Returns:
            Path to saved file
            
        Raises:
            FileProcessingException: If saving fails
        """
        try:
            # Generate unique filename
            file_id = uuid.uuid4().hex
            original_name = Path(file.filename).stem
            extension = Path(file.filename).suffix
            filename = f"{original_name}_{file_id}{extension}"
            
            file_path = self.upload_dir / filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            logger.info(f"File saved successfully: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            raise FileProcessingException(
                filename=file.filename,
                reason=f"Error saving file: {str(e)}"
            )
    
    def create_temp_file(self, content: str, extension: str = ".csv") -> str:
        """
        Create temporary file with content.
        
        Args:
            content: File content
            extension: File extension
            
        Returns:
            Path to temporary file
        """
        try:
            file_id = uuid.uuid4().hex
            filename = f"temp_{file_id}{extension}"
            file_path = self.upload_dir / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Temporary file created: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error creating temporary file: {e}")
            raise FileProcessingException(
                filename="temp",
                reason=f"Error creating temporary file: {str(e)}"
            )
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get file information.
        
        Args:
            file_path: Path to file
            
        Returns:
            File information dictionary
        """
        try:
            if not os.path.exists(file_path):
                raise FileProcessingException(
                    filename=file_path,
                    reason="File does not exist"
                )
            
            file_stats = os.stat(file_path)
            file_path_obj = Path(file_path)
            
            info = {
                "filename": file_path_obj.name,
                "size_bytes": file_stats.st_size,
                "size_mb": file_stats.st_size / (1024 * 1024),
                "created_at": file_stats.st_ctime,
                "modified_at": file_stats.st_mtime,
                "extension": file_path_obj.suffix,
                "exists": True
            }
            
            # If it's a CSV file, get additional info
            if file_path_obj.suffix.lower() == ".csv":
                try:
                    csv_info = self.csv_handler.get_csv_info(file_path)
                    info.update({
                        "csv_columns": csv_info.get("columns", []),
                        "csv_rows": csv_info.get("total_rows", 0),
                        "has_symbol_column": csv_info.get("has_symbol_column", False)
                    })
                except Exception as e:
                    logger.warning(f"Could not get CSV info for {file_path}: {e}")
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            raise FileProcessingException(
                filename=file_path,
                reason=f"Error getting file info: {str(e)}"
            )
    
    def cleanup_file(self, file_path: str) -> None:
        """
        Clean up file (delete if temporary).
        
        Args:
            file_path: Path to file
        """
        try:
            if os.path.exists(file_path):
                file_path_obj = Path(file_path)
                
                # Only delete temporary files
                if file_path_obj.name.startswith("temp_"):
                    os.remove(file_path)
                    logger.info(f"Temporary file cleaned up: {file_path}")
                else:
                    logger.info(f"File not cleaned up (not temporary): {file_path}")
                    
        except Exception as e:
            logger.warning(f"Error cleaning up file {file_path}: {e}")
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of files cleaned up
        """
        try:
            import time
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            cleaned_count = 0
            
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file() and file_path.name.startswith("temp_"):
                    file_age = current_time - file_path.stat().st_mtime
                    
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up old temporary file: {file_path}")
            
            logger.info(f"Cleaned up {cleaned_count} old temporary files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            return 0
    
    def list_files(self, pattern: str = "*") -> List[Dict[str, Any]]:
        """
        List files in upload directory.
        
        Args:
            pattern: File pattern to match
            
        Returns:
            List of file information dictionaries
        """
        try:
            files = []
            
            for file_path in self.upload_dir.glob(pattern):
                if file_path.is_file():
                    try:
                        file_info = self.get_file_info(str(file_path))
                        files.append(file_info)
                    except Exception as e:
                        logger.warning(f"Could not get info for file {file_path}: {e}")
                        continue
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def get_file_path(self, filename: str) -> str:
        """
        Get full path for a filename.
        
        Args:
            filename: Filename
            
        Returns:
            Full file path
            
        Raises:
            FileProcessingException: If file doesn't exist
        """
        file_path = self.upload_dir / filename
        
        if not file_path.exists():
            raise FileProcessingException(
                filename=filename,
                reason="File not found"
            )
        
        return str(file_path)
    
    def ensure_directory_exists(self, directory: str) -> None:
        """
        Ensure directory exists.
        
        Args:
            directory: Directory path
        """
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Storage statistics dictionary
        """
        try:
            total_files = 0
            total_size = 0
            temp_files = 0
            temp_size = 0
            
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    total_files += 1
                    total_size += file_size
                    
                    if file_path.name.startswith("temp_"):
                        temp_files += 1
                        temp_size += file_size
            
            return {
                "total_files": total_files,
                "total_size_mb": total_size / (1024 * 1024),
                "temp_files": temp_files,
                "temp_size_mb": temp_size / (1024 * 1024),
                "upload_dir": str(self.upload_dir),
                "max_file_size_mb": settings.max_file_size_mb,
                "allowed_extensions": self.allowed_extensions
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                "error": str(e),
                "upload_dir": str(self.upload_dir)
            }
