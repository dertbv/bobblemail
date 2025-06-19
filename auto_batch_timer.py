#!/usr/bin/env python3
"""
Automated Batch Processing Timer
Allows setting a timer to automatically run batch processing on all accounts
"""

import threading
import time
from datetime import datetime, timedelta
from db_logger import logger, LogLevel, LogCategory
from utils import get_user_choice, get_user_time_input, get_user_time_of_day, format_duration_minutes, format_time_remaining, clear_screen

class AutoBatchTimer:
    """Manages automated batch processing with timer functionality"""
    
    def __init__(self, batch_processor_callback):
        self.timer_threads = {}  # Dictionary to store multiple timers
        self.timer_counter = 0   # Counter for unique timer IDs
        self.batch_processor_callback = batch_processor_callback
        
        # Legacy single timer support (for backward compatibility)
        self.timer_thread = None
        self.timer_active = False
        self.timer_minutes = 0
        self.start_time = None
        self.stop_requested = False
        self.repeat_timer = False
        self.execution_count = 0
        
    def manage_auto_batch_timer(self):
        """Main timer management interface"""
        while True:
            self._show_timer_menu()
            choice = get_user_choice("Press a key (1-5, 9, or Enter/Escape to exit):", ['1', '2', '3', '4', '5', '9'], allow_enter=True)
            
            if choice is None or choice == '9':
                break
            
            clear_screen()
            if choice == '1':
                self._set_timer()
            elif choice == '2':
                self._schedule_timer()
            elif choice == '3':
                self._view_timer_status()
            elif choice == '4':
                self._toggle_repeat_mode()
            elif choice == '5':
                self._manage_timers()
            
            # Clear screen after each operation for consistency
            clear_screen()
    
    def _show_timer_menu(self):
        """Display timer management menu"""
        from utils import display_application_header
        status = "🟢 ACTIVE" if self.timer_active else "🔴 INACTIVE"
        
        display_application_header("AUTOMATED BATCH PROCESSING TIMER")
        print(f"📊 Timer Status: {status}")
        
        # Show repeat mode status
        repeat_mode = "🔄 REPEATING" if self.repeat_timer else "🔂 ONE-TIME"
        print(f"🔁 Mode: {repeat_mode}")
        
        if self.execution_count > 0:
            print(f"📈 Executions: {self.execution_count}")
        
        if self.timer_active and self.start_time:
            next_run = self.start_time + timedelta(minutes=self.timer_minutes)
            remaining_text = format_time_remaining(next_run)
            print(f"⏱️  Time Remaining: {remaining_text}")
            print(f"🎯 Next Run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        elif self.timer_minutes > 0:
            duration_text = format_duration_minutes(self.timer_minutes)
            print(f"⏱️  Timer Set: {duration_text}")
        else:
            print("⏱️  No timer set")
        
        print()
        print("1. ⏰ Set Timer (Minutes)")
        print("2. ⏰ Schedule Timer")
        print("3. 📊 View Timer Status")
        print("4. 🔁 Toggle Repeat Mode")
        print("5. 📋 Manage Timers")
        print("9. ⬅️  Back to Main Menu")
        
        if self.timer_active:
            duration_text = format_duration_minutes(self.timer_minutes)
            if self.repeat_timer:
                print(f"💡 Timer is running - will repeat every {duration_text}")
            else:
                print("💡 Timer is running - will run once then stop")
        else:
            active_timers = len([t for t in self.timer_threads.values() if t['active']])
            if active_timers > 0:
                print(f"💡 {active_timers} timer(s) currently running")
            else:
                print("💡 Set a timer and schedule it for hands-free batch processing")
    
    def _set_timer(self):
        """Set the timer duration in minutes"""
        clear_screen()
        print("\n⏰ SET TIMER DURATION")
        print("-" * 25)
        
        minutes = get_user_time_input("🕐 Set timer duration", max_minutes=10080)
        
        if minutes is None:
            print("❌ Cancelled")
        elif minutes == 0:
            self.timer_minutes = 0
            print("✅ Timer cleared")
        else:
            self.timer_minutes = minutes
            formatted = format_duration_minutes(minutes)
            print(f"✅ Timer set to {formatted}")
        
        input("\nPress Enter to continue...")
    
    def _schedule_timer(self):
        """Schedule a timer to run at a specific time or interval"""
        clear_screen()
        print("\n⏰ SCHEDULE TIMER")
        print("-" * 20)
        print("1. Start Timer Now (uses set duration)")
        print("2. Schedule for Specific Time")
        print("3. Quick Start (set duration & start)")
        print("9. Cancel")
        
        choice = get_user_choice("Choose scheduling option (1-3, 9, or Enter/Escape to exit):", ['1', '2', '3', '9'], allow_enter=True)
        
        if choice is None or choice == '9':
            return
        elif choice == '1':
            self._start_timer_now()
        elif choice == '2':
            self._schedule_for_time()
        elif choice == '3':
            self._quick_start_timer()
    
    def _schedule_for_time(self):
        """Schedule timer for a specific time"""
        clear_screen()
        print("\n🕐 SCHEDULE FOR SPECIFIC TIME")
        print("-" * 35)
        print("💡 This will schedule a one-time execution at the specified time")
        print()
        
        result = get_user_time_of_day("🕐 Enter target time")
        
        if result is None:
            print("❌ Cancelled")
            input("Press Enter to continue...")
            return
        
        hour, minute = result
        
        # Calculate target time
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If target time is in the past, schedule for tomorrow
        if target_time <= now:
            target_time += timedelta(days=1)
        
        delay_seconds = (target_time - now).total_seconds()
        delay_minutes = delay_seconds / 60
        
        print(f"\n🎯 Timer will run at: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Delay: {format_duration_minutes(int(delay_minutes))}")
        
        confirm = input("\nSchedule timer? (yes/no): ").strip().lower()
        if confirm in ('yes', 'y'):
            self._start_scheduled_timer(delay_minutes, target_time)
        else:
            print("❌ Cancelled")
            
        input("Press Enter to continue...")
    
    def _start_scheduled_timer(self, delay_minutes, target_time):
        """Start a scheduled timer"""
        timer_id = self._generate_timer_id()
        
        timer_info = {
            'id': timer_id,
            'delay_minutes': delay_minutes,
            'target_time': target_time,
            'repeat': self.repeat_timer,
            'active': True,
            'thread': None,
            'stop_requested': False,
            'execution_count': 0
        }
        
        # Start the timer thread
        timer_info['thread'] = threading.Thread(
            target=self._scheduled_timer_worker, 
            args=(timer_info,), 
            daemon=True
        )
        timer_info['thread'].start()
        
        self.timer_threads[timer_id] = timer_info
        
        print(f"✅ Timer #{timer_id} scheduled successfully!")
        print("💡 Batch processing will run automatically")
        print("⚠️  Keep the application running for timer to work")
        
        logger.info(f"Scheduled timer #{timer_id} for {target_time.isoformat()}", 
                   category=LogCategory.SYSTEM)
        
        input("\nPress Enter to continue...")
    
    def _generate_timer_id(self):
        """Generate unique timer ID"""
        self.timer_counter += 1
        return self.timer_counter
    
    def _start_timer_now(self):
        """Start the automated timer immediately"""
        if self.timer_minutes <= 0:
            print("\n❌ No timer duration set")
            print("💡 Use 'Set Timer' to set duration first")
            input("Press Enter to continue...")
            return
        
        if self.timer_active:
            print("\n⚠️  Timer is already running")
            print("💡 Stop the current timer first if you want to restart")
            input("Press Enter to continue...")
            return
        
        print(f"\n▶️  STARTING TIMER")
        print("-" * 20)
        print(f"⏱️  Duration: {self.timer_minutes} minutes")
        
        # Calculate when it will run
        start_time = datetime.now()
        run_time = start_time + timedelta(minutes=self.timer_minutes)
        print(f"🎯 Will run at: {run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        confirm = input("\nStart automated timer? (yes/no): ").strip().lower()
        if confirm not in ('yes', 'y'):
            print("❌ Cancelled")
            return
        
        # Start the timer thread
        self.timer_active = True
        self.start_time = start_time
        self.stop_requested = False
        
        self.timer_thread = threading.Thread(target=self._timer_worker, daemon=True)
        self.timer_thread.start()
        
        print("✅ Timer started successfully!")
        print("💡 Batch processing will run automatically")
        print("⚠️  Keep the application running for timer to work")
        
        # Log timer start
        logger.info(f"Auto-batch timer started: {self.timer_minutes} minutes", 
                   category=LogCategory.SYSTEM,
                   metadata={"timer_minutes": self.timer_minutes, "run_time": run_time.isoformat()})
        
        input("\nPress Enter to continue...")
    
    def _stop_timer(self):
        """Stop the automated timer"""
        if not self.timer_active:
            print("\n📭 No timer is currently running")
            input("Press Enter to continue...")
            return
        
        print("\n⏹️  STOPPING TIMER")
        print("-" * 20)
        
        if self.start_time:
            next_run = self.start_time + timedelta(minutes=self.timer_minutes)
            remaining_text = format_time_remaining(next_run)
            print(f"⏱️  Time remaining: {remaining_text}")
        
        confirm = input("Stop the automated timer? (yes/no): ").strip().lower()
        if confirm not in ('yes', 'y'):
            print("❌ Cancelled")
            return
        
        # Stop the timer
        self.stop_requested = True
        self.timer_active = False
        
        print("✅ Timer stopped successfully")
        
        # Log timer stop
        logger.info("Auto-batch timer stopped by user", 
                   category=LogCategory.SYSTEM)
        
        input("\nPress Enter to continue...")
    
    def _view_timer_status(self):
        """View detailed timer status"""
        clear_screen()
        print("\n📊 TIMER STATUS DETAILS")
        print("=" * 30)
        
        print(f"Timer Active: {'🟢 Yes' if self.timer_active else '🔴 No'}")
        duration_text = format_duration_minutes(self.timer_minutes) if self.timer_minutes > 0 else "Not set"
        print(f"Timer Duration: {duration_text}")
        print(f"Repeat Mode: {'🔄 REPEATING' if self.repeat_timer else '🔂 ONE-TIME'}")
        print(f"Executions: {self.execution_count}")
        
        if self.timer_active and self.start_time:
            print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            elapsed = datetime.now() - self.start_time
            elapsed_text = format_duration_minutes(int(elapsed.total_seconds() / 60))
            print(f"Elapsed: {elapsed_text}")
            
            next_run = self.start_time + timedelta(minutes=self.timer_minutes)
            remaining_text = format_time_remaining(next_run)
            print(f"Remaining: {remaining_text}")
            
            if next_run > datetime.now():
                print(f"Next Run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("Status: ⚠️  Timer expired")
        elif self.timer_minutes > 0:
            print("Status: Timer set but not started")
        else:
            print("Status: No timer configured")
        
        print("\n📋 How Timer Works:")
        print("• Set duration in minutes (1-10080)")
        print("• Toggle repeat mode (one-time or repeating)")
        print("• Start timer for automatic batch processing")
        print("• Keep application running for timer to work")
        print("• Timer stops when application exits")
        print("• Repeating mode: runs every X minutes until stopped")
        print("• One-time mode: runs once then stops")
        
        input("\nPress Enter to continue...")
    
    def _toggle_repeat_mode(self):
        """Toggle between one-time and repeating timer"""
        clear_screen()
        print("\n🔁 TOGGLE REPEAT MODE")
        print("-" * 25)
        
        current_mode = "REPEATING" if self.repeat_timer else "ONE-TIME"
        new_mode = "ONE-TIME" if self.repeat_timer else "REPEATING"
        
        print(f"Current mode: {current_mode}")
        print(f"New mode will be: {new_mode}")
        print()
        
        if not self.repeat_timer:
            print("🔄 REPEATING MODE:")
            print("• Timer will run every X minutes continuously")
            print("• Automatically restarts after each execution")
            print("• Perfect for hands-free automation (e.g., every 60 minutes)")
            print("• Runs until you manually stop it")
        else:
            print("🔂 ONE-TIME MODE:")
            print("• Timer runs once then stops")
            print("• You need to restart timer for next execution")
            print("• Good for scheduled one-off processing")
        
        print()
        confirm = input(f"Switch to {new_mode} mode? (yes/no): ").strip().lower()
        
        if confirm in ('yes', 'y'):
            self.repeat_timer = not self.repeat_timer
            mode_text = "REPEATING" if self.repeat_timer else "ONE-TIME"
            print(f"✅ Switched to {mode_text} mode")
            
            if self.repeat_timer:
                duration_text = format_duration_minutes(self.timer_minutes)
                print(f"💡 Timer will now repeat every {duration_text} when started")
            else:
                print("💡 Timer will now run once and stop")
        else:
            print("❌ Mode not changed")
        
        input("\nPress Enter to continue...")
    
    def _manage_timers(self):
        """View and manage all timers (active and inactive)"""
        while True:
            clear_screen()
            from utils import display_application_header
            display_application_header("TIMER MANAGEMENT")
            
            # Show legacy timer
            if self.timer_minutes > 0 or self.timer_active:
                status_icon = "🟢" if self.timer_active else "🔴"
                repeat_icon = "🔄" if self.repeat_timer else "🔂"
                duration_text = format_duration_minutes(self.timer_minutes) if self.timer_minutes > 0 else "Not set"
                exec_text = f" (Runs: {self.execution_count})" if self.execution_count > 0 else ""
                print(f"Legacy Timer {status_icon} {repeat_icon} - Duration: {duration_text}{exec_text}")
            
            # Show scheduled timers
            if self.timer_threads:
                print("\nScheduled Timers:")
                for timer_id, info in self.timer_threads.items():
                    status_icon = "🟢" if info['active'] else "🔴"
                    repeat_icon = "🔄" if info.get('repeat', False) else "🔂"
                    
                    if 'target_time' in info and info['active']:
                        remaining_text = format_time_remaining(info['target_time'])
                        target = info['target_time'].strftime('%H:%M')
                        status_text = f"{remaining_text} - Target: {target}"
                    elif 'target_time' in info:
                        target = info['target_time'].strftime('%H:%M')
                        status_text = f"Stopped - Was target: {target}"
                    else:
                        status_text = "Running" if info['active'] else "Stopped"
                    
                    exec_count = info.get('execution_count', 0)
                    exec_text = f" (Runs: {exec_count})" if exec_count > 0 else ""
                    print(f"Timer #{timer_id} {status_icon} {repeat_icon} - {status_text}{exec_text}")
            
            active_count = len([t for t in self.timer_threads.values() if t['active']]) + (1 if self.timer_active else 0)
            total_count = len(self.timer_threads) + (1 if self.timer_minutes > 0 or self.timer_active else 0)
            
            print(f"\n📊 Status: {active_count} active, {total_count} total timers")
            print("\nActions:")
            print("1. Start/Stop Legacy Timer")
            print("2. Start/Stop Scheduled Timer")
            print("3. Create New Scheduled Timer")
            print("4. Delete Timer")
            print("5. Stop All Active Timers")
            print("9. Back to main menu")
            
            choice = get_user_choice("Choose action (1-5, 9, or Enter/Escape to exit):", ['1', '2', '3', '4', '5', '9'], allow_enter=True)
            
            if choice is None or choice == '9':
                break
            elif choice == '1':
                self._toggle_legacy_timer()
            elif choice == '2':
                self._toggle_scheduled_timer()
            elif choice == '3':
                self._create_new_timer()
            elif choice == '4':
                self._delete_timer()
            elif choice == '5':
                self._stop_all_timers()
    
    def _quick_start_timer(self):
        """Set duration and start timer immediately"""
        clear_screen()
        print("\n⚡ QUICK START TIMER")
        print("-" * 25)
        
        minutes = get_user_time_input("🕐 Set timer duration", max_minutes=10080)
        
        if minutes is None or minutes == 0:
            print("❌ Cancelled")
            input("Press Enter to continue...")
            return
        
        # Set the timer duration
        self.timer_minutes = minutes
        formatted = format_duration_minutes(minutes)
        print(f"✅ Timer set to {formatted}")
        
        # Start immediately
        self._start_timer_now()
    
    def _toggle_legacy_timer(self):
        """Start or stop the legacy timer"""
        if self.timer_active:
            self._stop_timer()
        else:
            if self.timer_minutes <= 0:
                print("\n❌ No timer duration set")
                print("💡 Use 'Set Timer' to set duration first")
            else:
                self._start_timer_now()
        input("\nPress Enter to continue...")
    
    def _toggle_scheduled_timer(self):
        """Start or stop a scheduled timer"""
        if not self.timer_threads:
            print("\n📭 No scheduled timers exist")
            input("Press Enter to continue...")
            return
        
        print("\nScheduled Timers:")
        for timer_id, info in self.timer_threads.items():
            status = "🟢 Active" if info['active'] else "🔴 Stopped"
            target = info.get('target_time', 'N/A')
            target_str = target.strftime('%H:%M') if hasattr(target, 'strftime') else str(target)
            print(f"{timer_id}. Timer #{timer_id} - {status} - Target: {target_str}")
        
        try:
            timer_id = int(input("\nEnter timer ID to toggle: "))
            
            if timer_id not in self.timer_threads:
                print("❌ Invalid timer ID")
                input("Press Enter to continue...")
                return
            
            timer_info = self.timer_threads[timer_id]
            
            if timer_info['active']:
                timer_info['stop_requested'] = True
                timer_info['active'] = False
                print(f"✅ Timer #{timer_id} stopped")
            else:
                print("❌ Cannot restart stopped scheduled timers")
                print("💡 Create a new timer instead")
                
        except ValueError:
            print("❌ Invalid timer ID")
        
        input("\nPress Enter to continue...")
    
    def _create_new_timer(self):
        """Create a new scheduled timer"""
        clear_screen()
        print("\n➕ CREATE NEW SCHEDULED TIMER")
        print("-" * 35)
        
        result = get_user_time_of_day("🕐 Enter target time")
        
        if result is None:
            print("❌ Cancelled")
            input("Press Enter to continue...")
            return
        
        hour, minute = result
        
        # Calculate target time
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If target time is in the past, schedule for tomorrow
        if target_time <= now:
            target_time += timedelta(days=1)
        
        delay_seconds = (target_time - now).total_seconds()
        delay_minutes = delay_seconds / 60
        
        print(f"\n🎯 Timer will run at: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Delay: {format_duration_minutes(int(delay_minutes))}")
        
        confirm = input("\nCreate scheduled timer? (yes/no): ").strip().lower()
        if confirm in ('yes', 'y'):
            self._start_scheduled_timer(delay_minutes, target_time)
        else:
            print("❌ Cancelled")
            
        input("\nPress Enter to continue...")
    
    def _delete_timer(self):
        """Delete a timer"""
        if not self.timer_threads and (self.timer_minutes <= 0 and not self.timer_active):
            print("\n📭 No timers to delete")
            input("Press Enter to continue...")
            return
        
        print("\nTimers:")
        
        # Show legacy timer
        if self.timer_minutes > 0 or self.timer_active:
            status = "🟢 Active" if self.timer_active else "🔴 Inactive"
            duration_text = format_duration_minutes(self.timer_minutes) if self.timer_minutes > 0 else "Not set"
            print(f"L. Legacy Timer - {status} - Duration: {duration_text}")
        
        # Show scheduled timers
        for timer_id, info in self.timer_threads.items():
            status = "🟢 Active" if info['active'] else "🔴 Stopped"
            target = info.get('target_time', 'N/A')
            target_str = target.strftime('%H:%M') if hasattr(target, 'strftime') else str(target)
            print(f"{timer_id}. Timer #{timer_id} - {status} - Target: {target_str}")
        
        choice = input("\nEnter timer ID to delete (L for legacy, number for scheduled): ").strip().upper()
        
        if choice == 'L':
            if self.timer_active:
                self.stop_requested = True
                self.timer_active = False
            self.timer_minutes = 0
            self.execution_count = 0
            print("✅ Legacy timer deleted")
        else:
            try:
                timer_id = int(choice)
                if timer_id in self.timer_threads:
                    timer_info = self.timer_threads[timer_id]
                    if timer_info['active']:
                        timer_info['stop_requested'] = True
                        timer_info['active'] = False
                    del self.timer_threads[timer_id]
                    print(f"✅ Timer #{timer_id} deleted")
                else:
                    print("❌ Invalid timer ID")
            except ValueError:
                print("❌ Invalid input")
        
        input("\nPress Enter to continue...")
    
    def _stop_specific_timer(self, active_timers):
        """Stop a specific timer"""
        try:
            timer_id = int(input("\nEnter timer ID to stop: "))
            
            if timer_id not in active_timers:
                print("❌ Invalid timer ID")
                input("Press Enter to continue...")
                return
            
            timer_info = active_timers[timer_id]
            
            print(f"\n⏹️  STOPPING TIMER #{timer_id}")
            confirm = input("Stop this timer? (yes/no): ").strip().lower()
            
            if confirm in ('yes', 'y'):
                timer_info['stop_requested'] = True
                timer_info['active'] = False
                
                print(f"✅ Timer #{timer_id} stopped successfully")
                logger.info(f"Timer #{timer_id} stopped by user", category=LogCategory.SYSTEM)
            else:
                print("❌ Cancelled")
                
        except ValueError:
            print("❌ Invalid timer ID")
        
        input("\nPress Enter to continue...")
    
    def _stop_all_timers(self):
        """Stop all active timers"""
        active_count = len([t for t in self.timer_threads.values() if t['active']])
        
        if active_count == 0:
            print("\n📭 No active timers to stop")
            input("Press Enter to continue...")
            return
        
        print(f"\n⏹️  STOPPING ALL TIMERS ({active_count} active)")
        confirm = input("Stop all timers? (yes/no): ").strip().lower()
        
        if confirm in ('yes', 'y'):
            stopped_count = 0
            for timer_info in self.timer_threads.values():
                if timer_info['active']:
                    timer_info['stop_requested'] = True
                    timer_info['active'] = False
                    stopped_count += 1
            
            # Also stop legacy timer
            if self.timer_active:
                self.stop_requested = True
                self.timer_active = False
                stopped_count += 1
            
            print(f"✅ Stopped {stopped_count} timer(s) successfully")
            logger.info(f"All timers stopped by user ({stopped_count} timers)", category=LogCategory.SYSTEM)
        else:
            print("❌ Cancelled")
        
        input("\nPress Enter to continue...")
    
    def _timer_worker(self):
        """Background worker thread that handles the timer"""
        try:
            mode_text = "repeating" if self.repeat_timer else "one-time"
            logger.debug(f"Timer worker started: {mode_text} timer waiting {self.timer_minutes} minutes", 
                       category=LogCategory.SYSTEM)
            
            # Main timer loop - continues if repeating mode is enabled
            while self.timer_active and not self.stop_requested:
                # Calculate total seconds to wait
                total_seconds = self.timer_minutes * 60
                
                # Wait in small increments so we can check for stop requests
                check_interval = 10  # Check every 10 seconds
                elapsed_seconds = 0
                
                # Update start time for this cycle
                self.start_time = datetime.now()
                
                while elapsed_seconds < total_seconds and not self.stop_requested:
                    time.sleep(min(check_interval, total_seconds - elapsed_seconds))
                    elapsed_seconds += check_interval
                
                # Check if we were stopped
                if self.stop_requested:
                    logger.info("Timer worker stopped by user request", 
                               category=LogCategory.SYSTEM)
                    return
                
                # Time's up - run batch processing
                execution_num = self.execution_count + 1
                logger.info(f"Timer expired - starting automated batch processing (execution #{execution_num})", 
                           category=LogCategory.SYSTEM)
                
                print(f"\n    🚨 AUTOMATED BATCH PROCESSING STARTING (#{execution_num})")
                if self.repeat_timer:
                    print(f"    🔄 Repeating timer - execution #{execution_num}")
                print(f"    ⏰ Timer expired at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("    " + "=" * 50)
                
                try:
                    # Run batch processing
                    success = self.batch_processor_callback()
                    
                    # Increment execution count
                    self.execution_count += 1
                    
                    if success:
                        print("    ✅ Automated batch processing completed successfully")
                        logger.info(f"Automated batch processing completed successfully (execution #{self.execution_count})", 
                                   category=LogCategory.SYSTEM)
                    else:
                        print("    ⚠️  Automated batch processing completed with issues")
                        logger.warn(f"Automated batch processing completed with issues (execution #{self.execution_count})", 
                                   category=LogCategory.SYSTEM)
                        
                except Exception as e:
                    print(f"    ❌ Automated batch processing failed: {e}")
                    logger.error(e, f"automated_batch_processing_execution_{self.execution_count + 1}")
                
                # Check if we should continue (repeating mode)
                if self.repeat_timer and not self.stop_requested:
                    next_run = datetime.now() + timedelta(minutes=self.timer_minutes)
                    print(f"\n    🔄 REPEATING TIMER")
                    print(f"    ⏰ Next execution at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"    📊 Total executions: {self.execution_count}")
                    print("    " + "=" * 50)
                    # Continue the loop for next execution
                else:
                    # One-time timer or stopped - exit loop
                    print(f"\n    💡 Timer completed. Returning to main menu...")
                    break
            
            # Timer finished
            if self.repeat_timer and self.stop_requested:
                print(f"\n    🛑 REPEATING TIMER STOPPED")
                print(f"    📊 Total executions: {self.execution_count}")
                print(f"    💡 Returning to main menu...")
            elif not self.repeat_timer:
                print(f"    💡 One-time timer completed. Returning to main menu...")
                
            print("    " + "=" * 50)
            self.timer_active = False
                
        except Exception as e:
            logger.error(e, "timer_worker")
            self.timer_active = False
    
    def _scheduled_timer_worker(self, timer_info):
        """Background worker thread for scheduled timers"""
        try:
            timer_id = timer_info['id']
            target_time = timer_info['target_time']
            repeat = timer_info['repeat']
            
            logger.debug(f"Scheduled timer #{timer_id} worker started for {target_time.isoformat()}", 
                       category=LogCategory.SYSTEM)
            
            while timer_info['active'] and not timer_info['stop_requested']:
                # Calculate time until target
                now = datetime.now()
                time_until_target = (target_time - now).total_seconds()
                
                if time_until_target <= 0:
                    # Time to execute
                    execution_num = timer_info['execution_count'] + 1
                    logger.info(f"Scheduled timer #{timer_id} expired - starting batch processing (execution #{execution_num})", 
                               category=LogCategory.SYSTEM)
                    
                    print(f"\n    🚨 SCHEDULED TIMER #{timer_id} EXECUTING (#{execution_num})")
                    if repeat:
                        print(f"    🔄 Repeating timer - execution #{execution_num}")
                    print(f"    ⏰ Timer expired at {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    print("    " + "=" * 50)
                    
                    try:
                        # Run batch processing
                        success = self.batch_processor_callback()
                        
                        # Increment execution count
                        timer_info['execution_count'] += 1
                        
                        if success:
                            print(f"    ✅ Scheduled batch processing completed successfully")
                            logger.info(f"Scheduled batch processing completed successfully (timer #{timer_id}, execution #{timer_info['execution_count']})", 
                                       category=LogCategory.SYSTEM)
                        else:
                            print(f"    ⚠️  Scheduled batch processing completed with issues")
                            logger.warn(f"Scheduled batch processing completed with issues (timer #{timer_id}, execution #{timer_info['execution_count']})", 
                                       category=LogCategory.SYSTEM)
                            
                    except Exception as e:
                        print(f"    ❌ Scheduled batch processing failed: {e}")
                        logger.error(e, f"scheduled_batch_processing_timer_{timer_id}_execution_{timer_info['execution_count'] + 1}")
                    
                    # Check if we should continue (repeating mode)
                    if repeat and not timer_info['stop_requested']:
                        # Calculate next target time based on original delay
                        delay_minutes = timer_info['delay_minutes']
                        target_time = datetime.now() + timedelta(minutes=delay_minutes)
                        timer_info['target_time'] = target_time
                        
                        print(f"\n    🔄 REPEATING TIMER #{timer_id}")
                        print(f"    ⏰ Next execution at: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"    📊 Total executions: {timer_info['execution_count']}")
                        print("    " + "=" * 50)
                        # Continue the loop for next execution
                    else:
                        # One-time timer or stopped - exit loop
                        print(f"\n    💡 Scheduled timer #{timer_id} completed. Returning to main menu...")
                        break
                else:
                    # Wait a bit and check again
                    wait_time = min(10, time_until_target)  # Check every 10 seconds or less
                    time.sleep(wait_time)
            
            # Timer finished
            if repeat and timer_info['stop_requested']:
                print(f"\n    🛑 SCHEDULED TIMER #{timer_id} STOPPED")
                print(f"    📊 Total executions: {timer_info['execution_count']}")
                print(f"    💡 Returning to main menu...")
            elif not repeat:
                print(f"    💡 One-time scheduled timer #{timer_id} completed. Returning to main menu...")
                
            print("    " + "=" * 50)
            timer_info['active'] = False
                
        except Exception as e:
            logger.error(e, f"scheduled_timer_worker_{timer_info['id']}")
            timer_info['active'] = False
    
    def stop_all_timers(self):
        """Stop all timers (called on application exit)"""
        stopped_count = 0
        
        # Stop legacy timer
        if self.timer_active:
            logger.info("Stopping auto-batch timer due to application exit", 
                       category=LogCategory.SYSTEM)
            self.stop_requested = True
            self.timer_active = False
            stopped_count += 1
        
        # Stop all scheduled timers
        for timer_info in self.timer_threads.values():
            if timer_info['active']:
                timer_info['stop_requested'] = True
                timer_info['active'] = False
                stopped_count += 1
        
        if stopped_count > 0:
            logger.info(f"Stopped {stopped_count} timer(s) due to application exit", 
                       category=LogCategory.SYSTEM)
    
    def is_timer_active(self):
        """Check if any timer is currently active"""
        if self.timer_active:
            return True
        return any(info['active'] for info in self.timer_threads.values())
    
    def get_timer_status(self):
        """Get current timer status for display"""
        active_timers = [info for info in self.timer_threads.values() if info['active']]
        
        if self.timer_active:
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                remaining = timedelta(minutes=self.timer_minutes) - elapsed
                if remaining.total_seconds() > 0:
                    minutes_remaining = remaining.total_seconds() / 60
                    mode_text = " Repeating" if self.repeat_timer else ""
                    exec_text = f" Run #{self.execution_count + 1}" if self.repeat_timer else ""
                    legacy_status = f"Legacy: Active ({minutes_remaining:.1f}m remaining){mode_text}{exec_text}"
                else:
                    legacy_status = "Legacy: Expired"
            else:
                legacy_status = "Legacy: Active"
        else:
            mode_text = " Repeating" if self.repeat_timer else ""
            exec_text = f" ({self.execution_count} runs)" if self.execution_count > 0 else ""
            legacy_status = f"Legacy: Inactive{mode_text}{exec_text}" if self.execution_count > 0 or self.timer_minutes > 0 else ""
        
        if active_timers:
            status_parts = []
            if legacy_status and "Inactive" not in legacy_status:
                status_parts.append(legacy_status)
            
            for timer_info in active_timers[:3]:  # Show max 3 timers
                timer_id = timer_info['id']
                if 'target_time' in timer_info:
                    remaining_text = format_time_remaining(timer_info['target_time'])
                    repeat_text = " Rep" if timer_info.get('repeat', False) else ""
                    if "Expired" not in remaining_text:
                        status_parts.append(f"Timer {timer_id}: {remaining_text.replace('⏰ ', '')}{repeat_text}")
                    else:
                        status_parts.append(f"Timer {timer_id}: Expired")
            
            if len(active_timers) > 3:
                status_parts.append(f"+ {len(active_timers) - 3} more")
            
            return " | ".join(status_parts) if status_parts else "Multiple timers active"
        else:
            return legacy_status if legacy_status else "No timers active"

def main():
    """Main function for standalone testing"""
    def dummy_batch_processor():
        print("🧪 Dummy batch processor called")
        time.sleep(2)  # Simulate processing
        return True
    
    timer = AutoBatchTimer(dummy_batch_processor)
    timer.manage_auto_batch_timer()

if __name__ == "__main__":
    main()