# Aww Agents

## I. Core Principles & Design Philosophy

- **Ambient & Permacomputing:** The system operates in the background, minimizing direct user interaction. It leverages existing habits and routines, integrating seamlessly into the user's life rather than demanding constant attention. Data collection is largely passive. Computation is prioritized locally, using minimal resources.
- **Agentic AI (OODA Loop):** The core intelligence is built around the Observe-Orient-Decide-Act loop, creating a proactive and adaptive system.
- **Local-First & Privacy-Preserving:** All raw data processing happens locally. Cloud APIs are used _judiciously_ and only for high-level, anonymized inferences.
- **Modularity & Extensibility:** The architecture is designed to be modular, allowing for easy swapping of components (different sensors, AI models, UI elements) and future expansion.
- **User Control & Transparency:** The user maintains full control over the system's actions and can override recommendations or adjust settings at any time. The reasoning behind decisions should be explainable (to the extent possible with AI).
- **Multi-Modal Data Fusion:** The system combines data from diverse sources to build a holistic understanding of the user's state and environment.

## II. Architectural Components

1. **Data Acquisition Layer (Sensors & Inputs)**
    
    - **Wearable Sensors (HealthConnect):**
        - Source: Android wearable devices via HealthConnect API.
        - Data: Heart rate, sleep stages, activity levels, steps, etc. (timeseries data)
        - Processing: Local aggregation, feature extraction (e.g., resting heart rate, sleep efficiency).
    - **Environmental Sensors:**
        - Source: RTL-SDR (rtl_433MHz) for door/cabinet openings, temperature/humidity sensors, air quality sensors. Could also include a smart electricity meter, if available.
        - Data: Event timestamps (door openings), environmental readings (timeseries).
        - Processing: Anomaly detection (e.g., unusual fridge opening frequency), data smoothing, and aggregation.
    - **Home State Imagery:**
        - Source: Periodic snapshots from strategically placed low-resolution cameras (e.g., repurposed webcams).
        - Data: Images of key areas of the home (e.g., living room, kitchen).
        - Processing: _Local_ object detection and spatial analysis (using a small, efficient model like YOLO-NAS or MobileNet). Count objects, identify misplaced items, assess overall "clutter" level. This data is _never_ sent to the cloud in image form.
    - **Journal/Notes (Obsidian):**
        - Source: User's Obsidian vault (Markdown files).
        - Data: Text entries, tags, timestamps.
        - Processing: Local natural language processing (sentiment analysis, topic extraction, keyword detection) using small, efficient models (e.g., Sentence Transformers for embeddings, or smaller LLMs).
    - **User Feedback & Input:**
        - Source: Web UI, potentially voice input via a local speech-to-text model.
        - Data: Explicit feedback on suggestions (thumbs up/down), manual goal setting, overrides.
        - Processing: Direct incorporation into the decision-making process.
    - **Weather Information:**
        - Source: A local weather station, or data from stations close to the user.
        - Data: Temperature, rain, cloud cover.
        - Processing: Aggregation and analysis.
2. **Data Processing & Storage Layer**
    
    - **Local Database:** A lightweight, embedded database (e.g., SQLite, DuckDB) to store processed sensor data, extracted features, user preferences, and system logs. This database resides on one of the user's homelab servers or the Mac Studio.
    - **Feature Extraction Modules:** Individual modules for each data source, responsible for cleaning, transforming, and extracting relevant features from raw data. These modules run locally.
    - **Data Fusion Engine:** Combines extracted features from different modalities into a unified representation of the user's state. This could involve simple rule-based combinations or more sophisticated techniques like Kalman filtering or Bayesian networks.
