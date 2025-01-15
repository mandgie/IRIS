import time
import os
import logging
from datetime import datetime, timedelta
from src.agent import Goal, Agent
from src.config import GEMINI_API_KEY, CHECK_INTERVAL, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Validate configuration
    if not GEMINI_API_KEY:
        raise ValueError("Please set GEMINI_API_KEY in your .env file")

    # Create the goal
    goal = Goal(
        description="Complete a marathon in under 3 hours",
        success_criteria={
            "target_time": "3:00:00",
            "required_weekly_mileage": 50,
            "long_run_distance": 20
        },
        target_date=datetime(2025, 12, 31)
    )
    
    # Initialize the agent
    agent = Agent(goal, GEMINI_API_KEY)
    
    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            current_time = datetime.now()
            logger.info(f"Starting cycle {cycle_count} at {current_time}")
            
            # Run the decision cycle
            decision = agent.run_cycle()
            
            # Log the decision details
            logger.info("\nDecision Details:")
            logger.info(f"Analysis: {decision['analysis']}")
            logger.info(f"Decision: {decision['decision']}")
            logger.info(f"Reasoning: {decision['reasoning']}")
            
            if decision['action_details']:
                logger.info("\nAction Details:")
                logger.info(f"Tool: {decision['action_details'].get('tool')}")
                logger.info(f"Parameters: {decision['action_details'].get('parameters')}")
                
                if decision.get('action_result'):
                    logger.info("\nAction Result:")
                    logger.info(f"Status: {decision['action_result'].get('status')}")
                    if decision['action_result'].get('message'):
                        logger.info(f"Message: {decision['action_result'].get('message')}")
            
            # Calculate next check time
            next_check_str = decision.get('next_check', '1 hour')
            if 'hour' in next_check_str:
                hours = int(next_check_str.split()[0])
                next_check = current_time + timedelta(hours=hours)
            elif 'day' in next_check_str:
                days = int(next_check_str.split()[0])
                next_check = current_time + timedelta(days=days)
            else:
                next_check = current_time + timedelta(seconds=CHECK_INTERVAL)  # Default from config
            
            logger.info(f"\nNext check scheduled for: {next_check}")
            
            # Sleep until next check
            sleep_seconds = (next_check - datetime.now()).total_seconds()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            
    except KeyboardInterrupt:
        logger.info("\nAgent stopped by user")
    except Exception as e:
        logger.error(f"\nAgent stopped due to error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()