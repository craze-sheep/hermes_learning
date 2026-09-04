---
name: ielts-speaking-prep
description: "Manage IELTS speaking topic banks (Part 1/2/3), reconcile missing topics from visual sources, restructure numbered topic files, design minimum-story coverage strategies, and write study guides. Use when working with IELTS cue cards, topic lists, or speaking practice materials."
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ielts, speaking, topic-bank, study-prep, oral-exam]
    related_skills: [chinese-platform-research]
---

# IELTS Speaking Prep

## Overview

Manage and optimize IELTS speaking topic banks. Covers three main workflows:
1. **Topic bank reconciliation** — compare screenshots/images of topic lists with text files to find missing or mismatched entries
2. **Topic bank restructuring** — renumber, merge sections, normalize naming across large topic files
3. **Minimum-story coverage** — analyze N topics to find the fewest real-life stories that can naturally cover all of them

This skill is designed for the project at `/home/lzy/project/口语练习/题库/` but the techniques apply to any oral exam topic bank.

## When to Use

- User asks to compare a screenshot of topics with a text/JSON/CSV topic file
- User needs to restructure or renumber a large topic list
- User wants to minimize the number of stories/prepared answers for many topics
- User asks about IELTS speaking format, timing, scoring, or strategies
- User is building study materials for Part 1, Part 2, or Part 3

Don't use for: writing practice answers, grading pronunciation, or non-IELTS oral exams (TOEFL, PTE — different formats).

## IELTS Speaking Quick Reference

### Part 2 Format (Long Turn)

```
Cue Card handed to candidate + paper/pen
        ↓
    1 minute preparation (notes only, no full sentences)
        ↓
    1-2 minute monologue (examiner stops at 2 min)
        ↓
    1-2 brief follow-up questions from examiner
```

**Scoring (4 criteria, 25% each):**
- Fluency & Coherence
- Lexical Resource
- Grammatical Range & Accuracy
- Pronunciation

**Cue Card structure:**
```
Describe [topic]

You should say:
  - [bullet 1]  ← must cover
  - [bullet 2]  ← must cover
  - [bullet 3]  ← must cover
  - And explain [bullet 4]  ← most important, go deepest here
```

### Key Timing Rules

- Preparation: exactly 1 minute
- Target speaking time: 1 min 30 sec – 2 min
- Under 1 minute = **severe score penalty**
- Examiner cuts you off at 2 min = normal, don't panic
- Write KEYWORDS only during prep, never full sentences

### Answer Strategies

1. **5W1H Expansion**: Add When/Where/Who/What/Why/How beyond the card's bullets
2. **Storytelling > Opinions**: Tell a specific anecdote, don't list generic views
3. **Past-Present-Future**: For opinion/wish topics without a specific event
4. **Feelings-Reasons-Examples**: Expand each bullet with emotion → cause → concrete example

## Workflow: Topic Bank Reconciliation

When user provides a screenshot/image of a topic list and a text file to compare:

1. **Extract topics from image** using `vision_analyze` with a precise prompt:
   ```
   List ALL topic items visible in this screenshot. Include every single
   checkbox item text in order from top to bottom, left to right across
   all columns. Be thorough and don't miss any.
   ```

2. **Parse topics from text file** using `execute_code` with regex:
   ```python
   import re
   # Match numbered items like "1. Topic Name"
   m = re.match(r'^(\d+)\.\s+(.+)$', line.strip())
   ```

3. **Compare systematically** — check each image topic against the text file:
   - Exact match → OK
   - Minor wording difference → flag as "variant" (e.g. "长时间未收到回复" vs "长时间不回消息的人")
   - No match → flag as "missing"

4. **Check for truncated images** — if the bottom row has fewer items than expected, ask user if the image is complete or if there's more below the fold.

5. **Get topic card details** for missing topics — search for images in related directories (like `缺失/` folder) and use `vision_analyze` to extract the cue card text and follow-up questions.

6. **Report findings** as a clear diff: missing items, variant names, total counts.

## Workflow: Topic Bank Restructuring

When merging sections or renumbering a large topic file:

