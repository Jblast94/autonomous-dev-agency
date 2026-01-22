import streamlit as st
import redis
import os
import json
from kubernetes import client, config
from datetime import datetime

# Page Config
st.set_page_config(page_title="Agency Command Center", layout="wide")
st.title("🤖 Autonomous Agency Command Center")

# Sidebar - Settings
st.sidebar.header("Connection Status")

# 1. Redis Connection
redis_host = os.getenv("REDIS_HOST", "redis")
try:
    r = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
    r.ping()
    st.sidebar.success(f"Redis: Connected ({redis_host})")
    redis_connected = True
except:
    st.sidebar.error("Redis: Disconnected")
    redis_connected = False

# 2. Kubernetes Connection
try:
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    v1 = client.CoreV1Api()
    st.sidebar.success("Kubernetes: Connected")
    k8s_connected = True
except:
    st.sidebar.warning("Kubernetes: Not Connected (Local Mode?)")
    k8s_connected = False

# --- Dashboard Content ---

col1, col2, col3 = st.columns(3)

# Metric: Active Workers
worker_count = 0
if k8s_connected:
    pods = v1.list_namespaced_pod(namespace="agency", label_selector="role=worker")
    worker_count = len(pods.items)

col1.metric("Active Workers", worker_count)

# Metric: Tasks in Queue
queue_len = 0
if redis_connected:
    queue_len = r.llen("agency:tasks")
col2.metric("Pending Tasks", queue_len)

# Metric: System Time
col3.metric("System Time", datetime.now().strftime("%H:%M:%S"))

# --- Task Injection ---
st.divider()
st.subheader("📢 Dispatch Task")

with st.form("dispatch_form"):
    task_type = st.selectbox(
        "Task Type",
        ["shell", "echo", "python"],
        help="Select the type of task to execute on the worker node."
    )
    command = st.text_input(
        "Command / Message",
        value="echo 'Hello World'",
        help="Enter the command to execute or message to echo."
    )

    submitted = st.form_submit_button("Dispatch to Swarm")

    if submitted:
        if not redis_connected:
            st.error("❌ Cannot dispatch: Redis is disconnected.")
        elif not command.strip():
            st.error("⚠️ Please enter a command.")
        else:
            task_payload = json.dumps({
                "id": f"task-{int(datetime.now().timestamp())}",
                "type": task_type,
                "command": command,
                "message": command, # for echo
                "timestamp": str(datetime.now())
            })
            r.lpush("agency:tasks", task_payload)
            st.success("✅ Task dispatched to Redis Queue!")

# --- Worker Status ---
st.divider()
st.subheader("🏗️ Swarm Status")

if k8s_connected:
    pods = v1.list_namespaced_pod(namespace="agency")
    pod_data = []
    for pod in pods.items:
        pod_data.append({
            "Name": pod.metadata.name,
            "Status": pod.status.phase,
            "IP": pod.status.pod_ip,
            "Node": pod.spec.node_name,
            "Created": str(pod.metadata.creation_timestamp)
        })
    if pod_data:
        st.dataframe(pod_data, use_container_width=True)
    else:
        st.info("ℹ️ No active worker pods found.")
else:
    st.info("Kubernetes connection required to see pod status.")

# --- Auto-Refresh ---
if st.checkbox("Auto-Refresh (5s)"):
    st.rerun()
