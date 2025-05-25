// API client for communicating with the backend service

// Get the API base URL from the environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Types
export interface ScrapeRegex {
  pattern: string;
}

export interface ScrapeRule {
  url: ScrapeRegex;
  css_selector?: string;
}

export interface ScrapeRules {
  max_depth: number;
  max_pages: number;
  scrape_patterns: ScrapeRule[];
  forbidden_urls: ScrapeRegex[];
}

export interface PipelineResponse {
  token: string;
}

export interface JobResponse {
  job_id: string;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  message: string;
  result?: {
    token?: string;
  };
}

export interface AnswerResponse {
  answer: string;
}

// Create a new pipeline (async with job tracking)
export async function createPipeline(
  user_name: string,
  description: string,
  language: string,
  entry_docs_url: string,
  rules: ScrapeRules
): Promise<JobResponse> {
  // Create form data for the request
  const formData = new FormData();
  formData.append('user_name', user_name);
  formData.append('description', description);
  formData.append('language', language);
  formData.append('entry_docs_url', entry_docs_url);
  formData.append('rules', JSON.stringify(rules));
  
  // Send the request
  const response = await fetch(`${API_BASE_URL}/pipeline`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Error creating pipeline: ${response.status}`);
  }
  
  return response.json();
}

// Create a new pipeline (synchronous - deprecated)
export async function createPipelineSync(
  user_name: string,
  description: string,
  language: string,
  entry_docs_url: string,
  rules: ScrapeRules
): Promise<PipelineResponse> {
  // Create form data for the request
  const formData = new FormData();
  formData.append('user_name', user_name);
  formData.append('description', description);
  formData.append('language', language);
  formData.append('entry_docs_url', entry_docs_url);
  formData.append('rules', JSON.stringify(rules));
  
  // Send the request
  const response = await fetch(`${API_BASE_URL}/pipeline/sync`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Error creating pipeline: ${response.status}`);
  }
  
  return response.json();
}

// Check job status
export async function getJobStatus(job_id: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/pipeline/status/${job_id}`, {
    method: 'GET',
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Error fetching job status: ${response.status}`);
  }
  
  return response.json();
}

// Get answer from the RAG system
export async function getAnswer(token: string, prompt: string): Promise<AnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/answer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token
    },
    body: JSON.stringify({ prompt }),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Error fetching answer: ${response.status}`);
  }
  
  return response.json();
}
