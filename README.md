# AI-Based Network Detection and Diagnosis System

## Overview

The AI-Based Network Detection and Diagnosis System is a full-stack web application designed to detect and analyze unusual network activity in real time using AI-based rule logic and pattern detection techniques. The system operates entirely on **localhost** and is intended for development, testing, and academic demonstration purposes.

The application uses a **Flask-based backend** and a **pure HTML, CSS, and JavaScript frontend** to provide an interactive dashboard for monitoring network behavior, alerts, and system health.

---

## Features

* **AI-Based Detection**
  Rule-based logic to identify abnormal network patterns such as DDoS attacks, port scanning, brute force attempts, and general anomalous traffic.

* **Interactive Dashboard**
  Responsive web interface for real-time monitoring of network events and alerts.

* **Optimized Data Visualization**
  Charts displayed in modal windows to maintain a clean and space-efficient dashboard layout.

* **Real-Time Metrics**
  Displays active alerts, traffic statistics, detected anomalies, and system health indicators.

* **Alert Management**
  Tabular view of alerts including severity, status, and available actions.

* **System Monitoring**
  Continuous background analysis with event logging and system status tracking.

* **Modular Architecture**
  Clearly separated backend, frontend, and data models for maintainability and scalability.

---

## Project Structure

```
network-detection-system/
├── src/
│   ├── database.py
│   ├── detection_engine.py
│   ├── main.py
│   ├── models/
│   ├── routes/
│   └── static/
│       ├── index.html
│       ├── styles.css
│       └── script.js
├── venv/
├── requirements.txt
└── README.md
```

---

## Requirements

* Python 3.8 or higher
* pip (Python package manager)
* Visual Studio Code (recommended)

---

## Local Setup and Execution

### 1. Extract the Project

```bash
tar -xzf network-detection-system-enhanced-final.tar.gz
cd network-detection-system
```

### 2. Open in VS Code

```bash
code .
```

### 3. Create Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python src/main.py
```

### 6. Access the Dashboard

Open a browser and navigate to:

```
http://127.0.0.1:5000
```

---

## Optional: Localhost Execution Using Docker

The application may also be executed **locally using Docker** to ensure environment consistency. This option is restricted to **localhost execution only** and does not involve any cloud or production deployment.

When using Docker:

* The application runs inside a container
* Port `5000` is exposed to localhost
* Access remains at `http://127.0.0.1:5000`

---

## Scope

* Localhost-only execution
* No cloud or production deployment
* Intended for academic projects, local testing, and demonstrations

---

## Troubleshooting

**Import Errors**

* Ensure the virtual environment is activated
* Run the application from the project root directory

**Dashboard Not Updating**

* Verify that `detection_engine.py` is running in a background thread
* Ensure it does not block Flask request handling

**Charts Not Displaying**

* Confirm internet connectivity for the Chart.js CDN
* Verify correct JavaScript file linkage in `index.html`

---

## Deployment Notice

This project does not include production or cloud deployment. Any execution method described, including Docker, is limited strictly to **localhost usage**.

