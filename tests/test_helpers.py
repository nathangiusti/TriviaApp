"""Shared helper functions for tests to reduce code duplication"""

import tempfile
import os


def create_temp_csv(content: str) -> str:
    """Create a temporary CSV file with the given content
    
    Args:
        content: CSV content as string
        
    Returns:
        Path to temporary CSV file (caller should clean up)
    """
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
    temp_file.write(content)
    temp_file.close()
    return temp_file.name


def cleanup_temp_file(file_path: str) -> None:
    """Clean up temporary file
    
    Args:
        file_path: Path to file to remove
    """
    try:
        os.unlink(file_path)
    except (OSError, FileNotFoundError):
        pass  # File already removed or doesn't exist


# Standard test CSV content for consistent testing
STANDARD_CSV_CONTENT = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is the capital of France?,Paris
2,1,What is the largest planet?,Jupiter
2,2,What year did World War II end?,1945"""


def create_standard_test_csv() -> str:
    """Create a temporary CSV file with standard test questions
    
    Returns:
        Path to temporary CSV file (caller should clean up)
    """
    return create_temp_csv(STANDARD_CSV_CONTENT)