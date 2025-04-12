import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Union
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

class FixStepRequest(BaseModel):
    step: str
    risk: str
    recommendation: str
    reason: str
    use_mock: Optional[bool] = False

class AnalysisResult(BaseModel):
    step: str
    risk: str
    recommendation: str
    reason: str
    risk_types: List[str] = []  # Legal, Ethical, Bias, Privacy, Transparency
    suggested_reviewer: str = ""  # HR, Legal, Ethics Advisor, Data Analyst, Engineering, Product Manager
    rewritten_step: str = ""  # For the "Fix This Step" feature

# Mock responses for testing without API calls
MOCK_RESPONSES = {
    "AI scans resumes": {
        "risk": "low",
        "recommendation": "Continue with automated scanning, but periodically audit for bias",
        "reason": "Initial scanning is low risk as it's just collecting data, not making decisions",
        "risk_types": ["Bias", "Privacy"],
        "suggested_reviewer": "HR",
        "rewritten_step": "AI scans resumes with periodic bias audits and clear data retention policies"
    },
    "Filters top 20%": {
        "risk": "medium",
        "recommendation": "Add human review of filtering criteria and periodic audits",
        "reason": "Automated filtering may introduce bias based on the criteria used",
        "risk_types": ["Bias", "Ethical", "Transparency"],
        "suggested_reviewer": "HR",
        "rewritten_step": "AI suggests top 20% candidates for human review based on transparent criteria"
    },
    "Auto-rejects bottom 80%": {
        "risk": "high",
        "recommendation": "Add human reviewer for rejections or sample-based review",
        "reason": "Automated rejection without human oversight may violate employment regulations and introduce bias",
        "risk_types": ["Legal", "Ethical", "Bias"],
        "suggested_reviewer": "Legal",
        "rewritten_step": "Flag bottom 80% for human review before rejection, with clear reasoning provided"
    },
    "Sends interview invites": {
        "risk": "medium",
        "recommendation": "Have human approve final invite list",
        "reason": "Automated invitations may miss qualified candidates due to algorithm limitations",
        "risk_types": ["Bias", "Transparency"],
        "suggested_reviewer": "HR",
        "rewritten_step": "Prepare interview invite list for human approval before sending"
    },
    "AI scans user content": {
        "risk": "low",
        "recommendation": "Continue with automated scanning, but have clear appeal process",
        "reason": "Initial content scanning is low risk as it's just flagging for review",
        "risk_types": ["Privacy", "Transparency"],
        "suggested_reviewer": "Data Analyst",
        "rewritten_step": "AI scans user content with transparent criteria and clear appeal process"
    },
    "Flags potential violations": {
        "risk": "low",
        "recommendation": "Maintain human review of flagged content",
        "reason": "Flagging for human review is appropriate and low risk",
        "risk_types": ["Ethical", "Transparency"],
        "suggested_reviewer": "Ethics Advisor",
        "rewritten_step": "AI flags potential violations for human review with clear reasoning"
    },
    "Auto-removes extreme content": {
        "risk": "high",
        "recommendation": "Implement human review before removal or immediate appeal process",
        "reason": "Automated content removal may violate free speech or remove legitimate content",
        "risk_types": ["Legal", "Ethical", "Transparency"],
        "suggested_reviewer": "Legal",
        "rewritten_step": "Flag extreme content for expedited human review before removal"
    },
    "Sends warnings to borderline cases": {
        "risk": "medium",
        "recommendation": "Have human review warnings before sending",
        "reason": "Automated warnings may cause user frustration if incorrectly applied",
        "risk_types": ["Transparency", "Ethical"],
        "suggested_reviewer": "Ethics Advisor",
        "rewritten_step": "Draft warnings for borderline cases for human review before sending"
    },
    "Restricts repeat offenders": {
        "risk": "high",
        "recommendation": "Require human approval for account restrictions",
        "reason": "Account restrictions have significant impact on users and require due process",
        "risk_types": ["Legal", "Ethical", "Transparency"],
        "suggested_reviewer": "Legal",
        "rewritten_step": "Recommend account restrictions for repeat offenders for human approval"
    },
    "AI collects financial data": {
        "risk": "medium",
        "recommendation": "Ensure proper data security and consent mechanisms",
        "reason": "Financial data collection involves privacy concerns and regulatory requirements",
        "risk_types": ["Privacy", "Legal"],
        "suggested_reviewer": "Data Analyst",
        "rewritten_step": "AI collects financial data with explicit consent and robust security measures"
    },
    "Calculates credit score": {
        "risk": "high",
        "recommendation": "Ensure algorithm is explainable and complies with regulations",
        "reason": "Credit scoring is heavily regulated and must be transparent and fair",
        "risk_types": ["Legal", "Transparency", "Bias"],
        "suggested_reviewer": "Legal",
        "rewritten_step": "Calculate explainable credit score using compliant algorithms with human oversight"
    },
    "Determines loan eligibility": {
        "risk": "high",
        "recommendation": "Require human review of eligibility decisions",
        "reason": "Loan eligibility decisions have significant financial impact and regulatory oversight",
        "risk_types": ["Legal", "Ethical", "Bias"],
        "suggested_reviewer": "Legal",
        "rewritten_step": "Suggest loan eligibility for human review with transparent reasoning"
    },
    "Sets interest rate": {
        "risk": "high",
        "recommendation": "Implement human review of interest rate determinations",
        "reason": "Interest rate setting may have discriminatory effects if not properly overseen",
        "risk_types": ["Legal", "Bias", "Transparency"],
        "suggested_reviewer": "Legal",
        "rewritten_step": "Recommend interest rates based on clear criteria for human approval"
    },
    "Auto-approves qualifying applications": {
        "risk": "high",
        "recommendation": "Add human review step before final approval",
        "reason": "Automated loan approval may miss nuances and has significant financial implications",
        "risk_types": ["Legal", "Ethical", "Transparency"],
        "suggested_reviewer": "Legal",
        "rewritten_step": "Flag qualifying applications for expedited human review and approval"
    }
}

