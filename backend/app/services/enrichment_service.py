# Simplified enrichment service following original logic
import time
import math
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd

from app.core.logging import get_logger
from app.core.exceptions import ValidationException, SymbolNotFoundException
from app.models.responses import SymbolResponse, EnrichmentResult
from app.services.finnhub_service import FinnhubService
from app.services.file_service import FileService
from app.utils.csv_handler import CSVHandler

logger = get_logger(__name__)


class EnrichmentService:
    """Simplified enrichment service following original logic."""
    
    def __init__(self):
        self.finnhub_service = FinnhubService()
        self.file_service = FileService()
        self.csv_handler = CSVHandler()
        
        # Original configuration
        self.threads = min(10, os.cpu_count() or 4)
        self.page_size = 100
    
    def get_symbol(self, company_name: str) -> Optional[str]:
        """
        Get symbol for a single company using original logic.
        
        Args:
            company_name: Company name to lookup
            
        Returns:
            str: Symbol if found, None otherwise
        """
        try:
            # Original logic: symbol can't be too long so we are trimming after the 1st word
            symbol = company_name.split(" ")[0]
            result = self.finnhub_service.lookup_symbol(symbol)
            
            if isinstance(result, str):
                logger.info(f"Symbol found for {company_name}: {result}")
                return result
            else:
                logger.warning(f"Could not find symbol for {company_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting company profile: {e}")
            return None
    
    def process_row(self, idx: int, company_name: str) -> tuple[int, Optional[str]]:
        """
        Process a single row using original threading logic.
        
        Args:
            idx: Row index
            company_name: Company name to process
            
        Returns:
            tuple: (index, symbol)
        """
        symbol = None
        try:
            if isinstance(company_name, str) and company_name.strip():
                symbol = self.get_symbol(company_name)
                if isinstance(symbol, str):
                    logger.info(f"Symbol found for {company_name}: {symbol}")
                else:
                    logger.warning(f"Could not find symbol for {company_name}")
                    symbol = None
            else:
                logger.warning(f"Invalid company name at row {idx}: {company_name}")
        except Exception as e:
            logger.error(f"Error processing row {idx} ({company_name}): {e}")
            symbol = None
        
        # Original rate limiting
        time.sleep(0.5)  # API rate limit
        return idx, symbol
    
    def enrich_single_company(self, company_name: str) -> SymbolResponse:
        """
        Enrich a single company with ticker symbol.
        
        Args:
            company_name: Company name to lookup
            
        Returns:
            SymbolResponse with lookup result
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting enrichment for company: {company_name}")
            
            # Use original logic
            symbol = self.get_symbol(company_name)
            
            processing_time = time.time() - start_time
            
            if symbol:
                logger.info(f"Enrichment completed for '{company_name}': {symbol} (took {processing_time:.2f}s)")
                return SymbolResponse(
                    company_name=company_name,
                    symbol=symbol,
                    success=True,
                    confidence=1.0,
                    source="finnhub",
                    timestamp=datetime.now()
                )
            else:
                logger.warning(f"Symbol not found for '{company_name}' (took {processing_time:.2f}s)")
                return SymbolResponse(
                    company_name=company_name,
                    symbol=None,
                    success=False,
                    confidence=0.0,
                    source="finnhub",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Enrichment failed for '{company_name}': {e} (took {processing_time:.2f}s)")
            
            return SymbolResponse(
                company_name=company_name,
                symbol=None,
                success=False,
                confidence=0.0,
                source="finnhub",
                timestamp=datetime.now()
            )
    
    def enrich_csv_file(self, input_csv: str, output_csv: str) -> EnrichmentResult:
        """
        Enrich CSV file with symbols using original logic.
        
        Args:
            input_csv: Path to input CSV file
            output_csv: Path to output CSV file
            
        Returns:
            EnrichmentResult with processing statistics
        """
        start_time = time.time()
        
        try:
            # Read CSV using original logic
            df = pd.read_csv(input_csv)
            
            if df is None or df.empty:
                logger.error("Input CSV is empty or missing required columns.")
                return EnrichmentResult(
                    message="Input CSV is empty or missing required columns.",
                    rows_processed=0,
                    rows_updated=0,
                    rows_failed=0,
                    success_rate=0.0,
                    processing_time_seconds=0.0
                )

            if "Name" not in df.columns or "Symbol" not in df.columns:
                logger.error("CSV must have 'Name' and 'Symbol' columns.")
                return EnrichmentResult(
                    message="CSV must have 'Name' and 'Symbol' columns.",
                    rows_processed=0,
                    rows_updated=0,
                    rows_failed=0,
                    success_rate=0.0,
                    processing_time_seconds=0.0
                )

            total_rows = len(df)
            total_pages = math.ceil(total_rows / self.page_size)
            logger.info(f"Total rows: {total_rows}, processing in {total_pages} pages")

            rows_updated = 0
            rows_processed = 0

            for page in range(total_pages):
                start_idx = page * self.page_size
                end_idx = start_idx + self.page_size
                page_df = df.iloc[start_idx:end_idx]

                futures = []
                with ThreadPoolExecutor(max_workers=self.threads) as executor:
                    for idx, row in page_df.iterrows():
                        if pd.isna(row["Symbol"]) or row["Symbol"] == "":
                            company_name = str(row["Name"])
                            if company_name.strip():
                                futures.append(executor.submit(self.process_row, idx, company_name))

                    for future in as_completed(futures):
                        idx, symbol = future.result()
                        df.at[idx, "Symbol"] = symbol
                        rows_processed += 1
                        if symbol:
                            rows_updated += 1

                # Write CSV after each page (original logic)
                df.to_csv(output_csv, index=False)
                logger.info(f"Page {page + 1}/{total_pages} completed. Rows: {len(page_df)}")

            end_time = time.time()
            elapsed_time = end_time - start_time
            success_rate = rows_updated / rows_processed if rows_processed > 0 else 0.0
            
            logger.info(f"Symbol enrichment completed. Output: {output_csv}")
            logger.info(f"Total processing time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
            
            return EnrichmentResult(
                message="Symbol enrichment completed.",
                output_file=output_csv,
                rows_processed=rows_processed,
                rows_updated=rows_updated,
                rows_failed=rows_processed - rows_updated,
                success_rate=round(success_rate, 3),
                processing_time_seconds=round(elapsed_time, 2)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error enriching CSV: {e}")
            
            return EnrichmentResult(
                message=f"Error enriching CSV: {str(e)}",
                rows_processed=0,
                rows_updated=0,
                rows_failed=0,
                success_rate=0.0,
                processing_time_seconds=round(processing_time, 2)
            )
    
    def enrich_uploaded_file(self, file) -> EnrichmentResult:
        """
        Upload and enrich CSV file using original logic.
        
        Args:
            file: Uploaded file object
            
        Returns:
            EnrichmentResult with processing statistics
        """
        try:
            # Read uploaded file
            df = pd.read_csv(file.file)
            
            if df is None or df.empty:
                logger.error("Input CSV is empty or missing required columns.")
                return EnrichmentResult(
                    message="Input CSV is empty or missing required columns.",
                    rows_processed=0,
                    rows_updated=0,
                    rows_failed=0,
                    success_rate=0.0,
                    processing_time_seconds=0.0
                )
            
            # Ensure data directory exists - use absolute path from backend directory
            backend_dir = Path(__file__).parent.parent.parent  # Go up to backend directory
            data_dir = backend_dir / "data"
            data_dir.mkdir(exist_ok=True)
            
            # Save temporary file with proper path handling
            temp_filename = f"temp_{file.filename}"
            temp_input_path = data_dir / temp_filename
            df.to_csv(temp_input_path, index=False)
            
            # Generate output path
            output_filename = f"{file.filename.replace('.csv', '')}_enriched.csv"
            output_path = data_dir / output_filename
            
            # Process file
            result = self.enrich_csv_file(str(temp_input_path), str(output_path))
            
            # Cleanup temporary file (optional, keeping original logic)
            # if os.path.exists(temp_input_path):
            #     os.remove(temp_input_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing uploaded CSV: {e}")
            return EnrichmentResult(
                message=f"Error processing uploaded CSV: {str(e)}",
                rows_processed=0,
                rows_updated=0,
                rows_failed=0,
                success_rate=0.0,
                processing_time_seconds=0.0
            )