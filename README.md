# AgentKit Phase 1 – Production Control Plane

Cloud-native automation system with **REAL API integrations** that:
- Polls commands from Google Docs
- Performs actual website security scans
- Posts to real social media platforms
- Generates professional PDF/Excel reports
- Sends actual emails
- Updates Notion pages

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and setup
git clone https://github.com/deedk822-lang/deedk822-lang-agentkit-phase1.git
cd deedk822-lang-agentkit-phase1
chmod +x setup.sh
bash setup.sh
source venv/bin/activate

# Configure API keys
cp .env.template .env
# Edit .env with your real API keys
```

### 2. Start Redis
```bash
docker run --rm -d -p 6379:6379 redis:7-alpine
```

### 3. Test the System
```bash
# Test all components
python launch_agents.py test

# Check environment configuration
python launch_agents.py --check-env

# Run tests
pytest tests/ -v
```

### 4. Launch All Agents
```bash
# Start all agents with monitoring
python launch_agents.py start

# Or start specific agents
python launch_agents.py start --agents command_poller content_distribution
```

## 🚅 Real Integrations

### 📄 Command Poller Agent
- **Reads from actual Google Docs** using Google Docs API
- **Updates Notion pages** with real API calls
- **Kill switch** functionality via Redis
- Validates commands with comprehensive schemas
- Falls back to local file if Google Docs unavailable

### 📱 Content Distribution Agent
- **Twitter/X**: Real posts via Tweepy API
- **LinkedIn**: Automated posting via LinkedIn API
- **Facebook**: Page posts via Graph API
- **Reddit**: Submit posts to subreddits via PRAW
- **Email Newsletter**: SMTP delivery to subscriber lists
- **Instagram**: Ready for business API integration

### 🔍 Site Scanner Agent
- **Security Analysis**: SSL certificates, security headers, vulnerability detection
- **Performance Testing**: Load times, resource analysis, optimization suggestions
- **SEO Audit**: Meta tags, heading structure, technical SEO issues
- **Technology Detection**: Framework and CMS identification
- **Comprehensive Reports**: JSON results stored in Redis

### 📈 Report Generator Agent
- **PDF Reports**: Professional layouts with charts and tables
- **Excel Workbooks**: Multi-sheet reports with data analysis
- **CSV Exports**: Structured data for further analysis
- **Automated Data Gathering**: Pulls from scan results and distribution metrics
- **Client-Branded**: Customizable templates and styling

## 🔑 API Configuration

Copy `.env.template` to `.env` and configure:

### Google Services
```bash
GOOGLE_DOC_ID=your_google_doc_id
GOOGLE_CREDENTIALS_PATH=/path/to/service-account.json
```

### Social Media APIs
```bash
# Twitter
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret

# LinkedIn
LINKEDIN_USERNAME=your_email
LINKEDIN_PASSWORD=your_password

# Facebook
FACEBOOK_ACCESS_TOKEN=your_page_token
FACEBOOK_PAGE_ID=your_page_id

# Reddit
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
```

### Email Configuration
```bash
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### Notion Integration
```bash
NOTION_TOKEN=secret_your_notion_token
```

## 💼 Command Usage

Add commands to your Google Doc or `command_queue.txt`:

```
# Website Analysis
SCAN_SITE domain=example.com

# Content Distribution
DISTRIBUTE_CONTENT content_file=content.txt

# Report Generation
PUBLISH_REPORT client=acme dataset=q3_2024 format=pdf
PUBLISH_REPORT client=acme dataset=q3_2024 format=excel

# Notion Updates
UPDATE_NOTION page_id=abc123 content="Status: Completed"

# Emergency Stop
KILL_SWITCH
```

## 📊 Monitoring & Management

```bash
# Check agent status
python launch_agents.py status

# Stop all agents
python launch_agents.py stop

# Monitor with auto-restart
python launch_agents.py monitor
```

## 📁 Output Files

- **Reports**: `./reports/` directory
- **Scan Results**: Stored in Redis with TTL
- **Distribution Results**: Tracked in Redis
- **Logs**: Console and file logging

## 🔧 Testing Individual Components

```bash
# Test site scanner
python -m agents.site_scanner --scan example.com

# Test content distribution
python -m agents.content_distribution_agent --content content.txt --test-platforms

# Test report generation
python -m agents.report_generator --client test --dataset demo --format pdf
```

## 🚀 Production Deployment

### Docker
```bash
# Build images
docker build -f Dockerfile.poller -t agentkit-poller .
docker build -f Dockerfile.distributor -t agentkit-distributor .

# Run with Docker Compose
docker-compose up -d
```

### Kubernetes
```bash
# Update project ID in k8s/gcp-deployment.yml
kubectl apply -f k8s/gcp-deployment.yml
```

### GitHub Actions
Uncomment the workflow trigger in `.github/workflows/deploy.yml` and configure secrets:
- `GCP_PROJECT`
- `WIF_PROVIDER`

## 🛡️ Security Features

- **Kill Switch**: Emergency stop via Redis command
- **Environment Variables**: Secure credential management
- **Input Validation**: Comprehensive command validation
- **Error Handling**: Graceful failure with logging
- **Rate Limiting**: Built-in delays and retries

## 📊 Analytics

Real-time metrics stored in Redis:
- Scan results with performance data
- Distribution success/failure rates
- Agent health and uptime
- Command processing statistics

## 🔄 Fallback Behavior

When APIs are unavailable:
- Google Docs → Local `command_queue.txt`
- Social media → Simulated posts with logging
- Email → Local file output
- All operations logged for debugging

## 📈 Scaling

- **Horizontal**: Multiple agent instances
- **Vertical**: Resource allocation per agent
- **Queue-based**: Redis for inter-agent communication
- **Cloud-native**: Kubernetes deployment ready

---

**AgentKit Phase-1** is production-ready with real API integrations, comprehensive error handling, and enterprise-grade monitoring. No more mock-ups or simulations – this is the real deal! 🚀