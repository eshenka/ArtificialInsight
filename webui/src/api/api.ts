// API interface for ArtificialInsight RAG system

// Types for the API requests and responses
export interface PromptRequest {
  prompt: string;
}

export interface AnswerResponse {
  answer: string;
}

// ScrapeRules structure as defined in common.proto
export interface RegexPattern {
  pattern: string;
}

export interface Rule {
  url: RegexPattern;
  css_selector?: string;
}

export interface ScrapeRules {
  max_depth?: number;
  max_pages?: number;
  scrape_patterns: Rule[];
  forbidden_urls: RegexPattern[];
}

export interface PipelineResponse {
  token: string;
}

// Function to create a new RAG pipeline
export async function createPipeline(
  user_name: string,
  description: string,
  language: string,
  entry_docs_url: string,
  rules: ScrapeRules
): Promise<PipelineResponse> {
  // Convert the rules object to a JSON string
  const rulesJson = JSON.stringify(rules);
  
  // Create FormData object as the API expects application/x-www-form-urlencoded
  const formData = new FormData();
  formData.append('user_name', user_name);
  formData.append('description', description);
  formData.append('language', language);
  formData.append('entry_docs_url', entry_docs_url);
  formData.append('rules', rulesJson);
  
  const response = await fetch('/api/pipeline', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to create pipeline: ${response.statusText}`);
  }
  
  return response.json();
}

// Function to send a prompt and get an answer
export async function sendPrompt(
  token: string,
  prompt: string
): Promise<AnswerResponse> {
  const response = await fetch('/api/answer', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token,
    },
    body: JSON.stringify({ prompt }),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to get answer: ${response.statusText}`);
  }
  
  return response.json();
}
