#!/usr/bin/env python3
"""
Investigate the Process Emails button functionality on accounts page
"""

from playwright.sync_api import sync_playwright
import time

def investigate_process_button():
    with sync_playwright() as p:
        # Launch Chrome browser with visible UI
        browser = p.chromium.launch(
            headless=False,
            channel="chrome"  # Use Chrome instead of Chromium
        )
        context = browser.new_context()
        page = context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        
        # Navigate to accounts page
        print("📍 Navigating to accounts page...")
        page.goto("http://192.168.1.122:8020/accounts")
        
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        print("\n🔍 Looking for Process Emails buttons...")
        
        # Find all buttons with text "Process Emails"
        process_buttons = page.locator("button:has-text('Process Emails')")
        button_count = process_buttons.count()
        
        if button_count == 0:
            # Maybe it's a link or different element
            print("No <button> elements found. Checking for other elements...")
            
            # Check for any element with that text
            any_process = page.locator("text='Process Emails'")
            any_count = any_process.count()
            print(f"Found {any_count} elements with 'Process Emails' text")
            
            # Check what type of elements they are
            for i in range(any_count):
                element = any_process.nth(i)
                tag_name = element.evaluate("el => el.tagName")
                parent_tag = element.evaluate("el => el.parentElement.tagName")
                href = element.get_attribute("href")
                onclick = element.get_attribute("onclick")
                
                print(f"\nElement {i}:")
                print(f"  Tag: {tag_name}")
                print(f"  Parent tag: {parent_tag}")
                print(f"  Href: {href}")
                print(f"  Onclick: {onclick}")
                
                # Get all attributes
                attrs = element.evaluate("""el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }""")
                print(f"  All attributes: {attrs}")
        
        else:
            print(f"Found {button_count} Process Emails buttons")
            
            # Investigate first button
            first_button = process_buttons.first
            
            # Get button properties
            is_disabled = first_button.is_disabled()
            is_visible = first_button.is_visible()
            
            print(f"\nFirst button properties:")
            print(f"  Visible: {is_visible}")
            print(f"  Disabled: {is_disabled}")
            
            # Get onclick handler
            onclick = first_button.get_attribute("onclick")
            print(f"  Onclick: {onclick}")
            
            # Get all attributes
            attrs = first_button.evaluate("""el => {
                const attrs = {};
                for (let attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }""")
            print(f"  All attributes: {attrs}")
            
            # Check if there are any event listeners
            has_listeners = first_button.evaluate("""el => {
                const listeners = getEventListeners ? getEventListeners(el) : null;
                return listeners ? Object.keys(listeners).length > 0 : 'Unknown';
            }""")
            print(f"  Has event listeners: {has_listeners}")
        
        print("\n🔍 Checking page source for Process functionality...")
        
        # Search for process-related JavaScript functions
        page_content = page.content()
        
        # Check for process functions
        if "runProcess" in page_content:
            print("✅ Found runProcess function in page")
        else:
            print("❌ No runProcess function found")
            
        if "processEmails" in page_content:
            print("✅ Found processEmails function in page")
        else:
            print("❌ No processEmails function found")
        
        # Check for single-account links
        print("\n🔍 Checking single-account links...")
        single_account_links = page.locator("a[href^='/single-account/']")
        link_count = single_account_links.count()
        print(f"Found {link_count} single-account links")
        
        # Try clicking on a single account to see the Process button there
        if link_count > 1:  # Skip "All Accounts"
            print("\n🔍 Navigating to first individual account...")
            first_account = single_account_links.nth(1)
            first_account.click()
            
            # Wait for navigation
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            print("\n🔍 Checking Process button on single-account page...")
            
            # Look for Process action card
            process_card = page.locator(".action-card.process")
            if process_card.count() > 0:
                print("✅ Found Process action card")
                
                onclick = process_card.get_attribute("onclick")
                print(f"  Onclick: {onclick}")
                
                # Check if runProcess function exists
                has_runprocess = page.evaluate("typeof runProcess !== 'undefined'")
                print(f"  runProcess function exists: {has_runprocess}")
                
                if has_runprocess:
                    # Get function definition
                    func_def = page.evaluate("runProcess.toString()")
                    print(f"  runProcess definition preview: {func_def[:200]}...")
                    
                    print("\n🚀 Testing Process button click...")
                    # Clear browser cache first
                    page.reload()
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    
                    # Click the Process button
                    process_card = page.locator(".action-card.process")
                    process_card.click()
                    
                    # Wait a bit to see what happens
                    time.sleep(3)
                    
                    # Check for results or errors
                    status_msg = page.locator("#status-message")
                    if status_msg.is_visible():
                        status_text = status_msg.text_content()
                        print(f"  Status message: {status_text}")
                    
                    results_section = page.locator("#results-section")
                    if results_section.is_visible():
                        print("  ✅ Results section is visible")
            else:
                print("❌ No Process action card found")
        
        # Keep browser open for manual inspection
        print("\n⏸️  Browser will stay open for 30 seconds for manual inspection...")
        time.sleep(30)
        
        browser.close()

if __name__ == "__main__":
    print("🚀 Starting Process Button Investigation")
    print("====================================")
    investigate_process_button()
    print("\n✅ Investigation completed!")