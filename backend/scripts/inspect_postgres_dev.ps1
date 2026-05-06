Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Split-Path -Parent $scriptDir

Push-Location $backendDir
try {
  @'
import psycopg

dsn = "postgresql://LLM-project-shopeasy:LLm-260346@127.0.0.1:5433/shopeasy"
queries = {
    "customers": "select count(*) from customers",
    "orders": "select count(*) from orders",
    "shipments": "select count(*) from shipments",
    "refund_requests": "select count(*) from refund_requests",
    "proactive_alerts": "select count(*) from proactive_alerts",
    "agent_traces": "select count(*) from agent_traces",
}

with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
        for label, sql in queries.items():
            cur.execute(sql)
            print(f"{label}: {cur.fetchone()[0]}")
'@ | python -
}
finally {
  Pop-Location
}
