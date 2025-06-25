#!/bin/bash

# 🔄 ATLAS SESSION UNDO SCRIPT
# Restores ATLAS state from the most recent save backup

echo "🔄 ATLAS Session Undo Starting - $(date)"

# Check if backup directory exists
BACKUP_DIR=".atlas-backup-previous"
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ No backup found at $BACKUP_DIR"
    echo "   Backup is created when running the save protocol"
    echo "   Nothing to restore."
    exit 1
fi

# Check backup manifest
MANIFEST="$BACKUP_DIR/MANIFEST.txt"
if [ -f "$MANIFEST" ]; then
    echo "📋 Backup Information:"
    echo "======================"
    cat "$MANIFEST"
    echo "======================"
    echo ""
fi

# Confirmation prompt
echo "⚠️  This will restore files from backup, overwriting current versions."
echo "   Files that will be restored:"
echo "   - FRESH_COMPACT_MEMORY.md"
echo "   - Today's diary entry (if exists)"
echo "   - Today's working log (if exists)"
echo "   - Project TODO files"
echo ""
read -p "Continue with restore? (y/N): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 0
fi

echo ""
echo "🚀 Starting restore process..."

# Setup date variables
CURRENT_DATE=$(date +%Y_%m_%d)
CURRENT_MONTH=$(date +%m-%b | tr '[:upper:]' '[:lower:]')
CURRENT_YEAR=$(date +%Y)
DIARY_PATH="@MEMORY/PERSONAL_DIARY/$CURRENT_YEAR/$CURRENT_MONTH/diary_$CURRENT_DATE.md"
WORKING_LOG_PATH="@WORKING_LOG/$CURRENT_YEAR/$CURRENT_MONTH/wl_$CURRENT_DATE.md"

RESTORED_COUNT=0

# Restore FRESH_COMPACT_MEMORY
if [ -f "$BACKUP_DIR/FRESH_COMPACT_MEMORY.md" ]; then
    echo "🧠 Restoring FRESH_COMPACT_MEMORY.md..."
    # Create backup of current version first
    [ -f "@FRESH_COMPACT_MEMORY.md" ] && cp "@FRESH_COMPACT_MEMORY.md" "@FRESH_COMPACT_MEMORY.md.before-undo"
    cp "$BACKUP_DIR/FRESH_COMPACT_MEMORY.md" "@FRESH_COMPACT_MEMORY.md"
    echo "   ✅ FRESH_COMPACT_MEMORY.md restored"
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
else
    echo "   ⚠️  No FRESH_COMPACT_MEMORY.md backup found"
fi

# Restore diary
if [ -f "$BACKUP_DIR/diary.md" ]; then
    echo "📔 Restoring diary..."
    # Create backup of current version first
    [ -f "$DIARY_PATH" ] && cp "$DIARY_PATH" "${DIARY_PATH}.before-undo"
    # Ensure directory exists
    mkdir -p "$(dirname "$DIARY_PATH")"
    cp "$BACKUP_DIR/diary.md" "$DIARY_PATH"
    echo "   ✅ Diary restored to $DIARY_PATH"
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
else
    echo "   ⚠️  No diary backup found"
fi

# Restore working log
if [ -f "$BACKUP_DIR/worklog.md" ]; then
    echo "📝 Restoring working log..."
    # Create backup of current version first
    [ -f "$WORKING_LOG_PATH" ] && cp "$WORKING_LOG_PATH" "${WORKING_LOG_PATH}.before-undo"
    # Ensure directory exists
    mkdir -p "$(dirname "$WORKING_LOG_PATH")"
    cp "$BACKUP_DIR/worklog.md" "$WORKING_LOG_PATH"
    echo "   ✅ Working log restored to $WORKING_LOG_PATH"
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
else
    echo "   ⚠️  No working log backup found"
fi

# Restore project TODOs
echo "📋 Restoring project TODOs..."
TODO_COUNT=0
for todo_backup in "$BACKUP_DIR"/*_TODO.md; do
    [ -f "$todo_backup" ] || continue
    
    # Extract project name from backup filename
    backup_filename=$(basename "$todo_backup")
    project_name=${backup_filename%_TODO.md}
    
    TODO_PATH="@REPOS/$project_name/TODO.md"
    
    echo "   Restoring $project_name TODO..."
    
    # Create backup of current version first
    [ -f "$TODO_PATH" ] && cp "$TODO_PATH" "${TODO_PATH}.before-undo"
    
    # Ensure project directory exists
    mkdir -p "@REPOS/$project_name"
    
    # Restore TODO file
    cp "$todo_backup" "$TODO_PATH"
    echo "     ✅ $TODO_PATH restored"
    TODO_COUNT=$((TODO_COUNT + 1))
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
done

if [ "$TODO_COUNT" -eq 0 ]; then
    echo "   ⚠️  No project TODO backups found"
else
    echo "   ✅ $TODO_COUNT project TODOs restored"
fi

# Create restore report
cat > restore-report.md << EOF
ATLAS Restore Report
====================
Date: $(date)
Backup Source: $BACKUP_DIR

Files Restored: $RESTORED_COUNT
- FRESH_COMPACT_MEMORY.md: $([ -f "$BACKUP_DIR/FRESH_COMPACT_MEMORY.md" ] && echo "✅" || echo "❌")
- Diary: $([ -f "$BACKUP_DIR/diary.md" ] && echo "✅" || echo "❌")
- Working Log: $([ -f "$BACKUP_DIR/worklog.md" ] && echo "✅" || echo "❌")
- Project TODOs: $TODO_COUNT files

Current versions backed up with .before-undo extension.

Backup Information:
$([ -f "$MANIFEST" ] && cat "$MANIFEST" || echo "No manifest found")

Git Status After Restore:
$(git status --porcelain | head -10)
$([ "$(git status --porcelain | wc -l)" -gt 10 ] && echo "... (showing first 10 changes)")
EOF

echo ""
echo "📊 Restore Summary:"
echo "==================="
echo "Files Restored: $RESTORED_COUNT"
echo "Project TODOs: $TODO_COUNT"
echo "Report: restore-report.md"
echo ""

if [ "$RESTORED_COUNT" -gt 0 ]; then
    echo "✅ ATLAS Session Restore Complete!"
    echo ""
    echo "📝 Next Steps:"
    echo "- Review restored files to ensure they're correct"
    echo "- Check git status: git status"
    echo "- Current versions saved with .before-undo extension"
    echo "- Restore report saved to restore-report.md"
else
    echo "⚠️  No files were restored"
    echo "   Check that save protocol was run and created backups"
fi

echo ""
echo "🔍 To see what was restored:"
echo "   cat restore-report.md"
echo ""
echo "🔄 Restore completed at $(date)"