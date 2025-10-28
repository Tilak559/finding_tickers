# Input validation utilities
import re
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.core.logging import get_logger
from app.core.exceptions import ValidationException, FileProcessingException

logger = get_logger(__name__)


class InputValidator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_company_name(company_name: str) -> str:
        """
        Validate and sanitize company name.
        
        Args:
            company_name: Raw company name
            
        Returns:
            Sanitized company name
            
        Raises:
            ValidationException: If validation fails
        """
        if not company_name or not isinstance(company_name, str):
            raise ValidationException(
                field="company_name",
                value=company_name,
                reason="Company name must be a non-empty string"
            )
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', company_name.strip())
        
        if not cleaned:
            raise ValidationException(
                field="company_name",
                value=company_name,
                reason="Company name cannot be empty after cleaning"
            )
        
        # Check length
        if len(cleaned) > 200:
            raise ValidationException(
                field="company_name",
                value=company_name,
                reason="Company name too long (max 200 characters)"
            )
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z0-9\s\.,&\-\(\)]+$', cleaned):
            raise ValidationException(
                field="company_name",
                value=company_name,
                reason="Company name contains invalid characters"
            )
        
        return cleaned
    
    @staticmethod
    def validate_company_names(company_names: List[str]) -> List[str]:
        """
        Validate list of company names.
        
        Args:
            company_names: List of company names
            
        Returns:
            List of validated company names
            
        Raises:
            ValidationException: If validation fails
        """
        if not company_names or not isinstance(company_names, list):
            raise ValidationException(
                field="company_names",
                value=company_names,
                reason="Company names must be a non-empty list"
            )
        
        if len(company_names) > 100:
            raise ValidationException(
                field="company_names",
                value=len(company_names),
                reason="Too many company names (max 100)"
            )
        
        validated_names = []
        for i, name in enumerate(company_names):
            try:
                validated_name = InputValidator.validate_company_name(name)
                validated_names.append(validated_name)
            except ValidationException as e:
                logger.warning(f"Invalid company name at index {i}: {e.message}")
                continue
        
        if not validated_names:
            raise ValidationException(
                field="company_names",
                value=company_names,
                reason="No valid company names found"
            )
        
        return validated_names
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate filename format.
        
        Args:
            filename: Raw filename
            
        Returns:
            Validated filename
            
        Raises:
            ValidationException: If validation fails
        """
        if not filename or not isinstance(filename, str):
            raise ValidationException(
                field="filename",
                value=filename,
                reason="Filename must be a non-empty string"
            )
        
        # Check length
        if len(filename) > 255:
            raise ValidationException(
                field="filename",
                value=filename,
                reason="Filename too long (max 255 characters)"
            )
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', filename):
            raise ValidationException(
                field="filename",
                value=filename,
                reason="Filename contains invalid characters"
            )
        
        # Check for dangerous patterns
        dangerous_patterns = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for pattern in dangerous_patterns:
            if pattern in filename:
                raise ValidationException(
                    field="filename",
                    value=filename,
                    reason=f"Filename contains dangerous pattern: {pattern}"
                )
        
        return filename
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> str:
        """
        Validate file extension.
        
        Args:
            filename: Filename to check
            allowed_extensions: List of allowed extensions
            
        Returns:
            Validated filename
            
        Raises:
            ValidationException: If validation fails
        """
        validated_filename = InputValidator.validate_filename(filename)
        
        file_path = Path(validated_filename)
        extension = file_path.suffix.lower()
        
        if extension not in allowed_extensions:
            raise ValidationException(
                field="filename",
                value=filename,
                reason=f"File extension '{extension}' not allowed. Allowed: {allowed_extensions}"
            )
        
        return validated_filename
    
    @staticmethod
    def validate_file_size(file_path: str, max_size_mb: int) -> None:
        """
        Validate file size.
        
        Args:
            file_path: Path to file
            max_size_mb: Maximum size in MB
            
        Raises:
            FileProcessingException: If file is too large
        """
        if not os.path.exists(file_path):
            raise FileProcessingException(
                filename=file_path,
                reason="File does not exist"
            )
        
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise FileProcessingException(
                filename=file_path,
                reason=f"File too large: {file_size / (1024*1024):.2f}MB > {max_size_mb}MB"
            )
    
    @staticmethod
    def validate_pagination_params(page: int, size: int) -> Dict[str, int]:
        """
        Validate pagination parameters.
        
        Args:
            page: Page number
            size: Page size
            
        Returns:
            Validated pagination parameters
            
        Raises:
            ValidationException: If validation fails
        """
        if not isinstance(page, int) or page < 1:
            raise ValidationException(
                field="page",
                value=page,
                reason="Page must be a positive integer"
            )
        
        if not isinstance(size, int) or size < 1 or size > 1000:
            raise ValidationException(
                field="size",
                value=size,
                reason="Size must be between 1 and 1000"
            )
        
        return {"page": page, "size": size}
    
    @staticmethod
    def sanitize_search_term(search_term: str) -> str:
        """
        Sanitize search term for safe use.
        
        Args:
            search_term: Raw search term
            
        Returns:
            Sanitized search term
        """
        if not search_term:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', search_term.strip())
        
        # Limit length
        return sanitized[:100]
    
    @staticmethod
    def validate_csv_structure(file_path: str) -> Dict[str, Any]:
        """
        Validate CSV file structure.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Validation results
            
        Raises:
            FileProcessingException: If validation fails
        """
        try:
            import pandas as pd
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileProcessingException(
                    filename=file_path,
                    reason="File does not exist"
                )
            
            # Try to read CSV
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
            
            return {
                "valid": True,
                "columns": list(df_sample.columns),
                "has_symbol_column": "Symbol" in df_sample.columns,
                "sample_rows": len(df_sample)
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
                reason=f"Unexpected validation error: {str(e)}"
            )
