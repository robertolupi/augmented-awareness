## **TAQS Data Partitioning and Processing Strategy**

This document outlines how the Temporally Aware Quantified Self (TAQS) model entities are partitioned across the chosen storage technologies (SQLite, Apache Parquet) based on the tech-choices.pdf document, using data source examples from aww-agents.pdf, and incorporating an immutable raw data layer with derived event generation.

### **Core Technologies**

* **Metadata Storage:** SQLite  
* **Event Data Storage:** Apache Parquet (multiple datasets/layers)  
* **Data Interchange:** Apache Arrow

### **Partitioning Details**

1. **Metadata Storage (SQLite):**  
   * **Purpose:** Stores the relatively static, relational information that defines and organizes data concepts and sources (both raw and processing stages). SQLite acts as the central catalog.  
   * **TAQS Entities:**  
     * Concept: Defines *what* is measured or inferred (e.g., "Heart Rate", "Sleep Stage", "Room Temperature", "Journal Sentiment", "Fridge Door Opening", "Window Title", "Sleep Quality Correlation", "Evening Routine Plan"). Includes hierarchy. Managed via the processing steps.  
     * Source: Defines *where* data originates. This includes **raw sources** (e.g., "HealthConnect API", "RTL-SDR Sensor", "Obsidian Vault", "ActivityWatch") and **processing sources** representing stages that generate derived data (e.g., "Concept Assigner", "OODA-Orient-Summarizer", "OODA-Decide-Planner", "Aggregation Service"). New sources are registered here as needed.  
     * Stream: Defines the specific flow linking a Concept to a Source (e.g., "HealthConnect-HeartRate", "RTL-SDR-FridgeDoorEvents", "OODA-Orient-Summarizer-JournalSummary", "OODA-Decide-Planner-SleepGoalAction"). This link is established/updated during processing steps when derived events are generated.  
2. **Raw Event Data Storage (Apache Parquet \- Layer 1: Immutable Raw):**  
   * **Purpose:** Store the high-volume, time-based event data exactly as it arrived from external sources. This layer is treated as **immutable** (append-only).  
   * **TAQS Entity:**  
     * Event: Represents the individual raw data points or activity spans. Stores attributes like event\_id, source\_id (referencing the *raw* source), timestamp, duration, data\_payload, etc. stream\_id is typically not relevant/present at this raw stage.  
   * **Partitioning:** Parquet files are partitioned primarily by **date** and **source\_id** (raw source). This reflects the arrival pattern.  
   * **Examples from Aww-Agents:**  
     * Data from "HealthConnect API" (source\_id) arrives and is stored immutably in Parquet files under its source ID and the event date.  
     * Similarly, raw events from "RTL-SDR Sensor" (source\_id) are stored under its partition.  
3. **Event Processing & Derived Data Generation (Apache Parquet \- Layer 2+):**  
   * **Purpose:** To analyze raw events, assign concepts, aggregate data, perform OODA loop functions (Orient, Decide), and generate *new*, enriched, or summarized events.  
   * **Workflow (Conceptual):**  
     1. Processing agents/jobs read data from the Raw Event Layer (or subsequent derived layers) using Apache Arrow.  
     2. **Concept Assignment:** An initial process analyzes raw Event data (source\_id, data\_payload) to determine the appropriate concept\_id.  
     3. **OODA Loop Integration:**  
        * **Orient:** Processes read raw/derived events, perform analysis (e.g., correlation, summarization), and generate *new* "insight" events. These new events have a source\_id like "OODA-Orient-CorrelationDetector" and a relevant concept\_id (e.g., "Correlation:NightEating-PoorSleep").  
        * **Decide:** Processes read insight events, evaluate goals, and generate *new* "decision" or "plan" events (e.g., source\_id: "OODA-Decide-Planner", concept\_id: "PlannedAction:SuggestEveningRoutine", temporal\_modality: FUTURE\_PLANNED).  
     4. **Metadata Update (SQLite):**  
        * Ensure relevant Concept, Source (for the processing step), and Stream entries exist in SQLite.  
     5. **Derived Event Generation (Parquet):** The process writes **new** Event records to Parquet. These records:  
        * Have a source\_id identifying the *processing step* that created them.  
        * Have the relevant stream\_id populated (linking the concept and the processing source).  
        * May contain aggregated or transformed data in their data\_payload.  
        * Can be stored in separate Parquet datasets/directories or use different partitioning schemes (e.g., by date and processing\_source\_id, or by stream\_id) optimized for downstream consumption.  
4. **Data Interchange (Apache Arrow):**  
   * **Purpose:** Serve as the efficient, in-memory columnar format for moving data between storage layers (Parquet/SQLite) and processing components (ingestion, OODA agents, analysis tools).  
   * **Usage:** Used heavily when reading from any Parquet layer, passing data between processing steps, and writing derived events back to Parquet.

### **Summary**

This strategy establishes a clear data flow: Raw, immutable events land in a primary Parquet layer partitioned by source and date. Subsequent processing steps (including concept assignment and OODA loop stages like Orient and Decide) read from existing layers, perform transformations or analysis, update the SQLite metadata catalog (registering concepts, processing sources, and streams), and write **new, derived** Event records into separate Parquet datasets/layers. This preserves raw data integrity, provides clear data lineage, and allows flexible analysis across different stages of data processing.