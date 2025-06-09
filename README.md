<div align="center">

# Bitterbot - Advanced Autonomous Agentic Assistant

(that acts on your behalf)

Bitterbot is an AI assistant that helps you accomplish real-world tasks with ease. Through natural conversation, Bitterbot becomes your digital companion for research, data analysis, and everyday challenges—combining powerful capabilities with an intuitive interface that understands what you need and delivers results.

Bitterbot's powerful toolkit includes seamless browser automation to navigate the web and extract data, file management for document creation and editing, web crawling and extended search capabilities, command-line execution for system tasks, website deployment, and integration with various APIs and services. These capabilities work together harmoniously, allowing Bitterbot to solve your complex problems and automate workflows through simple conversations!

## Table of Contents

- [Bitterbot Architecture](#project-architecture)
  - [Backend API](#backend-api)
  - [Frontend](#frontend)
  - [Agent Docker](#agent-docker)
  - [Supabase Database](#supabase-database)
- [Run Locally / Self-Hosting](#run-locally--self-hosting)
  - [Requirements](#requirements)
  - [Prerequisites](#prerequisites)
  - [Installation Steps](#installation-steps)

## Project Architecture


Bitterbot consists of four main components:

### Backend API

Python/FastAPI service that handles REST endpoints, thread management, and LLM integration with Anthropic, and others via LiteLLM.

### Frontend

Next.js/React application providing a responsive UI with chat interface, dashboard, etc.

### Agent Docker

Isolated execution environment for every agent - with browser automation, code interpreter, file system access, tool integration, and security features.

### Supabase Database

Handles data persistence with authentication, user management, conversation history, file storage, agent state, analytics, and real-time subscriptions.


## Run Locally / Self-Hosting

Bitterbot can be self-hosted on your own infrastructure. Follow these steps to set up your own instance.

### Requirements

You'll need the following components:

- A Supabase project for database and authentication
- Redis database for caching and session management
- RabbitMQ message queue for orchestrating worker tasks
- Daytona sandbox for secure agent execution
- Python 3.11 for the API backend
- API keys for LLM providers (Anthropic, OpenRouter)
- Tavily API key for enhanced search capabilities
- Firecrawl API key for web scraping capabilities

### Prerequisites

1. **Supabase**:

   - Create a new [Supabase project](https://supabase.com/dashboard/projects)
   - Save your project's API URL, anon key, and service role key for later use
   - Install the [Supabase CLI](https://supabase.com/docs/guides/cli/getting-started)

2. **Redis and RabbitMQ**:

   - Go to the `/backend` folder
   - Run `docker compose up redis rabbitmq`

3. **Daytona**:

   - Create an account on [Daytona](https://app.daytona.io/)
   - Generate an API key from your account settings
   - Go to [Images](https://app.daytona.io/dashboard/images)
   - Click "Add Image"
   - Enter `kortix/suna:0.1.2` as the image name
   - Set `/usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf` as the Entrypoint

4. **LLM API Keys**:

   - Obtain an API key [Anthropic](https://www.anthropic.com/)
   - While other providers should work via [LiteLLM](https://github.com/BerriAI/litellm), Anthropic is recommended – the prompt needs to be adjusted for other providers to output correct XML for tool calls.

5. **Search API Key** (Optional):

   - For enhanced search capabilities, obtain an [Tavily API key](https://tavily.com/)
   - For web scraping capabilities, obtain a [Firecrawl API key](https://firecrawl.dev/)

6. **RapidAPI API Key** (Optional):
   - To enable API services like LinkedIn, and others, you'll need a RapidAPI key
   - Each service requires individual activation in your RapidAPI account:
     1. Locate the service's `base_url` in its corresponding file (e.g., `"https://linkedin-data-scraper.p.rapidapi.com"` in [`backend/agent/tools/data_providers/LinkedinProvider.py`](backend/agent/tools/data_providers/LinkedinProvider.py))
     2. Visit that specific API on the RapidAPI marketplace
     3. Subscribe to the service (many offer free tiers with limited requests)
     4. Once subscribed, the service will be available to your agent through the API Services tool

### Installation Steps

1. **Clone the repository**:

```bash
git clone https://github.com/Bitterbot-AI/Bitterbot_Dev
cd Bitterbot_Dev

2. **Configure backend environment**:

```bash
cd backend
cp .env.example .env  # Create from example if available, or use the following template
```

Edit the `.env` file and fill in your credentials:

```bash
NEXT_PUBLIC_URL="http://localhost:3000"

# Supabase credentials from step 1
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Redis credentials from step 2
REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_SSL=True  # Set to False for local Redis without SSL

RABBITMQ_HOST=your_rabbitmq_host # Set to localhost if running locally
RABBITMQ_PORT=5672

# Daytona credentials from step 3
DAYTONA_API_KEY=your_daytona_api_key
DAYTONA_SERVER_URL="https://app.daytona.io/api"
DAYTONA_TARGET="us"

# Anthropic
ANTHROPIC_API_KEY=

# OpenAI API:
OPENAI_API_KEY=your_openai_api_key

# Optional but recommended
TAVILY_API_KEY=your_tavily_api_key  # For enhanced search capabilities
FIRECRAWL_API_KEY=your_firecrawl_api_key  # For web scraping capabilities
RAPID_API_KEY=
```

3. **Set up Supabase database**:

```bash
# Login to Supabase CLI
supabase login

# Link to your project (find your project reference in the Supabase dashboard)
supabase link --project-ref your_project_reference_id

# Push database migrations
supabase db push
```

Then, go to the Supabase web platform again -> choose your project -> Project Settings -> Data API -> And in the "Exposed Schema" add "basejump" if not already there

4. **Configure frontend environment**:

```bash
cd ../frontend
cp .env.example .env.local  # Create from example if available, or use the following template
```

Edit the `.env.local` file:

```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_BACKEND_URL="http://localhost:8000/api"  # Use this for local development
NEXT_PUBLIC_URL="http://localhost:3000"
```

Note: If you're using Docker Compose, use the container name instead of localhost:

```
NEXT_PUBLIC_BACKEND_URL="http://backend:8000/api"  # Use this when running with Docker Compose
```

5. **Install dependencies**:

```bash
# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
poetry install
```

6. **Start the application**:

   In one terminal, start the frontend:

```bash
cd frontend
npm run dev
```

In another terminal, start the backend:

```bash
cd backend
poetry run python3.11 api.py
```

In one more terminal, start the backend worker:

```bash
cd backend
poetry run python3.11 -m dramatiq run_agent_background
```

5-6. **Docker Compose Alternative**:

Before running with Docker Compose, make sure your environment files are properly configured:

- In `backend/.env`, set all the required environment variables as described above

  - For Redis configuration, use `REDIS_HOST=redis` instead of localhost
  - For RabbitMQ, use `RABBITMQ_HOST=rabbitmq` instead of localhost
  - The Docker Compose setup will automatically set these Redis environment variables:

    ```
    REDIS_HOST=redis
    REDIS_PORT=6379
    REDIS_PASSWORD=
    REDIS_SSL=False

    RABBITMQ_HOST=rabbitmq
    RABBITMQ_PORT=5672
    ```

- In `frontend/.env.local`, make sure to set `NEXT_PUBLIC_BACKEND_URL="http://backend:8000/api"` to use the container name

Then run:

```bash
export GITHUB_REPOSITORY="your-github-username/repo-name"
docker compose -f docker-compose.ghcr.yaml up
```

If you're building the images locally instead of using pre-built ones:

```bash
docker compose up
```

The Docker Compose setup includes Redis and RabbitMQ services that will be used by the backend automatically.

7. **Access Bitterbot**:
   - Open your browser and navigate to `http://localhost:3000`
   - Sign up for an account using the Supabase authentication
   - Start using your self-hosted Bitterbot instance!

### Technologies

- [Daytona](https://daytona.io/) - Secure agent execution environment
- [Supabase](https://supabase.com/) -
- [Playwright](https://playwright.dev/) - Browser automation
- [OpenAI](https://openai.com/) - LLM provider
- [Anthropic](https://www.anthropic.com/) - LLM provider
- [Tavily](https://tavily.com/) - Search capabilities
- [Firecrawl](https://firecrawl.dev/) - Web scraping capabilities
- [RapidAPI](https://rapidapi.com/) - API services

## License

Bitterbot is licensed under the Apache License, Version 2.0. See [LICENSE](./LICENSE) for the full license text.
