#!/usr/bin/env python3
"""
Investigate why the last email in iCloud account can't be processed/deleted
"""

from playwright.sync_api import sync_playwright
import time
import json

def investigate_last_email():
    with sync_playwright() as p:
        # Launch Chrome browser with visible UI
        browser = p.chromium.launch(
            headless=False,
            channel="chrome"
        )
        context = browser.new_context()
        page = context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Page error: {err}"))
        
        # Navigate to accounts page
        print("📍 Navigating to accounts page...")
        page.goto("http://192.168.1.122:8020/accounts")
        page.wait_for_load_state("networkidle")
        
        # Find iCloud account (bobviolette@me.com)
        print("\n🔍 Looking for iCloud account...")
        icloud_link = page.locator("text=bobviolette@me.com").first
        if icloud_link.count() > 0:
            print("✅ Found iCloud account")
            # Click to navigate to single account page
            icloud_link.locator("xpath=ancestor::div[@class='account-card']//a").click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Run preview to see emails
            print("\n🔍 Running preview mode...")
            preview_button = page.locator("#preview-button")
            preview_button.click()
            
            # Wait for emails to load
            print("⏳ Waiting for email table...")
            page.wait_for_selector("#email-details-table table", timeout=30000)
            time.sleep(2)
            
            # Count emails
            email_rows = page.locator("tr[id^='email-row-']")
            email_count = email_rows.count()
            print(f"\n📊 Found {email_count} emails")
            
            if email_count > 0:
                # Get info about the last email
                last_email = email_rows.last
                last_email_id = last_email.get_attribute("id")
                print(f"\n🔍 Examining last email: {last_email_id}")
                
                # Get email details
                uid = last_email_id.replace("email-row-", "")
                
                # Check status icon
                status_icon = last_email.locator("td:first-child span").text_content()
                print(f"  Status icon: {status_icon}")
                
                # Get email info
                date = last_email.locator("td:nth-child(2)").text_content()
                sender = last_email.locator("td:nth-child(3)").text_content()
                subject = last_email.locator("td:nth-child(4)").text_content()
                category = last_email.locator("td:nth-child(5)").text_content()
                
                print(f"  Date: {date}")
                print(f"  From: {sender}")
                print(f"  Subject: {subject}")
                print(f"  Category: {category}")
                
                # Check checkboxes
                research_checkbox = last_email.locator(f"#research-{uid}")
                preserve_checkbox = last_email.locator(f"#preserve-{uid}")
                
                is_research_checked = research_checkbox.is_checked()
                is_preserve_checked = preserve_checkbox.is_checked()
                
                print(f"\n  Research checkbox: {'✅ Checked' if is_research_checked else '❌ Not checked'}")
                print(f"  Preserve checkbox: {'✅ Checked' if is_preserve_checked else '❌ Not checked'}")
                
                # Check if checkboxes are disabled
                research_disabled = research_checkbox.is_disabled()
                preserve_disabled = preserve_checkbox.is_disabled()
                
                if research_disabled or preserve_disabled:
                    print(f"  ⚠️ Checkboxes disabled: Research={research_disabled}, Preserve={preserve_disabled}")
                
                # Try to uncheck if checked
                if is_research_checked:
                    print("\n🔧 Attempting to uncheck research checkbox...")
                    research_checkbox.click()
                    time.sleep(2)
                    
                    # Check if it unchecked
                    still_checked = research_checkbox.is_checked()
                    print(f"  Result: {'Still checked ❌' if still_checked else 'Successfully unchecked ✅'}")
                
                # Now try to process
                print("\n🚀 Attempting to process emails...")
                process_button = page.locator(".action-card.process")
                process_button.click()
                
                # Wait for processing
                time.sleep(5)
                
                # Check results
                status_msg = page.locator("#status-message")
                if status_msg.is_visible():
                    status_text = status_msg.text_content()
                    print(f"\n📋 Status: {status_text}")
                
                # Check if last email still exists
                print("\n🔍 Checking if last email still exists after processing...")
                # Re-run preview
                preview_button.click()
                page.wait_for_selector("#email-details-table table", timeout=30000)
                time.sleep(2)
                
                # Check if same email still there
                same_email = page.locator(f"#email-row-{uid}")
                if same_email.count() > 0:
                    print(f"  ⚠️ Email {uid} is STILL present after processing")
                    
                    # Check its status again
                    new_status = same_email.locator("td:first-child span").text_content()
                    print(f"  Current status: {new_status}")
                else:
                    print(f"  ✅ Email {uid} was successfully deleted")
                    
        else:
            print("❌ Could not find iCloud account")
        
        # Keep browser open
        print("\n⏸️ Browser will stay open for 30 seconds for manual inspection...")
        time.sleep(30)
        
        browser.close()

if __name__ == "__main__":
    print("🚀 Starting Last Email Investigation")
    print("===================================")
    investigate_last_email()
    print("\n✅ Investigation completed!")