1. **Read the full file** and parse topic blocks (each topic = header + indented content until next header)
2. **Determine new order** — if merging "新题" and "保留话题" sections, the user usually wants a single sequential numbering
3. **Use `execute_code`** for bulk renumbering — regex replace the leading number in each block
4. **Strip section headers** (## 本季新题, ## 保留话题, etc.)
5. **Update the file header** (total count, date)
6. **Verify** by checking first, middle, and last topics after writing

### Pitfall: Line-number prefixes from read_file

The `read_file` tool returns content with line-number prefixes like `     1|content`. Always strip these before processing:

```python
import re
lines = []
for line in raw.split('\n'):
    m = re.match(r'^\s*\d+\|(.*)$', line)
    if m:
        lines.append(m.group(1))
    else:
        lines.append(line)
```

## Workflow: Minimum-Story Coverage

This is the highest-value technique for IELTS Part 2 prep: given N topics, find the fewest real-life stories that can naturally cover all of them.

### Step 0: Evaluate Existing Work First

Before writing new content, evaluate any existing preparation files. Write findings to `评价.md`:
1. **Coverage** — are all topics assigned? Any missing?
2. **Bullet-point match** — for each topic, does the answer cover ALL cue card bullets? List failures.
3. **Naturalness** — which topics feel forced?
4. **Detail level** — are answers specific (names, places, dates) or generic?
5. **English quality** — natural conversational? Chinglish? Essay-like?
6. **Examiner understandability** — would a non-Chinese examiner follow this?
7. **Story count** — any room to compress? Are boundaries clean?

Fix issues found before producing final output. User preference: "让它先评价，写入评价.md，再重新写或者修改"

### Step-by-Step Process

1. **Extract all topics** with their cue card prompts (the "Describe..." line)
2. **Categorize** by what they require:
   - Person topics (need a specific person)
   - Place topics (need a specific location)
   - Experience/event topics (need a specific event)
   - Thing/object topics (need a specific item or opinion)
3. **Identify story nuclei** — rich real-life experiences with multiple facets:
   - A university project/competition (team, tech problems, decisions, outcomes)
   - A trip to a city (buildings, food, shopping, transport, companions)
   - A specific friend/family member (their qualities, shared experiences)
   - A media experience (movie, TV show, video, book)
   - A family visit (home, traditions, heirlooms, environment)
4. **Map topics to stories** — for each topic, assign it to the most natural story
5. **Check for forced connections** — if a topic's link to a story requires mental gymnastics, move it elsewhere
6. **Verify complete coverage** — ensure every topic is assigned to exactly one story
7. **Bullet-point verification (CRITICAL).** For EVERY topic, extract the full cue card
   bullet points and verify that EACH bullet can be answered from the assigned story.
   Use `execute_code` to systematically parse all cue card bullets from the topic bank
   file and cross-check against story assignments:
   ```python
   # Parse bullets between "题卡" and "后续小问" for each topic
   # For each bullet, verify the story provides a natural answer
   # Flag bullets that require fabrication or mental gymnastics
   ```
   If 2+ bullets don't fit, MOVE the topic to a different story. Don't rationalize.
8. **Optimize** — try to merge stories if possible (e.g., trip + family visit in same location)

### Quality Criteria for Story-Topic Mapping

A mapping is **natural** if:
- You can describe the topic by focusing on one aspect of the story
- The story provides concrete details (names, places, dates, emotions) for the topic
- You don't need to invent details that weren't part of the original story
- **Every bullet point on the cue card** can be answered from the story without fabrication

A mapping is **forced** if:
- The connection requires "well, technically..." reasoning
- The story would need significant new details to cover the topic
- A listener would be confused by the connection
- **Any bullet point** requires inventing details not present in the story

### Example: 3-Story Coverage for 55 Part 2 Topics

```
Story 1: University project/competition (22 topics)
  → tech problems, teamwork, decisions, career ambitions

Story 2: City trip + visiting grandparents (22 topics)
  → buildings, food, shopping, family home, nature, laws

Story 3: Childhood friend studying medicine (11 topics)
  → friendship, career, personal qualities, shared experiences
```

### Example: 6-Story Coverage (preferred when 3 stories have forced connections)

```
Story 1: Gaokao repeat year (7 topics)
  → #2,12,18,28,35,48,50

Story 2: University competitions & research (9 topics)
  → #4,9,13,19,20,36,42,46,47

Story 3: Cloud teaching in Yunnan (8 topics)
  → #1,3,14,23,29,34,37,52

Story 4: Xi'an family visit (17 topics)
  → #5,6,8,15,17,21,24,25,30,31,32,38,43,44,49,51,53

Story 5: Childhood friend (9 topics)
  → #7,10,11,16,22,26,39,41,45

Story 6: College daily life (5 topics, independent)
  → #27,33,40,54,55
```

See `references/minimum-story-coverage.md` for detailed mapping tables.

## Study Guide Template

When creating a study guide for IELTS speaking, include these sections:

1. **Exam format & timing** — exact numbers, flow diagram
2. **Cue card structure** — what the card looks like, what must be covered
3. **Scoring criteria** — 4 dimensions with weights
4. **Answer strategies** — 5W1H, storytelling, Past-Present-Future, Feelings-Reasons-Examples
5. **Common pitfalls** — what loses points
6. **Prep advice** — recording, timer practice, keyword notes
7. **Story coverage plan** — the minimum stories mapped to all topics

## User Preferences

- **Use real autobiographical material** when available. If the user has written an autobiography,
  personal history, or provided background information, base stories on their REAL experiences
  rather than generic fictional ones. Real stories are easier to remember and deliver naturally
  during the exam. Ask the user for personal background material before inventing stories.
- **Transparent about forced connections.** When a topic's cue card bullets can't be fully
  answered from a story, explicitly flag it rather than silently assuming the user will fill
  in the gaps. Present a clear table of problematic topics with specific bullet-point analysis.
- **Globally recognizable content for examiner.** When selecting specific examples (movies, TV
  shows, ads, celebrities), choose content the IELTS examiner (likely a non-Chinese English
  speaker) will know or easily understand. Prefer international blockbusters over domestic hits,
  global brands over local ones. If using local content, describe it clearly enough for a
  foreign listener. Direct user quote: "你还要考虑到考官是否能理解啊，应该选一些大众的，
  全球的，容易理解的"
- **No forced connections — "没有维和感".** The user explicitly wants zero awkwardness in
  story-topic mappings. If a connection requires "well, technically..." reasoning, it's forced.
  Split into more stories (up to 6 is acceptable) rather than rationalizing weak connections.
  Direct user quote: "争取没有维和感"
- **Write complete stories first, then adapt.** The preferred workflow is: (1) write full
  story narratives in a separate file (故事.md), (2) then adapt each story to the specific
  cue card topics. This ensures story coherence before topic-level optimization.
- **Stories file in user's language, answers in English.** The story narratives (故事.md)
  should be written in the user's native language for easier memorization. The sample answers
  (part2初始版.md) should be in English since that's the exam language.
- **Embed full autobiography context when delegating.** When using subagents to generate
  sample answers, include the complete autobiography/personal details in the context field.
  Don't just reference a file path — subagents can't access the parent conversation's memory.
  Include names, dates, places, relationships, and specific events as inline text.
- **Evaluate before writing (先评价再修改).** When asked to redo or improve existing work,
  first evaluate what exists and write findings to 评价.md. Then fix the issues found.
  Don't start from scratch without understanding what was wrong.

## Common Pitfalls

1. **Comparing Chinese topic names loosely.** "长时间未收到回复" and "长时间不回消息的人" look different but describe the same topic card. Always compare the English "Describe..." line to confirm.

2. **Forgetting to check for truncated screenshots.** If the last row of a grid has fewer items than other rows, the image may be cut off. Ask before assuming it's complete.

3. **Using `skill_manage` or `read_file` in `execute_code`.** The `read_file` from `hermes_tools` has a different return format than the standalone `read_file` tool. In `execute_code`, use Python's `open()` directly.

4. **Forcing story-topic connections.** If connecting "environmental law" to a coding competition requires "well, I learned about e-waste...", it's forced. Move that topic to a story where the connection is natural (e.g., saw pollution while traveling).

5. **Too many topics in one story.** Over 20 topics per story risks confusion during the exam. The test-taker needs to quickly locate the right angle. Split when natural — the user is better served by 6 clean stories than 3 bloated ones. Don't force a minimum story count.

6. **Refusing to split because "3 is the minimum."** The user may be fine with 4-6 stories. When bullet-point verification reveals forced connections, the right move is to SPLIT the story, not to rationalize the connection. Ask the user what story count they're comfortable with before designing.

7. **Topics that need fabricated specifics.** Some topics (celebrity ads, movies watched, videos seen) have no autobiographical anchor. Flag them explicitly in a "needs preparation" table: the user only needs to memorize one specific name/title per topic, then the rest flows naturally.

8. **Not verifying complete coverage.** Always count: total topics assigned across all stories must equal the total number of topics. One missing topic = one unprepared question on exam day.

9. **Only checking topic names, not cue card bullet points (CRITICAL).** When mapping stories to topics, it's NOT enough to check whether the topic NAME fits the story. Each topic has a cue card with 3-4 specific bullet points ("You should say: ..."). EVERY bullet point must be answerable from the story. For example, topic #21 "拥有成功事业的人" might seem to fit a competition story (teammate who's successful), but the cue card asks "Why and how he/she started the business" + "What business he/she does" — which requires someone who literally started a business, not just a successful person. Always extract the full cue card bullets and verify each one against the story before finalizing the mapping.

