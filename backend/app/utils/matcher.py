# NLP-based word matcher for company name corrections
from typing import Optional, List
from difflib import SequenceMatcher, get_close_matches
import re


class NLPMatcher:
    """NLP matcher for suggesting corrected words."""
    
    # Common company name keywords that might be misspelled
    COMMON_COMPANY_WORDS = [
        "apple", "microsoft", "google", "amazon", "tesla", "meta", "nvidia",
        "berkshire", "hathaway", "johnson", "jpmorgan", "chase", "visa",
        "walmart", "mastercard", "home", "depot", "disney", "nike",
        "coca", "cola", "pepsico", "intel", "cisco", "oracle", "ibm",
        "adobe", "salesforce", "netflix", "spotify", "zoom", "snap",
        "twitter", "facebook", "alphabet", "verizon", "att", "comcast",
        "pfizer", "merck", "united", "health", "anthem", "cigna",
        "goldman", "sachs", "morgan", "stanley", "bank", "america",
        "wells", "fargo", "citigroup", "exxon", "mobil", "chevron"
    ]
    
    @staticmethod
    def similarity_score(a: str, b: str) -> float:
        """
        Calculate similarity score between two strings.
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    @staticmethod
    def find_best_match(word: str, dictionary: List[str], min_similarity: float = 0.6) -> Optional[str]:
        """
        Find the best matching word from dictionary using fuzzy matching.
        
        Args:
            word: Word to match
            dictionary: List of candidate words
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            Best matching word or None if no good match found
        """
        if not word or not word.strip():
            return None
        
        word_lower = word.lower().strip()
        
        # Use difflib's get_close_matches for efficient fuzzy matching
        matches = get_close_matches(
            word_lower,
            [w.lower() for w in dictionary],
            n=1,
            cutoff=min_similarity
        )
        
        if matches:
            matched = matches[0]
            # Find the original case version from dictionary
            for dict_word in dictionary:
                if dict_word.lower() == matched:
                    return dict_word
        
        return None
    
    @staticmethod
    def suggest_correction(word: str) -> Optional[str]:
        """
        Suggest a correction for a potentially misspelled company name word.
        
        Args:
            word: Word that might be misspelled
            
        Returns:
            Suggested correction or None if no good match found
        """
        if not word or not word.strip():
            return None
        
        # Clean the word
        cleaned_word = re.sub(r'[^a-zA-Z]', '', word.strip())
        
        if not cleaned_word:
            return None
        
        # Try to find best match from common company words
        corrected = NLPMatcher.find_best_match(
            cleaned_word,
            NLPMatcher.COMMON_COMPANY_WORDS,
            min_similarity=0.6
        )
        
        return corrected
    
    @staticmethod
    def get_corrected_word(original_word: str) -> Optional[str]:
        """
        Get corrected word using NLP matching.
        This is the main method to use for getting word corrections.
        
        Args:
            original_word: Original word that might need correction
            
        Returns:
            Corrected word or None if no correction found
        """
        return NLPMatcher.suggest_correction(original_word)
