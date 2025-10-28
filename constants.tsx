
export const COMMAND_SCHEMAS = {
  SCAN_SITE: {
    description: 'Performs a quick security and health scan on a website.',
    params: [{ name: 'domain', type: 'text', required: true, placeholder: 'example.com' }],
    severity: 'LOW',
  },
  PUBLISH_REPORT: {
    description: 'Generates and publishes a report for a client.',
    params: [
      { name: 'client', type: 'text', required: true, placeholder: 'Client Name' },
      { name: 'dataset', type: 'text', required: true, placeholder: 'Q3_Performance' },
      { name: 'format', type: 'select', required: true, options: ['pdf', 'html', 'csv'] },
    ],
    severity: 'MEDIUM',
  },
  START_CAMPAIGN: {
    description: 'Initiates a new marketing campaign on a specified channel.',
    params: [
      { name: 'channel', type: 'select', required: true, options: ['linkedin', 'meta', 'mailchimp'] },
      { name: 'campaign_id', type: 'text', required: true, placeholder: 'summer-sale-2024' },
    ],
    severity: 'HIGH',
  },
  REVERT_ACTION: {
    description: 'Reverts a previously executed action using its Action ID.',
    params: [
      { name: 'action_id', type: 'text', required: true, placeholder: 'wp_uuid...' },
      { name: 'reason', type: 'text', required: true, placeholder: 'Emergency rollback due to...' },
    ],
    severity: 'HIGH',
  },
};

export const RUNBOOK_CONTENT = `
# Production Control Plane - Operational Runbook

## 🚨 Emergency Procedures

### IMMEDIATE: Stop All Autonomous Actions
- **Method 1 (Recommended):** Flip the kill switch in the Notion Feature Flags database. Set \`kill_switch\` to \`true\`.
- **Method 2 (CLI):** Scale down the command poller Kubernetes deployment: \`kubectl scale deployment command-poller --replicas=0 -n pcp-prod\`
- **Verification:** Monitor the Action Ledger in Notion. No new entries should appear for at least 2 minutes.

### Compromised Key Rotation
If the \`MCP_PRIVATE_KEY\` is compromised, follow these steps immediately:
1.  Generate a new key: \`openssl rand -hex 32\`
2.  Update the secret in GCP Secret Manager and restart all PCP deployments to pull the new secret.
3.  Update the key in all connected systems (e.g., WordPress plugin config).
4.  Verify all components are healthy and can communicate.

### Rollback Recent Actions
- **Single Action:** Find the \`action_id\` in the Notion Action Ledger. Use the Command Center to issue a \`REVERT_ACTION\` command with the target \`action_id\` and a clear reason.
- **Bulk Rollback:** Use the provided Python script: \`python scripts/rollback_recent.py --last 10 --reason "Emergency rollback"\`. Use with extreme caution.

## 📊 Monitoring & Alerts

### Key Metrics to Watch
- **Action Success Rate:** Should be >95%. Dips below 90% are critical.
- **MCP Response Time (P95):** Should be <500ms. Sustained times over 1000ms indicate a problem.
- **Ledger Chain Breaks:** Should always be 0. Any break is a critical security incident.
- **Circuit Breaker Trips:** Occasional trips are normal. >20 trips/hour indicates a failing downstream service.

### Grafana Dashboards
- **PCP Overview:** [https://grafana.yourdomain.com/d/pcp-overview](https://grafana.yourdomain.com/d/pcp-overview)
- **Ledger Integrity:** [https://grafana.yourdomain.com/d/pcp-ledger](https://grafana.yourdomain.com/d/pcp-ledger)

## 🔧 Common Operations

### Deploying a New Version
1.  Build and push the new container image to GCR.
2.  Update the Kubernetes deployment manifest with the new image tag.
3.  Apply the changes: \`kubectl apply -f gcp-deployment.yml -n pcp-prod\`
4.  Monitor the rollout status: \`kubectl rollout status deployment/mcp-orchestrator -n pcp-prod\`
`;
