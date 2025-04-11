import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import openai
import json

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Sentra API", description="API for analyzing AI workflow steps")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")

# Define data models
class WorkflowStep(BaseModel):
    step: str
    
class WorkflowRequest(BaseModel):
    steps: List[str]
    use_mock: Optional[bool] = False  # New parameter to toggle mock responses

class AnalysisResult(BaseModel):
    step: str
    risk: str
    recommendation: str
    reason: str

# Mock responses for testing without API calls
MOCK_RESPONSES = {
    "AI scans resumes": {
        "risk": "low",
        "recommendation": "Continue with automated scanning, but periodically audit for bias",
        "reason": "Initial scanning is low risk as it's just collecting data, not making decisions"
    },
    "Filters top 20%": {
        "risk": "medium",
        "recommendation": "Add human review of filtering criteria and periodic audits",
        "reason": "Automated filtering may introduce bias based on the criteria used"
    },
    "Auto-rejects bottom 80%": {
        "risk": "high",
        "recommendation": "Add human reviewer for rejections or sample-based review",
        "reason": "Automated rejection without human oversight may violate employment regulations and introduce bias"
    },
    "Sends interview invites": {
        "risk": "medium",
        "recommendation": "Have human approve final invite list",
        "reason": "Automated invitations may miss qualified candidates due to algorithm limitations"
    },
    "AI scans user content": {
        "risk": "low",
        "recommendation": "Continue with automated scanning, but have clear appeal process",
        "reason": "Initial content scanning is low risk as it's just flagging for review"
    },
    "Flags potential violations": {
        "risk": "low",
        "recommendation": "Maintain human review of flagged content",
        "reason": "Flagging for human review is appropriate and low risk"
    },
    "Auto-removes extreme content": {
        "risk": "high",
        "recommendation": "Implement human review before removal or immediate appeal process",
        "reason": "Automated content removal may violate free speech or remove legitimate content"
    },
    "Sends warnings to borderline cases": {
        "risk": "medium",
        "recommendation": "Have human review warnings before sending",
        "reason": "Automated warnings may cause user frustration if incorrectly applied"
    },
    "Restricts repeat offenders": {
        "risk": "high",
        "recommendation": "Require human approval for account restrictions",
        "reason": "Account restrictions have significant impact on users and require due process"
    },
    "AI collects financial data": {
        "risk": "medium",
        "recommendation": "Ensure proper data security and consent mechanisms",
        "reason": "Financial data collection involves privacy concerns and regulatory requirements"
    },
    "Calculates credit score": {
        "risk": "high",
        "recommendation": "Ensure algorithm is explainable and complies with regulations",
        "reason": "Credit scoring is heavily regulated and must be transparent and fair"
    },
    "Determines loan eligibility": {
        "risk": "high",
        "recommendation": "Require human review of eligibility decisions",
        "reason": "Loan eligibility decisions have significant financial impact and regulatory oversight"
    },
    "Sets interest rate": {
        "risk": "high",
        "recommendation": "Implement human review of interest rate determinations",
        "reason": "Interest rate setting may have discriminatory effects if not properly overseen"
    },
    "Auto-approves qualifying applications": {
        "risk": "high",
        "recommendation": "Add human review step before final approval",
        "reason": "Automated loan approval may miss nuances and has significant financial implications"
    }
}

# Default mock response for steps not in the predefined list
DEFAULT_MOCK_RESPONSE = {
    "risk": "medium",
    "recommendation": "Add human oversight to this step",
    "reason": "Automated decision-making without human oversight may introduce risks"
}

@app.get("/")
async def root():
    return {"message": "Welcome to Sentra API - AI Workflow Auditor"}

@app.post("/analyze", response_model=List[AnalysisResult])
async def analyze_workflow(request: WorkflowRequest):
    """
    Analyze a list of workflow steps for risk and provide recommendations.
    
    Each step is either processed through the OpenAI API or uses mock responses
    based on the use_mock parameter.
    
    Returns a list of analysis results with risk level, recommendations, and explanations.
    """
    results = []
    
    try:
        # Use mock responses if requested or if OpenAI API key is not available
        use_mock = request.use_mock or not openai_api_key
        
        for step in request.steps:
            # Skip empty steps
            if not step.strip():
                continue
                
            if use_mock:
                # Use predefined mock responses or default if not found
                mock_data = MOCK_RESPONSES.get(step, DEFAULT_MOCK_RESPONSE)
                results.append(
                    AnalysisResult(
                        step=step,
                        risk=mock_data["risk"],
                        recommendation=mock_data["recommendation"],
                        reason=mock_data["reason"]
                    )
                )
            else:
                # Use OpenAI API for analysis
                try:
                    client = openai.OpenAI(api_key=openai_api_key)
                    
                    prompt = f"""
                    You are an AI ethics and compliance assistant.
                    
                    Step: "{step}"
                    
                    Analyze this step for:
                    - How critical the decision is
                    - Whether human oversight is needed
                    - Legal or ethical risk
                    - Auditability
                    
                    Output in JSON:
                    - "risk": low/medium/high
                    - "recommendation": (string)
                    - "reason": (short explanation)
                    """
                    
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",  # Using 3.5-turbo to conserve credits
                        messages=[
                            {"role": "system", "content": "You are an AI ethics and compliance assistant that analyzes workflow steps and outputs JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,  # Lower temperature for more consistent outputs
                        response_format={"type": "json_object"}
                    )
                    
                    # Extract the JSON response
                    analysis = response.choices[0].message.content
                    
                    # Process the response into our data model
                    try:
                        analysis_data = json.loads(analysis)
                        results.append(
                            AnalysisResult(
                                step=step,
                                risk=analysis_data.get("risk", "unknown"),
                                recommendation=analysis_data.get("recommendation", "No specific recommendation"),
                                reason=analysis_data.get("reason", "No explanation provided")
                            )
                        )
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        results.append(
                            AnalysisResult(
                                step=step,
                                risk="unknown",
                                recommendation="Error processing this step",
                                reason="Could not parse AI response"
                            )
                        )
                except Exception as api_error:
                    # If OpenAI API call fails, fall back to mock response
                    mock_data = MOCK_RESPONSES.get(step, DEFAULT_MOCK_RESPONSE)
                    results.append(
                        AnalysisResult(
                            step=step,
                            risk=mock_data["risk"],
                            recommendation=mock_data["recommendation"] + " (Mock response due to API error)",
                            reason=mock_data["reason"] + f" (API Error: {str(api_error)[:100]}...)"
                        )
                    )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing workflow: {str(e)}")
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
