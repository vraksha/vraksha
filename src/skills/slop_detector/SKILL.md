# Slop Detector

## What this skill does
Analyzes GitHub repositories for AI-generated code using commit forensics.

## Output format
Returns a YAML verdict with probability score, suspect files, and signal IDs.

## How to present results
- Always summarize verdict and probability score first
- Explain top 2-3 signals in plain English
- End with: "Was this verdict correct?" to collect feedback
- Use trigger phrase VERIFICATION_REQUIRED at the end

