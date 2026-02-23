# Concurrent Workflow with JobFinder and CVFinder Agents

This project demonstrates a concurrent workflow using Microsoft Agent Framework, where JobFinder and CVFinder agents run in parallel to process user queries.

## Features

- **Concurrent Execution**: JobFinder and CVFinder agents process the same query simultaneously using fan-out/fan-in patterns.
- **HTTP Server Mode**: Production-ready HTTP server for handling requests.
- **Debug Support**: Integrated debugging with AI Toolkit Agent Inspector.

## Setup

1. Install dependencies:
   ```bash
   pip install agent-framework==1.0.0b260107 agent-framework-azure-ai==1.0.0b260107 azure-ai-agentserver-agentframework==1.0.0b10 azure-ai-agentserver-core==1.0.0b10 debugpy
   ```

2. Ensure you have Azure CLI logged in: `az login`

3. Configure your Foundry project endpoint in the code if different.

## Running

### CLI Mode
```bash
python concurrent_workflow.py
```

### HTTP Server Mode
```bash
python concurrent_workflow.py --server
```

### Debugging
Use VS Code tasks: "Run Concurrent Workflow HTTP Server" then "Debug Concurrent Workflow HTTP Server"

## Workflow Description

1. **Dispatcher**: Receives user input and sends it to both agents.
2. **Fan-out**: JobFinder and CVFinder agents process the query in parallel.
3. **Fan-in**: Aggregator combines results from both agents.
4. **Output**: Returns combined job and CV findings.

## Agents

- **JobFinder**: Finds relevant job opportunities based on the query.
- **CVFinder**: Finds matching candidate profiles/CVs based on the query.