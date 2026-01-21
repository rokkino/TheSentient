import ollama
from config import OLLAMA_MODEL, MANAGER_SYSTEM_PROMPT
from .utils import setup_logger, parse_json_response

logger = setup_logger("ManagerAI")

def consult_manager(current_time: str, market_status: str, open_positions: list) -> dict:
    """
    Consults the local Ollama model to decide whether to activate the Analyst AI.
    """
    try:
        # Construct the prompt
        prompt = f"Current Time: {current_time}. Market Status: {market_status}. Open Positions: {len(open_positions)}."
        
        logger.info(f"Consulting Manager AI ({OLLAMA_MODEL})...")
        
        response = ollama.chat(model=OLLAMA_MODEL, messages=[
            {
                'role': 'system',
                'content': MANAGER_SYSTEM_PROMPT
            },
            {
                'role': 'user',
                'content': prompt
            }
        ])
        
        response_content = response['message']['content']
        logger.debug(f"Manager AI Response: {response_content}")
        
        return parse_json_response(response_content)
        
    except Exception as e:
        logger.error(f"Error consulting Manager AI: {e}")
        # Fail-safe: Sleep if error
        return {"action": "SLEEP"}