3. **Agentic AI Core (OODA Loop)**
    
    - **Observe:** Gathers data from the Data Processing Layer. This is the input to the Orient phase.
    - **Orient:**
        - **Contextualization:** Combines current observations with historical data, user preferences, and external knowledge (e.g., general health guidelines).
        - **Pattern Recognition:** Identifies patterns and anomalies in the user's behavior and environment. This might involve time-series analysis, clustering, or anomaly detection algorithms.
        - **Learning:** Updates internal models based on new data and user feedback. This could involve simple rule updates, reinforcement learning, or fine-tuning of pre-trained models. This step leverages local LLMs (running on the Mac Studio via LM Studio) for tasks like summarizing journal entries, identifying recurring themes, and relating observations to potential underlying causes. _Judicious_ use of cloud LLMs (OpenAI API) might be used for complex reasoning or knowledge retrieval, but _only_ with anonymized, high-level summaries.
    - **Decide:**
        - **Goal Evaluation:** Assesses progress towards user-defined goals (e.g., improve sleep quality, reduce stress, maintain a tidy home).
        - **Planning:** Generates potential actions (tips, reminders, schedule adjustments) to help the user achieve their goals. This could involve constraint satisfaction, optimization algorithms, or a rule-based system.
        - **Risk Assessment:** Evaluates the potential negative consequences of actions (e.g., suggesting a workout when the user is already fatigued).
    - **Act:**
        - **Action Execution:** Delivers interventions to the user via appropriate channels:
            - **Web UI:** Detailed information, explanations, and options for customization.
            - **Wearable Notifications:** Brief, timely reminders or prompts.
            - **IoT Dashboards (e-Paper):** Visual summaries, schedules, or motivational messages.
        - **Feedback Monitoring:** Tracks user responses to interventions (explicit feedback, changes in behavior).
4. **User Interface Layer**
    
    - **Web UI (Local):** A simple, locally hosted web application (e.g., built with Flask, React, or Vue.js) that allows the user to:
        - View system status and data summaries.
        - Set goals and preferences.
        - Provide feedback on interventions.
        - Override system recommendations.
        - Review historical data and trends.
    - **Wearable Integration:** Push notifications to the user's Android wearable device.
    - **IoT Dashboard Integration:** Display information on e-paper displays or other low-power IoT devices.

## III. Hardware & Software Implementation Notes

- **Distribution:** The system can be distributed across the user's hardware:
    - **Homelab Servers:** Data acquisition (sensor interfaces), data processing, database, web UI backend.
    - **Mac Studio:** Local LLM inference, heavier data processing tasks.
    - **Wearable/IoT Devices:** Data sources and output channels.
- **Communication:** Local network communication (e.g., MQTT, HTTP) between devices.
- **Software Stack (Examples - flexible):**
    - Programming Languages: Python (for most components), JavaScript (for web UI).
    - Databases: SQLite, DuckDB.
    - Message Queue: MQTT (for sensor data).
    - Web Framework: Flask, FastAPI, React, Vue.js.
    - AI/ML Libraries: TensorFlow Lite, PyTorch Mobile, Sentence Transformers, scikit-learn.
    - LLM Tools: LM Studio, Ollama, OpenAI API (judiciously).

**IV. AI Model Selection & Experimentation**

- **Local-First Preference:** Prioritize small, efficient models that can run on the available hardware.
- **Model Zoo:** Maintain a collection of candidate models for different tasks (e.g., object detection, sentiment analysis, time-series forecasting).
- **Automated Evaluation:** Implement a framework for automatically evaluating model performance based on user feedback and objective metrics (e.g., accuracy, F1-score, resource usage). This could involve:
    - **Reinforcement Learning (RL):** Train models to optimize for user satisfaction and goal achievement.
    - **A/B Testing:** Compare different models or configurations in a controlled manner.
    - **Hyperparameter Optimization:** Automatically tune model parameters to improve performance.

**V. Example Workflow**

1. **Observe:** RTL-SDR sensor detects frequent fridge openings at night. HealthConnect data shows poor sleep quality. Obsidian journal entry expresses feelings of stress.
2. **Orient:** The system identifies a potential correlation between nighttime eating, poor sleep, and stress. Local LLM summarizes the journal entry as "feeling overwhelmed and anxious."
3. **Decide:** The system evaluates the user's goal of "improve sleep" and "reduce stress." It plans to suggest a relaxing evening routine and avoiding late-night snacks. It assesses the risk of the suggestion being ignored.
4. **Act:** A notification is sent to the user's wearable an hour before bedtime: "Time to wind down! Try a warm bath or some light reading. Avoid screens and snacks before bed." The e-paper display shows a calming image and a reminder of the user's sleep goal. The system monitors whether the fridge is opened after the notification.

**VI. Key Advantages**

- **Privacy:** Data is processed locally, minimizing privacy risks.
- **Low Latency:** Local processing enables rapid responses.
- **Resilience:** The system can continue to function even without an internet connection.
- **Customization:** The modular architecture allows for easy adaptation to the user's specific needs and preferences.
- **Cost-Effective:** Leverages existing hardware and minimizes reliance on expensive cloud services.