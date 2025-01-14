# goal_agent/main.py
import time
import os
import json
from datetime import datetime, timedelta
from src.agent import Goal, Agent

def main():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY environment variable")

    goal = Goal(
        description="Complete a marathon in under 3 hours",
        success_criteria={
            "target_time": "3:00:00",
            "required_weekly_mileage": 50,
            "long_run_distance": 20
        },
        target_date=datetime(2025, 12, 31)
    )
    
    agent = Agent(goal, api_key)
    
    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            print(f"\nStarting cycle {cycle_count} at {datetime.now()}")
            
            decision = agent.run_cycle()
            
            # Pretty print the decision dictionary
            print(f"\nDecision for cycle {cycle_count}:")
            print("Analysis:", decision['analysis'])
            print("Decision:", decision['decision'])
            print("Reasoning:", decision['reasoning'])
            print("Action Details:", json.dumps(decision['action_details'], indent=2) if decision['action_details'] else None)
            print("Next Check:", decision['next_check'])
            
            next_check = datetime.now() + timedelta(hours=1)
            print(f"\nWaiting until {next_check} for next cycle...")
            time.sleep(3600)
            
    except KeyboardInterrupt:
        print("\nAgent stopped by user")
    except Exception as e:
        print(f"\nAgent stopped due to error: {e}")
        raise  # This will show the full error traceback

if __name__ == "__main__":
    main()