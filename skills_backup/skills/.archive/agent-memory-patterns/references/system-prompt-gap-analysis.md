# System Prompt Gap Analysis: Holographic Memory

## Date: 2026-05-30

## Issue
The system prompt's guidance for holographic memory is too vague, leading to "silent sessions" where the agent never proactively stores facts.

## Current System Prompt (relevant sections)

### Holographic Memory section:
> Active. 116 facts stored with entity resolution and trust scoring.
> Use fact_store to search, probe entities, reason across entities, or add facts.
> Use fact_feedback to rate facts after using them (trains trust scores).

### Persona section:
> When the user references something from a past conversation or you suspect relevant cross-session context exists, use session_search to recall it before asking them to repeat themselves.
> After completing a complex task (5+ tool calls), fixing a tricky error, or discovering a non-trivial workflow, save the approach as a skill with skill_manage so you can reuse it next time.

## Gaps Identified

1. **No trigger conditions**: "use fact_store to add facts" doesn't say WHEN to add facts
2. **Emphasis on other tools**: Persona section highlights session_search and skill_manage but not holographic memory
3. **Missing distinction**: No guidance on when to use fact_store vs session_search vs skill_manage
4. **Passive vs active**: Guidance is passive ("use it") not active ("after X, do Y")

## Recommended Improvements

1. Add explicit trigger conditions to holographic memory section
2. Add a sentence to persona section: "When the user expresses a preference, correction, or important information, use fact_store to store it for future sessions"
3. Create a memory triage guide (this skill) to help agents choose the right tool

## Impact
Without these improvements, agents default to "answer and forget" behavior, losing valuable cross-session context.