# Default mock response for steps not in the predefined list
DEFAULT_MOCK_RESPONSE = {
    "risk": "medium",
    "recommendation": "Add human oversight to this step",
    "reason": "Automated decision-making without human oversight may introduce risks",
    "risk_types": ["Ethical", "Transparency"],
    "suggested_reviewer": "Ethics Advisor",
    "rewritten_step": "Implement this step with human oversight and clear documentation"
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
    
    Returns a list of analysis results with risk level, recommendations, explanations,
    risk types, suggested reviewer, and rewritten step.
    """
    results = []
    
    try:
        # Validate input
        if not request.steps or len(request.steps) == 0:
            raise HTTPException(status_code=400, detail="No workflow steps provided")
            
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
                        reason=mock_data["reason"],
                        risk_types=mock_data["risk_types"],
                        suggested_reviewer=mock_data["suggested_reviewer"],
                        rewritten_step=mock_data["rewritten_step"]
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
                    - Risk type classification
                    - Appropriate reviewer
                    
                    Output in JSON:
                    - "risk": low/medium/high
                    - "recommendation": (string)
                    - "reason": (short explanation)
                    - "risk_types": [array of applicable types from: Legal, Ethical, Bias, Privacy, Transparency]
                    - "suggested_reviewer": (one of: HR, Legal, Ethics Advisor, Data Analyst, Engineering, Product Manager)
                    - "rewritten_step": (rewritten version of the step that reduces legal, ethical, or safety risks while keeping its original goal intact)
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
                                reason=analysis_data.get("reason", "No explanation provided"),
                                risk_types=analysis_data.get("risk_types", []),
                                suggested_reviewer=analysis_data.get("suggested_reviewer", ""),
                                rewritten_step=analysis_data.get("rewritten_step", "")
                            )
                        )
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        results.append(
                            AnalysisResult(
                                step=step,
                                risk="unknown",
                                recommendation="Error processing this step",
                                reason="Could not parse AI response",
                                risk_types=["Transparency"],
                                suggested_reviewer="Engineering",
                                rewritten_step=""
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
                            reason=mock_data["reason"] + f" (API Error: {str(api_error)[:100]}...)",
                            risk_types=mock_data["risk_types"],
                            suggested_reviewer=mock_data["suggested_reviewer"],
                            rewritten_step=mock_data["rewritten_step"]
                        )
                    )
                
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing workflow: {str(e)}")
    
    return results

@app.post("/fix-step", response_model=AnalysisResult)
async def fix_workflow_step(request: FixStepRequest):
    """
    Rewrite a workflow step to reduce legal, ethical, or safety risks.
    
    Takes a step and its current analysis, and returns an updated analysis
    with a rewritten version of the step.
    
    Returns the updated analysis result with the rewritten step.
    """
    try:
        # Validate input
        if not request.step or not request.step.strip():
            raise HTTPException(status_code=400, detail="No workflow step provided")
            
        # Use mock responses if requested or if OpenAI API key is not available
        use_mock = request.use_mock or not openai_api_key
        
        if use_mock:
            # Use predefined mock responses or default if not found
            mock_data = MOCK_RESPONSES.get(request.step, DEFAULT_MOCK_RESPONSE)
            return AnalysisResult(
                step=request.step,
                risk=mock_data["risk"],
                recommendation=mock_data["recommendation"],
                reason=mock_data["reason"],
                risk_types=mock_data["risk_types"],
                suggested_reviewer=mock_data["suggested_reviewer"],
                rewritten_step=mock_data["rewritten_step"]
            )
        else:
            # Use OpenAI API for rewriting the step
            try:
                client = openai.OpenAI(api_key=openai_api_key)
                
                prompt = f"""
                You are an AI ethics and compliance assistant.
                
                Original Step: "{request.step}"
                Current Risk Level: {request.risk}
                Current Recommendation: "{request.recommendation}"
                Reason for Risk: "{request.reason}"
                
                Rewrite this step to reduce legal, ethical, or safety risks while keeping its original goal intact.
                
                Output in JSON:
                - "rewritten_step": (rewritten version of the step)
                - "risk": (new risk level: low/medium/high)
                - "recommendation": (updated recommendation)
                - "reason": (updated explanation)
                - "risk_types": [array of applicable types from: Legal, Ethical, Bias, Privacy, Transparency]
                - "suggested_reviewer": (one of: HR, Legal, Ethics Advisor, Data Analyst, Engineering, Product Manager)
                """
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Using 3.5-turbo to conserve credits
                    messages=[
                        {"role": "system", "content": "You are an AI ethics and compliance assistant that rewrites workflow steps to reduce risks."},
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
                    return AnalysisResult(
                        step=request.step,
                        risk=analysis_data.get("risk", request.risk),
                        recommendation=analysis_data.get("recommendation", request.recommendation),
                        reason=analysis_data.get("reason", request.reason),
                        risk_types=analysis_data.get("risk_types", []),
                        suggested_reviewer=analysis_data.get("suggested_reviewer", ""),
                        rewritten_step=analysis_data.get("rewritten_step", "")
                    )
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return AnalysisResult(
                        step=request.step,
                        risk=request.risk,
                        recommendation=request.recommendation,
                        reason=request.reason,
                        risk_types=["Transparency"],
                        suggested_reviewer="Engineering",
                        rewritten_step="Could not generate rewritten step due to processing error"
                    )
            except Exception as api_error:
                # If OpenAI API call fails, fall back to mock response
                mock_data = MOCK_RESPONSES.get(request.step, DEFAULT_MOCK_RESPONSE)
                return AnalysisResult(
                    step=request.step,
                    risk=mock_data["risk"],
                    recommendation=mock_data["recommendation"],
                    reason=mock_data["reason"] + f" (API Error: {str(api_error)[:100]}...)",
                    risk_types=mock_data["risk_types"],
                    suggested_reviewer=mock_data["suggested_reviewer"],
                    rewritten_step=mock_data["rewritten_step"]
                )
                
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fixing workflow step: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
