from kubernetes import client, config
from supabase import create_client, Client
import os
import logging
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgencyManager")

class AgencyManager:
    def __init__(self):
        # 1. Initialize Supabase Connection
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not found. Using mock mode for DB.")
            self.supabase = None
        else:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # 2. Initialize Kubernetes Connection
        try:
            # Tries to load in-cluster config first (production), then kubeconfig (local dev)
            try:
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes config.")
            except config.ConfigException:
                config.load_kube_config()
                logger.info("Loaded local kubeconfig.")

            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
        except Exception as e:
            logger.error(f"Failed to connect to Kubernetes: {e}")
            self.v1 = None
            self.apps_v1 = None

    def list_active_agents(self) -> List[Dict[str, Any]]:
        """List all pods in the 'agency' namespace."""
        if not self.v1:
            return [{"error": "Kubernetes not connected"}]

        try:
            pods = self.v1.list_namespaced_pod(namespace="agency", label_selector="role=worker")
            agents = []
            for pod in pods.items:
                agents.append({
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip
                })
            return agents
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return []

    def deploy_worker(self, name: str, replicas: int = 1):
        """Scale the worker deployment."""
        if not self.apps_v1:
            return {"error": "Kubernetes not connected"}

        try:
            # In a real scenario, we might patch the specific deployment or create a new one
            # For now, we scale the generic 'agency-worker' deployment
            patch = {"spec": {"replicas": replicas}}
            self.apps_v1.patch_namespaced_deployment(
                name="agency-worker",
                namespace="agency",
                body=patch
            )
            return {"status": "success", "message": f"Scaled worker to {replicas} replicas"}
        except Exception as e:
            return {"error": str(e)}

    def register_task(self, description: str, project_id: str) -> Dict[str, Any]:
        """Add a task to the Supabase queue."""
        if not self.supabase:
            return {"error": "Supabase not connected"}

        data = {
            "description": description,
            "project_id": project_id,
            "status": "pending"
        }
        try:
            response = self.supabase.table("tasks").insert(data).execute()
            return response.data
        except Exception as e:
            return {"error": str(e)}

# --- MCP Server Setup ---

mcp = FastMCP("Agency Manager")
manager = AgencyManager()

@mcp.tool()
def get_agency_status() -> str:
    """Returns the current status of the agency (active agents, resource usage)."""
    agents = manager.list_active_agents()
    return f"Active Agents: {len(agents)}\nDetails: {agents}"

@mcp.tool()
def scale_workers(count: int) -> str:
    """Scales the number of generic worker nodes."""
    result = manager.deploy_worker("agency-worker", count)
    return str(result)

@mcp.tool()
def create_task(description: str, project_id: str) -> str:
    """Creates a new task in the backlog."""
    result = manager.register_task(description, project_id)
    return str(result)

if __name__ == "__main__":
    # Start the MCP server
    mcp.run()