8. **Rushing through descriptive bullets to get to "And explain."** The instruction "And explain part should be longest" does NOT mean the descriptive bullets should be one sentence each. The descriptive parts (who/what/where/when/how) must be specific and thorough — with names, places, times, numbers, sensory details. Only after describing clearly should you spend extra time on the reflective "And explain" part. Think of it as: 60% describing (clear, specific, detailed) + 40% reflecting (feelings, reasons, lessons). User said: "只是描述量要描述清楚一下"

11. **Using Chinese-specific content the examiner won't know.** When topics require specific examples (movies, TV shows, ads, celebrities), avoid purely Chinese content that a foreign examiner won't recognize. Chinese dramas, Chinese celebrity names, or local brand ads need extra explanation. Prefer globally known alternatives: international movies (Oppenheimer over 热辣滚烫), global brands (Huawei over a local brand), internationally known TV shows (The Good Doctor over 非凡医者). If you must use local content, describe it clearly enough that a foreign listener can follow — don't just drop a Chinese name and expect the examiner to know it.

12. **Not writing the full stories before adapting to topics.** The workflow matters: (1) write complete story narratives first (故事.md), (2) then adapt each story to specific cue cards. Writing stories first ensures narrative coherence. Jumping straight to topic-by-topic answers produces disjointed, template-like responses.

13. **Subagent batches for large answer sets.** When writing 55+ sample answers, delegate to subagents in parallel batches (e.g., 5 batches of 11 topics each). Each batch gets the story context and cue card details, writes to a temp file, then merge at the end. Much faster than writing sequentially.
