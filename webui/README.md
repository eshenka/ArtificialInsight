# ArtificialInsight Web UI

## Overview

This repository contains the web user interface for the ArtificialInsight application. The UI provides a user-friendly way to create and test RAG (Retrieval-Augmented Generation) pipelines by scraping documentation websites. It interfaces with the existing REST API endpoints to create pipelines and interact with them through a chat interface.

## Features

The Web UI enables users to:

1. **Create RAG Pipelines**: Configure and submit parameters for new documentation-based RAG systems
2. **Test Generated Pipelines**: Interact with the created RAG pipeline through a chat interface
3. **Manage Access Tokens**: Save and reuse tokens for previously created pipelines

## UI/UX Design Specifications

### Layout

The interface follows a minimalistic, clean design with two main sections:

1. **Pipeline Creation Panel**
2. **Chat Testing Panel**

### Pipeline Creation Form

The form should include the following components:

- **Basic Information**:
  - User Name input field
  - Pipeline Description text area
  - Language dropdown (e.g., "en", "ru")
  - Entry Documentation URL input field with validation
  
- **Scraping Configuration**:
  - Max Depth slider/number input (with reasonable limits and default value)
  - Max Pages slider/number input (with reasonable limits and default value)
  
- **Pattern Rules** (dynamic form section):
  - Add multiple URL patterns with corresponding CSS selectors
  - Each rule should have:
    - URL Pattern input (regex)
    - Optional CSS Selector input
    - Remove button for individual rules
  - "Add Rule" button to add more pattern rules
  
- **Forbidden URLs** (dynamic form section):
  - Add multiple URL patterns to exclude
  - Each entry should have:
    - URL Pattern input (regex)
    - Remove button
  - "Add Forbidden URL" button to add more patterns
  
- **Submit Button**: Clearly visible "Create Pipeline" button
- **Loading State**: Visual indicator during pipeline creation process
- **Result Display**: Success message with token display and "Copy" button

### Chat Testing Interface

- **Token Input**: Field to enter or paste the pipeline token
- **Chat Panel**:
  - Messages displayed in alternating sender/receiver format
  - User messages displayed in solid background
  - AI responses displayed in Markdown-rendered format
  - Timestamps for each message
  - Auto-scrolling to latest message
  
- **Input Area**:
  - Text input field for typing prompts
  - Send button
  - Enter key submission support
  - Loading indicator while waiting for response

### Responsive Design

- Desktop layout: Side-by-side panels for Pipeline Creation and Chat Testing
- Tablet/Mobile layout: Tabbed interface or stacked panels with smooth transitions

### State Management

- Form validation with visual feedback
- Error handling with user-friendly error messages
- Success notifications
- Persistent chat history during the session

## Technology Stack

The Web UI will be implemented using the following technologies:

- **Frontend Framework**: React with TypeScript
- **Styling**: Tailwind CSS for utility-first styling
- **HTTP Client**: Axios for API communication
- **Markdown Rendering**: react-markdown for rendering LLM responses
- **Form Management**: react-hook-form for form state and validation
- **Build Tool**: Vite for fast development and optimized production builds
- **Testing**: Jest and React Testing Library

## API Integration

The UI will communicate with two primary API endpoints:

1. **POST /pipeline**: For creating new RAG pipelines
   - Content-Type: application/x-www-form-urlencoded
   - Fields: user_name, description, language, entry_docs_url, rules

2. **POST /answer**: For sending prompts and receiving answers
   - Content-Type: application/json
   - Authorization header with token
   - Request body: { "prompt": "user question" }

## Getting Started

### Prerequisites

- Node.js (v16 or later)
- npm or yarn package manager
- Access to the Gateway Service API (running locally or remotely)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ArtificialInsight.git
   cd ArtificialInsight/webui
   ```

2. Install dependencies:
   ```bash
   npm install
   # or with yarn
   yarn install
   ```

3. Configure the API endpoint:
   
   By default, the application expects the API to be available at `http://localhost:8000`. 
   
   To change this, modify the proxy settings in `vite.config.ts` or set the `VITE_API_BASE_URL` 
   environment variable before building.

### Development

Run the development server:

```bash
npm run dev
# or with yarn
yarn dev
```

This will start the development server at `http://localhost:5173` (or another port if 5173 is in use).

### Building for Production

Build the application for production:

```bash
npm run build
# or with yarn
yarn build
```

This will generate optimized production files in the `dist` directory.

### Deployment

To preview the production build:

```bash
npm run preview
# or with yarn
yarn preview
```

To deploy to a web server, copy the contents of the `dist` directory to your server's web root or 
deploy using a static site hosting service.

### Testing

Run tests:

```bash
npm run test
# or with yarn
yarn test