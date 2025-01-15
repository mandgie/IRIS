import time
from datetime import datetime, timedelta
from src.agent import Goal, Agent
from src.config import GEMINI_API_KEY, CHECK_INTERVAL
from src.utils.logging_config import setup_logging

def main():
    # Setup logging
    logger = setup_logging()
    
    # Validate configuration
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found in environment variables")
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
    
    logger.info(f"Goal set: {goal.description}")
    logger.info(f"Success criteria: {goal.success_criteria}")
    logger.info(f"Target date: {goal.target_date}")
    
    # Initialize the agent
    agent = Agent(goal, GEMINI_API_KEY)
    logger.info("Agent initialized")
    
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
            logger.info(f"Analysis: {decision['analysis']}")
            logger.info(f"Decision: {decision['decision']}")
            logger.info(f"Reasoning: {decision['reasoning']}")
            
            if decision['action_details']:
                logger.info("\nACTION DETAILS")
                logger.info("-" * 50)
                logger.info(f"Tool: {decision['action_details'].get('tool')}")
                logger.info(f"Parameters: {decision['action_details'].get('parameters')}")
                
                if decision.get('action_result'):
                    logger.info("\nACTION RESULT")
                    logger.info("-" * 50)
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
                next_check = current_time + timedelta(seconds=CHECK_INTERVAL)
            
            logger.info("\nNEXT CHECK")
            logger.info("-" * 50)
            logger.info(f"Next check scheduled for: {next_check}")
            logger.info("="*70 + "\n")
            
            # Sleep until next check
            sleep_seconds = (next_check - datetime.now()).total_seconds()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            
    except KeyboardInterrupt:
        logger.info("\nAgent stopped by user")
    except Exception as e:
        logger.error(f"\nAgent stopped due to error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()