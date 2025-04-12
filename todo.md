# Sentra Enhancement Implementation Plan

## Examined Files
- [x] Extracted and examined the Sentra application files
- [x] Analyzed the backend code (FastAPI with OpenAI integration)
- [x] Analyzed the frontend code (React application)
- [x] Understood the feature requirements from pasted_content.txt

## Feature Implementation Plan

### Backend Changes
- [x] Update the AnalysisResult model to include new fields:
  - [x] Add risk_types field for risk classification
  - [x] Add suggested_reviewer field for reviewer recommendation
  - [x] Add rewritten_step field for the "Fix This Step" feature
- [x] Update the OpenAI prompt in the analyze endpoint to include:
  - [x] Risk type classification
  - [x] Reviewer recommendation
- [x] Add a new endpoint for the "Fix This Step" feature
- [x] Improve error handling for invalid inputs

### Frontend Changes
- [x] Add input validation:
  - [x] Empty input validation
  - [x] Minimum steps validation
- [x] Implement "Fix This Step" button on medium/high risk cards
  - [x] Add UI for displaying rewritten steps
- [x] Display risk type tags on result cards
- [x] Display reviewer recommendation on result cards
- [x] (Optional) Implement Compare Versions Mode
  - [x] Add UI for comparing workflow versions
  - [x] Show differences in risk levels

### Testing
- [x] Test backend changes
- [x] Test frontend changes
- [ ] Test all features together
- [ ] Verify UI consistency

### Packaging
- [ ] Package the enhanced application
- [ ] Prepare final zip file for delivery
