import time
from datetime import datetime, timedelta
import logging
from src.agent import Agent
from src.config.config import GEMINI_API_KEY, CHECK_INTERVAL
from src.utils.logging_config import setup_logging

def main():
    # Setup logging
    logger = setup_logging()
    
    # Validate configuration
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found in environment variables")
        raise ValueError("Please set GEMINI_API_KEY in your .env file")

    # Initialize the agent (goal will be loaded from config)
    agent = Agent(GEMINI_API_KEY)
    logger.info("Agent initialized")
    
    # Log the loaded goal
    logger.info(f"Goal set: {agent.goal.description}")
    logger.info("Success criteria:")
    for criterion in agent.goal.success_criteria:
        logger.info(f"- {criterion}")
    logger.info(f"Due date: {agent.goal.due_date}")
    
    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            current_time = datetime.now()
            
            logger.info("\n" + "="*30 + f" Cycle {cycle_count} " + "="*30)
            logger.info(f"Starting cycle at {current_time}")
            
            # Run the decision cycle
            decision = agent.run_cycle()
            
            # Log decision details
            logger.info("\nDECISION SUMMARY")
            logger.info("-" * 50)
            logger.info(f"Analysis: {decision.get('analysis', 'No analysis provided')}")
            logger.info(f"Decision: {decision.get('decision', 'No decision type provided')}")
            logger.info(f"Reasoning: {decision.get('reasoning', 'No reasoning provided')}")
            
            if decision.get('action_details'):
                logger.info("\nACTION DETAILS")
                logger.info("-" * 50)
                logger.info(f"Tool: {decision['action_details'].get('tool', 'No tool specified')}")
                logger.info(f"Parameters: {decision['action_details'].get('parameters', {})}")
                
                if decision.get('action_result'):
                    logger.info("\nACTION RESULT")
                    logger.info("-" * 50)
                    logger.info(f"Status: {decision['action_result'].get('status', 'No status provided')}")
                    if decision['action_result'].get('message'):
                        logger.info(f"Message: {decision['action_result']['message']}")
            
            # Calculate next check time
            next_check_str = decision.get('next_check', '1 hour')
            if isinstance(next_check_str, str):
                if 'hour' in next_check_str:
                    hours = int(next_check_str.split()[0])
                    next_check = current_time + timedelta(hours=hours)
                elif 'day' in next_check_str:
                    days = int(next_check_str.split()[0])
                    next_check = current_time + timedelta(days=days)
                else:
                    next_check = current_time + timedelta(seconds=CHECK_INTERVAL)
            else:
                next_check = current_time + timedelta(seconds=CHECK_INTERVAL)
            
            logger.info("\nNEXT CHECK")
            logger.info("-" * 50)
            logger.info(f"Next check scheduled for: {next_check}")
            logger.info("="*70 + "\n")
            
            # Sleep until next check (uncomment for production)
            # sleep_seconds = (next_check - datetime.now()).total_seconds()
            # if sleep_seconds > 0:
            #     time.sleep(sleep_seconds)
            
    except KeyboardInterrupt:
        logger.info("\nAgent stopped by user")
    except Exception as e:
        logger.error(f"\nAgent stopped due to error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()