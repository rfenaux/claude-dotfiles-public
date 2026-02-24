# Skill: risk-analyze

Analyze meeting transcripts for project risk signals using the Risk Detector tool.

## Triggers

- `/risk-analyze` - Analyze a Fathom transcript
- `/risk-analyze <file>` - Analyze specific file
- `/risk-analyze meeting` - Pull latest meeting from Fathom and analyze
- "analyze this meeting for risks"
- "what are the project risks in this transcript"
- "risk score for this meeting"

## Workflow

<risk-analyze>

### Step 1: Identify Source

Determine what to analyze:
1. If user provided a file path → use that file
2. If user said "meeting" or "latest" → fetch from Fathom MCP
3. If transcript JSON is in context → save to temp file

### Step 2: Fetch Transcript (if needed)

If fetching from Fathom:
```bash
# List recent meetings
mcp__fathom__list_meetings include_transcript=false

# Get transcript for specific meeting
mcp__fathom__get_transcript recording_id=<id>
```

Save the transcript to a temp file:
```bash
echo '<transcript_json>' > /tmp/transcript_to_analyze.json
```

### Step 3: Run Risk Detector

```bash
cd ~/dev-projects/risk-detector && source venv/bin/activate && risk-detector analyze <file> --format both
```

### Step 4: Interpret Results

Present the results with context:
- Overall risk score and severity
- Top 3 risk categories
- Key signals to watch
- Actionable recommendations

### Step 5: Optional Follow-up

Offer to:
- Save JSON report to a specific location
- Compare with previous meetings
- Deep-dive into specific risk category
- Create action items from recommendations

</risk-analyze>

## Example Usage

```
User: /risk-analyze
Claude: Which transcript would you like to analyze?
        1. Provide a file path
        2. Fetch latest meeting from Fathom
        3. Paste transcript JSON

User: /risk-analyze ~/downloads/meeting.json
Claude: [Runs analysis and shows report]

User: /risk-analyze meeting
Claude: [Lists recent Fathom meetings]
        Which meeting?
        1. DotDigital - Data Migration (today)
        2. Hubexo - Daily Alignment (today)
```

## Output Format

Always include:
1. **Score summary**: `79.7/100 CRITICAL`
2. **Category breakdown**: Top 3 categories with signal counts
3. **Key signals**: Top 5 matched patterns with timestamps/speakers
4. **Recommendations**: Numbered actionable items

## Dependencies

- Risk Detector: `~/dev-projects/risk-detector/`
- Fathom MCP: For fetching transcripts
- Python venv: Pre-configured in project

## Related

- `/action-extractor` - Extract action items from meetings
- Fathom MCP tools - `mcp__fathom__*`
