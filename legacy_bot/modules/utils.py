import logging
import json
import re
import sys

def setup_logger(name: str, log_file: str = "trading_bot.log", level=logging.INFO) -> logging.Logger:
    """Sets up a logger with both file and console handlers."""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console_handler)
    
    return logger

def parse_json_response(response_text: str) -> dict:
    """
    Robustly parses a JSON response from an LLM.
    It attempts to find a JSON block within the text if the text itself is not valid JSON.
    """
    try:
        # Try direct parsing first
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, look for a JSON block ```json ... ``` or just {...}
        try:
            # Regex to find the first JSON-like object
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
        except Exception as e:
            logging.error(f"Failed to extract JSON from response: {e}")
            
    # Return empty dict or raise error depending on strictness needed
    logging.warning(f"Could not parse JSON from: {response_text[:100]}...")
    return {}
