#!/bin/bash
# ATLAS Email Project Cleanup Script
# Removes obsolete files and directories safely

echo "🧹 ATLAS Email Project Cleanup"
echo "=============================="

# Create cleanup log
CLEANUP_LOG="cleanup_$(date +%Y%m%d_%H%M%S).log"
echo "Starting cleanup at $(date)" > "$CLEANUP_LOG"

# Function to safely remove with logging
safe_remove() {
    local path="$1"
    if [ -e "$path" ]; then
        echo "Removing: $path"
        echo "Removed: $path" >> "$CLEANUP_LOG"
        rm -rf "$path"
    else
        echo "Not found (skipping): $path"
    fi
}

# 1. Remove duplicate CLAUDE files
echo -e "\n📄 Removing duplicate files..."
safe_remove "CLAUDE-original.md"

# 2. Remove obsolete fresh_memory files (already in unified memory)
echo -e "\n🧠 Removing obsolete memory files..."
safe_remove "FRESH_COMPACT_MEMORY.md"
safe_remove "REPOS/Atlas_Email/fresh_memory_Atlas_Email.md"
safe_remove "REPOS/email_project/fresh_memory_email.md"
safe_remove "REPOS/email_project/fresh_memory_email_project.md"
safe_remove "REPOS/stocks_project/fresh_memory_stocks.md"

# 3. Remove completed agent worktrees
echo -e "\n🤖 Removing completed agent worktrees..."
echo "⚠️  Make sure valuable results have been extracted!"
read -p "Have you verified all agent results are saved? (y/n): " confirm
if [ "$confirm" = "y" ]; then
    safe_remove "REPOS/Atlas_Email/playground/email-geographic-stooges-work"
    safe_remove "REPOS/Atlas_Email/playground/email-performance-impact-work"
    safe_remove "REPOS/Atlas_Email/playground/email-research-flag-analysis-work"
    safe_remove "REPOS/playground/email-recursive-refinement-analysis-work"
    safe_remove "REPOS/playground/email-report-page-fix-work"
else
    echo "Skipping agent worktree cleanup"
fi

# 4. Remove test files
echo -e "\n🧪 Removing obsolete test files..."
safe_remove "test_deletion.py"
safe_remove "REPOS/Atlas_Email/test_bed_bath.py"
safe_remove "REPOS/Atlas_Email/test_geographic_integration.py"
safe_remove "REPOS/Atlas_Email/simple_performance_analysis.py"
safe_remove "REPOS/Atlas_Email/performance_benchmark.py"

# 5. Clean up log files
echo -e "\n📋 Cleaning log files..."
safe_remove "REPOS/stocks_project/*.log"
safe_remove "REPOS/Atlas_Email/logs/webapp.log"
safe_remove "REPOS/Atlas_Email/logs/webapp.pid"
safe_remove "REPOS/Atlas_Email/src/atlas_email/api/webapp.log"
safe_remove "REPOS/Atlas_Email/src/atlas_email/api/webapp.pid"

# 6. Remove migration completion markers
echo -e "\n📝 Removing migration markers..."
safe_remove "UNIFIED-MEMORY-IMPLEMENTATION-COMPLETE.md"
safe_remove "UNIFIED-MEMORY-MIGRATION-COMPLETE.md"

# 7. Optional: Remove old email_project
echo -e "\n📦 Old email_project directory found"
echo "This appears to be an older version superseded by Atlas_Email"
read -p "Remove old email_project directory? (y/n): " remove_old
if [ "$remove_old" = "y" ]; then
    safe_remove "REPOS/email_project"
else
    echo "Keeping email_project directory"
fi

# Summary
echo -e "\n✅ Cleanup complete!"
echo "Log saved to: $CLEANUP_LOG"
echo -e "\nSpace reclaimed:"
df -h .

echo -e "\n💡 Next steps:"
echo "1. Review $CLEANUP_LOG to see what was removed"
echo "2. Run 'git status' to see changes"
echo "3. Commit the cleanup if satisfied"