#!/bin/bash

# 🔄 FIXED RECURSIVE REFINEMENT SCRIPT

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔄 Recursive Refinement for Spam Pipeline Optimization${NC}"
echo ""

# Create the refinement prompt
cat > /tmp/spam_pipeline_prompt.txt << 'EOF'
Optimize the spam detection pipeline order for Atlas_Email to minimize expensive domain validation by implementing a "fail fast" approach with early exit conditions.

Current Problem:
- Domain validation with WHOIS lookups (100-500ms) runs on ALL 163 spam emails out of 164 total
- Even emails with 99% spam confidence get expensive domain checks
- Processing takes 32.8 seconds due to validating obvious spam domains like "3em5zstrd8.us"
- System validates domains AFTER spam detection instead of using it as last resort

Proposed Optimized Pipeline Order:
1. ML Classification (First Line of Defense)
   - Already 95.6% accurate, catches most spam immediately
   - Speed: ~5-10ms per email
   - Early exit: If ML says 90%+ spam confidence, skip to gibberish check
   - Benefit: Filters out bulk of spam before any other processing

2. Gibberish Detection (Quick Pattern Check)
   - Super fast regex on domains like 3em5zstrd8.us, fktw.kzznfdmzhhpbz.us
   - Speed: <1ms per email
   - Patterns to catch:
     * No vowels in domain name
     * Random alphanumeric strings
     * High entropy character sequences
   - Early exit: Gibberish domain = instant spam, skip remaining checks

3. Authentication (Verify Legitimate Senders)
   - Fast DNS lookups for SPF/DKIM/DMARC
   - Speed: 10-50ms per email
   - Logic: Only check emails that passed ML and gibberish tests
   - Benefit: Catches spoofed legitimate domains

4. Business Overrides (Protect Important Emails)
   - Prevent false positives on critical emails
   - Checks:
     * Appointment confirmations
     * Order receipts
     * Banking transactions
   - Speed: <5ms pattern matching
   - Benefit: Never lose important transactional emails

5. Domain Validation (Last Resort)
   - Most expensive operation (WHOIS lookups 100-500ms)
   - Only run when:
     * ML confidence between 40-70% (uncertain)
     * Passed gibberish check
     * Mixed authentication results
     * Not a business email
   - Skip entirely if: Any previous check gave definitive spam/ham result

Performance Impact:
- Current approach: 164 emails × 200ms avg domain validation = 32.8 seconds
- Optimized approach:
  * 150 emails caught by ML/gibberish = 150 × 10ms = 1.5 seconds
  * 14 uncertain emails need domain validation = 14 × 200ms = 2.8 seconds
  * Total: 4.3 seconds (87% faster!)

Requirements:
- Detailed implementation plan with specific code changes
- Performance benchmarks and calculations
- Risk analysis with mitigation strategies
- Phased rollout approach to ensure safety
- Testing methodology and validation metrics
- Monitoring plan for production deployment

Create a comprehensive optimization plan that maintains Atlas_Email's high accuracy while dramatically improving performance through intelligent pipeline ordering.
EOF

echo -e "${YELLOW}Prompt created. Now you can use it with Claude's recursive refinement tools.${NC}"
echo ""
echo -e "${GREEN}Option 1: Copy and paste this command:${NC}"
echo "claude"
echo ""
echo -e "${GREEN}Then in Claude, type:${NC}"
echo "Use the incremental_refine tool with the prompt from /tmp/spam_pipeline_prompt.txt"
echo ""
echo -e "${GREEN}Option 2: Direct usage (if MCP tools are available):${NC}"
echo "cat /tmp/spam_pipeline_prompt.txt"
echo ""
echo -e "${BLUE}The prompt has been saved to: /tmp/spam_pipeline_prompt.txt${NC}"