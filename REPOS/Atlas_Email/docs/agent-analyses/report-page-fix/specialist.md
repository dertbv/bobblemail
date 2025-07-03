# LARRY - SPECIALIST REPORT

## Implementation Plan

### Issue 1: Missing Data in Template Context

The report_page function queries for data but doesn't pass all of it to the template:
- `preserved_categories` - Queried but not passed
- `preservation_reasons` - Queried but not passed  
- Geographic data - Not queried at all
- Confidence scores - Hardcoded to zeros

### Issue 2: Geographic Data Storage

Geographic data is processed by `GeographicIntelligenceProcessor` but stored in the `raw_data` JSON field of `processed_emails_bulletproof` table. Need to:
1. Extract geographic data from raw_data JSON
2. Aggregate by country
3. Display in report

### Issue 3: Missing Remove Last Import Button

The button simply needs to be added to the template with proper styling and JavaScript handler.

### Issue 4: Duplicate Data Loading

The template loads data twice - once from backend and once via JavaScript API. Should remove the JavaScript call.

## Implementation

### Fix 1: Update report_page to pass all data

```python
# Add missing data to template context
return templates.TemplateResponse(
    "pages/report.html",
    {
        "request": request,
        "session_info": session_info,
        "stats": stats,
        "deleted_pct": deleted_pct,
        "preserved_pct": preserved_pct,
        "category_stats": deleted_categories,
        "preserved_categories": preserved_categories,  # ADD THIS
        "preservation_reasons": preservation_reasons,  # ADD THIS
        "confidence_stats": confidence_stats,
        "validation_stats": validation_stats,
        "category_chart_data": category_chart_data,
        "geographic_stats": geographic_stats  # ADD THIS
    }
)
```

### Fix 2: Add Geographic Data Query

```python
# Get geographic data from raw_data JSON
geographic_stats = db.execute_query("""
    SELECT 
        json_extract(raw_data, '$.sender_country_name') as country,
        json_extract(raw_data, '$.sender_country_code') as country_code,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM processed_emails_bulletproof 
                                        WHERE session_id = ? AND action = 'DELETED'), 0), 1) as percentage
    FROM processed_emails_bulletproof 
    WHERE session_id = ? 
        AND action = 'DELETED'
        AND json_extract(raw_data, '$.sender_country_name') IS NOT NULL
    GROUP BY country 
    ORDER BY count DESC
    LIMIT 10
""", (session_id, session_id))
```

### Fix 3: Calculate Real Confidence Scores

```python
# Get actual confidence score distribution
confidence_distribution = db.execute_query("""
    SELECT 
        CASE 
            WHEN confidence_score >= 0.7 THEN 'High (70%+)'
            WHEN confidence_score >= 0.4 THEN 'Medium (40-70%)'
            ELSE 'Low (<40%)'
        END as level,
        COUNT(*) as count
    FROM processed_emails_bulletproof 
    WHERE session_id = ? AND confidence_score IS NOT NULL
    GROUP BY level
""", (session_id,))

# Convert to expected format
total_with_scores = sum(c['count'] for c in confidence_distribution) if confidence_distribution else 0
confidence_stats = []
for conf in confidence_distribution:
    percentage = (conf['count'] / total_with_scores * 100) if total_with_scores > 0 else 0
    confidence_stats.append({
        "level": conf['level'],
        "count": conf['count'],
        "percentage": percentage
    })
```

### Fix 4: Add Remove Last Import Button to Template

```html
<!-- Add at bottom of report page -->
<div style="margin-top: 40px; text-align: center;">
    <button id="removeLastImport" class="btn btn-danger" onclick="confirmRemoveLastImport()">
        🗑️ Remove Last Import
    </button>
</div>

<script>
async function confirmRemoveLastImport() {
    if (!confirm('Are you sure you want to remove all emails from the last import? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/remove-last-import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully removed ${result.details.emails_removed} emails from last import`);
            window.location.href = '/';
        } else {
            alert(`Error: ${result.message}`);
        }
    } catch (error) {
        alert(`Error removing last import: ${error.message}`);
    }
}
</script>
```

### Fix 5: Remove Duplicate JavaScript Loading

Remove the `loadLastImportInfo()` function and the div with id="lastImportInfo" since data is already loaded from backend.