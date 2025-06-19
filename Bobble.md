You’re about to auto /compact soon. Follow these steps—no deviations.

# Compact Session – full-context digest 🪄
# NOTE: Every update in this ritual is applied ONLY to the *project-local*
#       file located at:  ./CLAUDE.md   (i.e. the CLAUDE.md that lives in
#       the root of the current repository).  The global file
#       ~/.claude/CLAUDE.md is *not* touched.

1. **Scan** the last 40 messages (or entire window if fewer) and group
   information under these headings:
   • #CurrentFocus  ── one sentence describing the feature / task in progress  
   • #SessionChanges ── bullet list of edits, refactors, commits made **this** session  
   • #NextSteps   ── bullet list of remaining tasks or open checklist items  
   • #BugsAndTheories── bullet list in the form {bug ⇒ suspected cause / hypothesis}  
   • #Background  ── any key rationale or historical note that gives context

2. Distil each bullet to ≤ 140 chars.  
   • Use past-tense verbs for **#SessionChanges** (e.g. “Refactored `db.py`”)  
   • Use imperative verbs for **#NextSteps** (e.g. “Write unit test for formatter”)

3. **Open *only* `./CLAUDE.md` (project root)** and then:  
   • Append today’s digest under a dated sub-heading:  
     `## 2025-06-13 – Compact Session`  
   • If earlier bullets conflict with the new info, tag them **#Deprecated**  
     (do not delete; keep the historical record).

4. Respond with two deliverables:  
   A. A ```diff``` block showing the precise changes to *./CLAUDE.md*  
   B. A one-line entry for `CHANGELOG.md`, e.g.  
      `2025-06-13  meta: compacted session – API refactor, 2 bugs triaged`

5.  copy todolist to todolist.md and respond tasks have been copied to todolist.md
6. copy update.diff to updated_diff.md file

6. **Purge** chat history, retaining only:  
   • this command’s instructions (for transparency)  
   • the updated diff  
   • the single-line changelog entry