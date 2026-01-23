"""
Agency Command Center Dashboard.

This Streamlit application serves as a control panel for the autonomous agency,
allowing users to monitor worker status, view task queues, and dispatch new tasks.
"""

import os
import json
from datetime import datetime
import streamlit as st
import redis
from kubernetes import client, config

# Page Config
st.set_page_config(page_title="Agency Command Center", layout="wide", page_icon="🤖")
st.title("🤖 Autonomous Agency Command Center")

# Sidebar - Settings
st.sidebar.header("Connection Status")

# 1. Redis Connection
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
try:
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
    r.ping()
    st.sidebar.success(f"Redis: Connected ({REDIS_HOST})")
    REDIS_CONNECTED = True
except Exception: # pylint: disable=broad-except
    st.sidebar.error("Redis: Disconnected")
    REDIS_CONNECTED = False

# 2. Kubernetes Connection
try:
    try:
        config.load_incluster_config()
    except Exception: # pylint: disable=broad-except
        config.load_kube_config()
    v1 = client.CoreV1Api()
    st.sidebar.success("Kubernetes: Connected")
    K8S_CONNECTED = True
except Exception: # pylint: disable=broad-except
    st.sidebar.warning("Kubernetes: Not Connected (Local Mode?)")
    K8S_CONNECTED = False

# --- Dashboard Content ---

col1, col2, col3 = st.columns(3)

# Metric: Active Workers
WORKER_COUNT = 0
if K8S_CONNECTED:
    try:
        pods = v1.list_namespaced_pod(namespace="agency", label_selector="role=worker")
        WORKER_COUNT = len(pods.items)
    except Exception: # pylint: disable=broad-except
        WORKER_COUNT = 0

col1.metric("Active Workers", WORKER_COUNT)

# Metric: Tasks in Queue
QUEUE_LEN = 0
if REDIS_CONNECTED:
    try:
        QUEUE_LEN = r.llen("agency:tasks")
    except Exception: # pylint: disable=broad-except
        QUEUE_LEN = 0
col2.metric("Pending Tasks", QUEUE_LEN)

# Metric: System Time
col3.metric("System Time", datetime.now().strftime("%H:%M:%S"))

# --- Task Injection ---
st.divider()
st.subheader("📢 Dispatch Task")

with st.form("dispatch_form"):
    task_type = st.selectbox("Task Type", ["shell", "echo", "python"])

    # UX Improvement: Use text_area for multi-line commands and add helper text
    command = st.text_area(
        "Command / Message",
        value="echo 'Hello World'",
        height=150,
        help="Enter the shell command, python script, or message to dispatch."
    )

    submitted = st.form_submit_button("Dispatch to Swarm")

    if submitted:
        if not command.strip():
            st.error("⚠️ Command cannot be empty.")
        elif not REDIS_CONNECTED:
            st.error("❌ Redis is not connected. Cannot dispatch task.")
        else:
            task_id = f"task-{int(datetime.now().timestamp())}"
            task_payload = json.dumps({
                "id": task_id,
                "type": task_type,
                "command": command,
                "message": command, # for echo
                "timestamp": str(datetime.now())
            })
            try:
                r.lpush("agency:tasks", task_payload)
                st.success(f"✅ Task dispatched to Redis Queue! (ID: {task_id})")
            except Exception as e: # pylint: disable=broad-except
                st.error(f"❌ Failed to dispatch task: {e}")

# --- Worker Status ---
st.divider()
st.subheader("🏗️ Swarm Status")

if K8S_CONNECTED:
    try:
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
        st.dataframe(pod_data, use_container_width=True)
    except Exception as e: # pylint: disable=broad-except
        st.error(f"Error fetching pod status: {e}")
else:
    st.info("Kubernetes connection required to see pod status.")

# --- Auto-Refresh ---
if st.checkbox("Auto-Refresh (5s)"):
    st.rerun()
