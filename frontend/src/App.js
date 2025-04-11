import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Row, Col, Form, Button, Card, Alert, Spinner, Nav, Tab, Accordion, InputGroup, FormControl, Badge, OverlayTrigger, Tooltip, Modal, ProgressBar, ButtonGroup, ToggleButton } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import html2pdf from 'html2pdf.js';

function App() {
  const [workflowSteps, setWorkflowSteps] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('analyze');
  const [history, setHistory] = useState([]);
  const [loadingAnimation, setLoadingAnimation] = useState(false);
  const [sensitivityLevel, setSensitivityLevel] = useState('medium');
  const [searchTerm, setSearchTerm] = useState('');
  const [searchRiskFilter, setSearchRiskFilter] = useState('all');
  const [showDetailedExplanation, setShowDetailedExplanation] = useState(false);
  const [currentExplanationStep, setCurrentExplanationStep] = useState(null);
  
  // Example workflows
  const exampleWorkflows = {
    hiring: "1. AI scans resumes\n2. Filters top 20%\n3. Auto-rejects bottom 80%\n4. Sends interview invites",
    moderation: "1. AI scans user content\n2. Flags potential violations\n3. Auto-removes extreme content\n4. Sends warnings to borderline cases\n5. Restricts repeat offenders",
    loan: "1. AI collects financial data\n2. Calculates credit score\n3. Determines loan eligibility\n4. Sets interest rate\n5. Auto-approves qualifying applications"
  };

  // Load history from sessionStorage on component mount
  useEffect(() => {
    const savedHistory = sessionStorage.getItem('workflowHistory');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  const loadExample = (example) => {
    setWorkflowSteps(exampleWorkflows[example]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLoadingAnimation(true);
    setError('');
    
    // Split the input by new lines and filter out empty lines
    const steps = workflowSteps
      .split('\n')
      .map(step => step.trim())
      .filter(step => step.length > 0)
      .map(step => {
        // Remove numbering if present (e.g., "1. Step" becomes "Step")
        const match = step.match(/^\\d+\\.\\s*(.+)$/);
        return match ? match[1] : step;
      });
    
    if (steps.length === 0) {
      setError('Please enter at least one workflow step.');
      setLoading(false);
      setLoadingAnimation(false);
      return;
    }
    
    try {
      // Add sensitivity level to the request
      const response = await axios.post('http://localhost:8000/analyze', {
        steps: steps,
        sensitivity: sensitivityLevel
      });
      
      // Apply sensitivity filter to results (simulated since backend doesn't support it yet)
      let adjustedResults = response.data.map(result => {
        // This is a simulation of how sensitivity would affect results
        // In a real implementation, the backend would handle this
        let adjustedRisk = result.risk.toLowerCase();
        
        if (sensitivityLevel === 'strict' && adjustedRisk === 'low') {
          adjustedRisk = 'medium';
        } else if (sensitivityLevel === 'strict' && adjustedRisk === 'medium') {
          adjustedRisk = 'high';
        } else if (sensitivityLevel === 'low' && adjustedRisk === 'medium') {
          adjustedRisk = 'low';
        } else if (sensitivityLevel === 'low' && adjustedRisk === 'high') {
          adjustedRisk = 'medium';
        }
        
        return {
          ...result,
          risk: adjustedRisk
        };
      });
      
      setResults(adjustedResults);
      
      // Save to history
      const newWorkflow = {
        id: Date.now(),
        date: new Date().toLocaleString(),
        steps: workflowSteps,
        results: adjustedResults,
        sensitivity: sensitivityLevel
      };
      
      const updatedHistory = [newWorkflow, ...history].slice(0, 10); // Keep last 10 instead of 3
      setHistory(updatedHistory);
      sessionStorage.setItem('workflowHistory', JSON.stringify(updatedHistory));
      
    } catch (err) {
      console.error('Error analyzing workflow:', err);
      setError('Error analyzing workflow. Please try again.');
    } finally {
      setLoading(false);
      setTimeout(() => {
        setLoadingAnimation(false);
      }, 500); // Add a small delay to make the animation more noticeable
    }
  };

  // Helper function to get badge color based on risk level
  const getRiskBadgeColor = (risk) => {
    switch (risk.toLowerCase()) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'danger';
      default:
        return 'secondary';
    }
  };

  // Helper function to get risk icon
  const getRiskIcon = (risk) => {
    switch (risk.toLowerCase()) {
      case 'low':
        return '✅';
      case 'medium':
        return '⚠️';
      case 'high':
        return '🔴';
      default:
        return '❓';
    }
  };

  // Calculate summary statistics
  const calculateSummary = (resultsData = results) => {
    if (!resultsData.length) return null;
    
    const counts = {
      low: resultsData.filter(r => r.risk.toLowerCase() === 'low').length,
      medium: resultsData.filter(r => r.risk.toLowerCase() === 'medium').length,
      high: resultsData.filter(r => r.risk.toLowerCase() === 'high').length,
      unknown: resultsData.filter(r => !['low', 'medium', 'high'].includes(r.risk.toLowerCase())).length
    };
    
    return counts;
  };

  // Calculate cumulative risk score
  const calculateRiskScore = (resultsData = results) => {
    if (!resultsData.length) return null;
    
    // Assign weights to different risk levels
    const riskWeights = {
      low: 1,
      medium: 2,
      high: 3
    };
    
    // Calculate weighted sum
    let totalWeight = 0;
    let maxPossibleWeight = 0;
    
    resultsData.forEach(result => {
      const riskLevel = result.risk.toLowerCase();
      if (riskWeights[riskLevel]) {
        totalWeight += riskWeights[riskLevel];
      }
      // Maximum possible weight if all were high risk
      maxPossibleWeight += riskWeights.high;
    });
    
    // Calculate score as percentage of maximum risk (inverted so higher is riskier)
    const riskPercentage = Math.round((totalWeight / maxPossibleWeight) * 100);
    
    // Return score out of 100
    return {
      score: riskPercentage,
      maxScore: 100
    };
  };

  // Function to handle PDF download
  const handleDownloadPDF = () => {
    const element = document.getElementById('results-container');
    const opt = {
      margin: 10,
      filename: 'sentra-workflow-analysis.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };
    
    html2pdf().set(opt).from(element).save();
  };

  // Function to show detailed explanation modal
  const showExplanation = (step) => {
    setCurrentExplanationStep(step);
    setShowDetailedExplanation(true);
  };

  // Function to get detailed explanation for a step
  const getDetailedExplanation = (step) => {
    // In a real implementation, this would call the GPT API
    // For now, we'll generate a more detailed version of the existing reason
    return `
      <h5>Detailed Risk Analysis</h5>
      <p>The step "${step.step}" has been identified as ${step.risk.toUpperCase()} RISK for the following reasons:</p>
      <ul>
        <li><strong>Primary concern:</strong> ${step.reason}</li>
        <li><strong>Potential impact:</strong> ${
          step.risk.toLowerCase() === 'high' 
            ? 'This could have significant legal, ethical, or business implications if not properly managed.'
            : step.risk.toLowerCase() === 'medium'
              ? 'This presents moderate concerns that should be addressed to ensure compliance and ethical AI use.'
              : 'While the risk is low, best practices still suggest human oversight for quality assurance.'
        }</li>
        <li><strong>Industry standards:</strong> ${
          step.risk.toLowerCase() === 'high'
            ? 'Most regulatory frameworks require human oversight for this type of decision.'
            : step.risk.toLowerCase() === 'medium'
              ? 'Industry guidelines recommend human review for this type of process.'
              : 'This aligns with standard industry practices but periodic review is still recommended.'
        }</li>
      </ul>
      <h5>Recommendation Details</h5>
      <p>${step.recommendation}</p>
      <p>Consider implementing the following additional safeguards:</p>
      <ul>
        <li>${
          step.risk.toLowerCase() === 'high'
            ? 'Regular audits and documentation of all decisions made by this process'
            : step.risk.toLowerCase() === 'medium'
              ? 'Sampling of outputs for quality assurance and bias detection'
              : 'Periodic review of the process effectiveness and outcomes'
        }</li>
        <li>Clear escalation paths for edge cases</li>
        <li>Transparent communication with affected stakeholders</li>
      </ul>
    `;
  };

  // Filter history based on search term and risk filter
  const filteredHistory = history.filter(item => {
    // Filter by search term
    const matchesSearch = searchTerm === '' || 
      item.steps.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.results.some(r => 
        r.step.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.recommendation.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.reason.toLowerCase().includes(searchTerm.toLowerCase())
      );
    
    // Filter by risk level
    const matchesRisk = searchRiskFilter === 'all' ||
      item.results.some(r => r.risk.toLowerCase() === searchRiskFilter);
    
    return matchesSearch && matchesRisk;
  });

  // Render the loading animation
  const renderLoadingAnimation = () => {
    return (
      <div className="text-center my-5 py-5">
        <div className="mb-3">
          <Spinner animation="border" role="status" variant="primary" style={{ width: '3rem', height: '3rem' }}>
            <span className="visually-hidden">Loading...</span>
          </Spinner>
        </div>
        <h4>Analyzing<span className="dot-animation">...</span></h4>
      </div>
    );
  };

  // Render the results section
  const renderResults = (resultsData = results, showDownloadButton = true, isHistoryItem = false) => {
    if (!resultsData.length) return null;
    
    const summaryData = calculateSummary(resultsData);
    const riskScore = calculateRiskScore(resultsData);
    
    return (
      <div id={isHistoryItem ? `history-results-${isHistoryItem}` : "results-container"}>
        <Row className="mb-4">
          <Col>
            <div className="d-flex justify-content-between align-items-center mb-3">
              <h3>Analysis Results</h3>
              {showDownloadButton && (
                <Button variant="outline-primary" onClick={handleDownloadPDF}>
                  <i className="bi bi-download me-2"></i>
                  Download Report as PDF
                </Button>
              )}
            </div>
            
            {summaryData && (
              <Card className="mb-3">
                <Card.Body>
                  <Row>
                    <Col md={8}>
                      <h5>Risk Summary</h5>
                      <div className="d-flex justify-content-around">
                        <div className="text-center">
                          <div className="fs-4 text-success">{summaryData.low}</div>
                          <div>Low Risk</div>
                        </div>
                        <div className="text-center">
                          <div className="fs-4 text-warning">{summaryData.medium}</div>
                          <div>Medium Risk</div>
                        </div>
                        <div className="text-center">
                          <div className="fs-4 text-danger">{summaryData.high}</div>
                          <div>High Risk</div>
                        </div>
                      </div>
                    </Col>
                    <Col md={4} className="border-start">
                      <h5>Cumulative Risk</h5>
                      <div className="text-center mb-2">
                        <div className="fs-1 fw-bold">{riskScore.score}</div>
                        <div className="text-muted">out of {riskScore.maxScore}</div>
                      </div>
                      <ProgressBar>
                        <ProgressBar variant="success" now={riskScore.score < 33 ? riskScore.score : 33} max={100} />
                        <ProgressBar variant="warning" now={riskScore.score >= 33 && riskScore.score < 66 ? riskScore.score - 33 : (riskScore.score >= 66 ? 33 : 0)} max={100} />
                        <ProgressBar variant="danger" now={riskScore.score >= 66 ? riskScore.score - 66 : 0} max={100} />
                      </ProgressBar>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            )}
            
            {resultsData.map((result, index) => (
              <Card key={index} className={`mb-3 border-left-risk border-left-risk-${result.risk.toLowerCase()}`}>
                <Card.Body>
                  <div className="d-flex align-items-start">
                    <div className="risk-indicator me-3">
                      {getRiskIcon(result.risk)}
                    </div>
                    <div className="flex-grow-1">
                      <div className="d-flex justify-content-between align-items-center mb-2">
                        <h5 className="mb-0">{result.step}</h5>
                        <div className="d-flex align-items-center">
                          <Button 
                            variant="link" 
                            className="text-secondary p-0 me-2" 
                            onClick={() => showExplanation(result)}
                            title="Why is this risky?"
                          >
                            <i className="bi bi-question-circle"></i>
                          </Button>
                          <Alert variant={getRiskBadgeColor(result.risk)} className="mb-0 py-1 px-2">
                            {result.risk.toUpperCase()} RISK
                          </Alert>
                        </div>
                      </div>
                      <Card.Subtitle className="mb-2 text-muted">Recommendation</Card.Subtitle>
                      <Card.Text>{result.recommendation}</Card.Text>
                      <Card.Subtitle className="mb-2 text-muted">Reason</Card.Subtitle>
                      <Card.Text>{result.reason}</Card.Text>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            ))}
          </Col>
        </Row>
      </div>
    );
  };

  return (
    <Container className="py-4">
      <Row className="mb-4">
        <Col>
          <h1 className="text-center">Sentra</h1>
          <h4 className="text-center text-muted mb-4">Visual AI Workflow Auditor</h4>
          
          <Tab.Container id="main-tabs" activeKey={activeTab} onSelect={(k) => setActiveTab(k)}>
            <Nav variant="tabs" className="mb-3">
              <Nav.Item>
                <Nav.Link eventKey="analyze">Analyze Workflow</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="history">History</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="about">About Sentra</Nav.Link>
              </Nav.Item>
            </Nav>
            
            <Tab.Content>
              <Tab.Pane eventKey="analyze">
                <Card>
                  <Card.Body>
                    <Form onSubmit={handleSubmit}>
                      <Form.Group className="mb-3">
                        <Form.Label>Enter your AI workflow steps (one per line):</Form.Label>
                        <Form.Control
                          as="textarea"
                          rows={6}
                          value={workflowSteps}
                          onChange={(e) => setWorkflowSteps(e.target.value)}
                          placeholder="Example:&#10;1. AI scans resumes&#10;2. Filters top 20%&#10;3. Auto-rejects bottom 80%&#10;4. Sends interview invites"
                        />
                      </Form.Group>
                      
                      <Row className="mb-3">
                        <Col md={8}>
                          <div className="d-flex">
                            <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => loadExample('hiring')}>
                              Load Hiring Example
                            </Button>
                            <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => loadExample('moderation')}>
                              Load Moderation Example
                            </Button>
                            <Button variant="outline-secondary" size="sm" onClick={() => loadExample('loan')}>
                              Load Loan Example
                            </Button>
                          </div>
                        </Col>
                        <Col md={4}>
                          <Form.Group>
                            <Form.Label>Impact Sensitivity</Form.Label>
                            <div>
                              <ButtonGroup>
                                <ToggleButton
                                  id="sensitivity-low"
                                  type="radio"
                                  variant={sensitivityLevel === 'low' ? 'outline-success' : 'outline-secondary'}
                                  name="sensitivity"
                                  value="low"
                                  checked={sensitivityLevel === 'low'}
                                  onChange={(e) => setSensitivityLevel(e.currentTarget.value)}
                                >
                                  Low
                                </ToggleButton>
                                <ToggleButton
                                  id="sensitivity-medium"
                                  type="radio"
                                  variant={sensitivityLevel === 'medium' ? 'outline-warning' : 'outline-secondary'}
                                  name="sensitivity"
                                  value="medium"
                                  checked={sensitivityLevel === 'medium'}
                                  onChange={(e) => setSensitivityLevel(e.currentTarget.value)}
                                >
                                  Medium
                                </ToggleButton>
                                <ToggleButton
                                  id="sensitivity-strict"
                                  type="radio"
                                  variant={sensitivityLevel === 'strict' ? 'outline-danger' : 'outline-secondary'}
                                  name="sensitivity"
                                  value="strict"
                                  checked={sensitivityLevel === 'strict'}
                                  onChange={(e) => setSensitivityLevel(e.currentTarget.value)}
                                >
                                  Strict
                                </ToggleButton>
                              </ButtonGroup>
                            </div>
                          </Form.Group>
                        </Col>
                      </Row>
                      
                      <Button variant="primary" type="submit" disabled={loading}>
                        {loading ? (
                          <>
                            <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
                            <span className="ms-2">Analyzing...</span>
                          </>
                        ) : (
                          'Analyze Workflow'
                        )}
                      </Button>
                    </Form>
                  </Card.Body>
                </Card>
                
                {error && (
                  <Alert variant="danger" className="mt-3">
                    {error}
                  </Alert>
                )}
                
                {loadingAnimation ? (
                  renderLoadingAnimation()
                ) : (
                  results.length > 0 && renderResults()
                )}
              </Tab.Pane>
              
              <Tab.Pane eventKey="history">
                <Card>
                  <Card.Body>
                    <h5>Workflow Analysis History</h5>
                    
                    <Row className="mb-3">
                      <Col md={8}>
                        <InputGroup>
                          <InputGroup.Text>
                            <i className="bi bi-search"></i>
                          </InputGroup.Text>
                          <FormControl
                            placeholder="Search workflows..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                          />
                        </InputGroup>
                      </Col>
                      <Col md={4}>
                        <Form.Select 
                          value={searchRiskFilter} 
                          onChange={(e) => setSearchRiskFilter(e.target.value)}
                        >
                          <option value="all">All Risk Levels</option>
                          <option value="low">Low Risk</option>
                          <option value="medium">Medium Risk</option>
                          <option value="high">High Risk</option>
                        </Form.Select>
                      </Col>
                    </Row>
                    
                    {filteredHistory.length === 0 ? (
                      <p className="text-muted">No workflow analysis history available.</p>
                    ) : (
                      <Accordion>
                        {filteredHistory.map((item, index) => (
                          <Accordion.Item key={item.id} eventKey={item.id.toString()}>
                            <Accordion.Header>
                              <div className="d-flex justify-content-between align-items-center w-100 me-3">
                                <span>
                                  <strong>Analysis #{index + 1}</strong>
                                  {' - '}
                                  <Badge bg={
                                    item.results.some(r => r.risk.toLowerCase() === 'high') ? 'danger' :
                                    item.results.some(r => r.risk.toLowerCase() === 'medium') ? 'warning' : 'success'
                                  }>
                                    {
                                      item.results.some(r => r.risk.toLowerCase() === 'high') ? 'High Risk' :
                                      item.results.some(r => r.risk.toLowerCase() === 'medium') ? 'Medium Risk' : 'Low Risk'
                                    }
                                  </Badge>
                                </span>
                                <small className="text-muted">{item.date}</small>
                              </div>
                            </Accordion.Header>
                            <Accordion.Body>
                              <Card.Subtitle className="mb-2">Workflow Steps:</Card.Subtitle>
                              <Card.Text className="mb-3">
                                <pre className="border p-2 bg-light">{item.steps}</pre>
                              </Card.Text>
                              {item.sensitivity && (
                                <div className="mb-3">
                                  <Badge bg={
                                    item.sensitivity === 'strict' ? 'danger' :
                                    item.sensitivity === 'medium' ? 'warning' : 'success'
                                  }>
                                    {item.sensitivity.charAt(0).toUpperCase() + item.sensitivity.slice(1)} Sensitivity
                                  </Badge>
                                </div>
                              )}
                              {renderResults(item.results, false, item.id)}
                            </Accordion.Body>
                          </Accordion.Item>
                        ))}
                      </Accordion>
                    )}
                  </Card.Body>
                </Card>
              </Tab.Pane>
              
              <Tab.Pane eventKey="about">
                <Card>
                  <Card.Body>
                    <h5>About Sentra</h5>
                    <p>
                      Sentra is a Visual AI Workflow Auditor designed to help organizations analyze and assess the risks associated with their AI workflows.
                    </p>
                    <p>
                      Our platform provides detailed risk assessments, recommendations, and explanations to help you build more ethical, compliant, and responsible AI systems.
                    </p>
                    <h6>Key Features:</h6>
                    <ul>
                      <li>Comprehensive risk analysis of AI workflow steps</li>
                      <li>Detailed recommendations for risk mitigation</li>
                      <li>Clear explanations of potential ethical and legal concerns</li>
                      <li>Historical tracking of workflow analyses</li>
                      <li>PDF report generation for documentation and compliance</li>
                      <li>Customizable sensitivity levels for different risk appetites</li>
                      <li>Cumulative risk scoring to quantify overall workflow risk</li>
                      <li>Detailed GPT-enhanced explanations of risk factors</li>
                    </ul>
                    <p>
                      Sentra helps organizations identify and address potential issues in their AI systems before they become problems, ensuring that AI is deployed responsibly and ethically.
                    </p>
                  </Card.Body>
                </Card>
              </Tab.Pane>
            </Tab.Content>
          </Tab.Container>
        </Col>
      </Row>
      
      {/* Detailed Explanation Modal */}
      <Modal show={showDetailedExplanation} onHide={() => setShowDetailedExplanation(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            Why Is This Risky?
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {currentExplanationStep && (
            <div dangerouslySetInnerHTML={{ __html: getDetailedExplanation(currentExplanationStep) }} />
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDetailedExplanation(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default App;
