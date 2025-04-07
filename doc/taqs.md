# Temporally Aware Quantified Self (TAQS) model

Blending data architecture with philosophical concepts like _consecutio temporum_ requires a model that's not just functional but also semantically rich. Let's approach this as architects, engineers, and a touch of philosophers.

The goal is a data model for Quantified Self (QS) that handles:

1. **Event Streams & Time Series:** The core data types.
2. **Point Events & Span Events:** Differentiating instantaneous occurrences from activities with duration.
3. **Temporal Modality (Consecutio Temporum inspired):** Representing past, present, future, probability, projection, and alternatives.
4. **Hierarchical Concepts & Events:** Linking high-level summaries to detailed logs.

Here's a proposed model, which we can call the **"Temporally Aware Quantified Self Model" (TAQS Model)**.

---

## TAQS Data Model Core Entities

We'll define the main entities and their relationships. I'll use a conceptual representation that can be translated into relational (SQL), document (NoSQL), or graph database structures.

**1. `Concept`**

- **Purpose:** Represents the _what_ is being measured or recorded. These form a hierarchy.
- **Attributes:**
    - `concept_id`: Unique identifier (e.g., UUID, `concept:work:programming:python`)
    - `name`: Human-readable name (e.g., "Work", "Sleep", "Programming", "Python Development", "CPU Usage", "Window Title")
    - `description`: Optional longer description.
    - `parent_concept_id`: Foreign key to `Concept` (self-referencing) to establish hierarchy (nullable for root concepts).
    - `type`: (Optional) Enum like `ACTIVITY`, `METRIC`, `STATE`, `LOCATION`, etc.
    - `meta`: JSON/Dictionary for additional properties (e.g., expected units for metrics like '%', 'bpm', 'count'; default visualization hints).

**2. `Source`**

- **Purpose:** Represents the _origin_ of the data.
- **Attributes:**
    - `source_id`: Unique identifier (e.g., UUID, `source:manual:diary`, `source:app:activitywatch`)
    - `name`: Human-readable name (e.g., "Manual Diary Entry", "ActivityWatch", "Oura Ring", "Weather API")
    - `type`: Enum like `MANUAL`, `SENSOR`, `APPLICATION`, `API`, `PLUGIN`.
    - `description`: Optional details about the source.
    - `meta`: JSON/Dictionary for source-specific details (e.g., device ID, API version, configuration).

**3. `Stream`**

- **Purpose:** Represents a specific flow of data _about_ a `Concept` _from_ a `Source`. This is the container for related events.
- **Attributes:**
    - `stream_id`: Unique identifier (e.g., UUID).
    - `concept_id`: Foreign key to `Concept`. (What this stream measures/records).
    - `source_id`: Foreign key to `Source`. (Where the data comes from).
    - `name`: (Optional) Specific name for this stream instance (e.g., "My Laptop ActivityWatch Window Titles").
    - `description`: (Optional) Further details.
    - `meta`: JSON/Dictionary for stream-specific settings (e.g., sampling rate if applicable, retention policy).

**4. `Event`** (The core data point)

- **Purpose:** Represents a single data point or activity span, incorporating the temporal nuances.
- **Attributes:**
    - `event_id`: Unique identifier (e.g., UUID).
    - `stream_id`: Foreign key to `Stream`. (Which stream this event belongs to).
    - `timestamp`: **Timestamp with Timezone**. This marks the _occurrence time_ of the event. For spans, it's the _start time_. **Crucial:** This timestamp defines its position on the main timeline.
    - `duration`: **Interval/Duration Type (Nullable)**.
        - If `NULL` or `0`, it's a **point event** (like a sample, a single log entry).
        - If > `0`, it's a **span event** (like a traced activity, a meeting). The event covers the time range `[timestamp, timestamp + duration)`.
    - `temporal_modality`: **Enum**. This is the core of the _consecutio temporum_ aspect. Values could include:
        - `PAST_ACTUAL`: Happened, recorded as fact. (Standard log data).
        - `PAST_RECALLED_UNCERTAIN`: Happened, but recalled with some uncertainty (e.g., manually entered past event).
        - `PAST_INFERRED`: Deduced to have happened based on other data, not directly observed.
        - `PRESENT_ONGOING`: A span event that is currently in progress (its duration might be unknown or dynamically updated until it ends). Point events are rarely 'ongoing'.
        - `FUTURE_PLANNED`: Intended to happen (e.g., calendar appointment, planned workout).
        - `FUTURE_PROJECTED`: Predicted or forecasted to happen based on models or trends (e.g., projected sleep time, predicted arrival time).
        - `HYPOTHETICAL_ALTERNATIVE`: Represents a what-if scenario, a counterfactual, or an alternative plan not taken.
        - `HYPOTHETICAL_POSSIBILITY`: Represents a potential future or past event whose occurrence is/was conditional or uncertain.
    - `confidence`: **Float (0.0 to 1.0, Nullable)**. Quantifies the certainty, especially useful for `_UNCERTAIN`, `_INFERRED`, `_PROJECTED`, `_POSSIBILITY` modalities. Can be derived from temporal_distribution when available.
    - `data_payload`: **Flexible Data Type (JSON, Dictionary, specific types)**. Contains the actual value(s) or descriptive data for the event.
        - For time series: `{ "value": 75.5, "unit": "%" }`
        - For activity log: `{ "window_title": "TAQS Model Design", "app_name": "Obsidian" }`
        - For diary entry: `{ "text": "Felt productive working on the data model." }`
    - `parent_event_id`: Foreign key to `Event` (self-referencing, nullable). Establishes hierarchical links between events. E.g., multiple detailed `ActivityWatch` events could be children of a single high-level "Work on Project X" diary span event.
    - `scenario_id`: **UUID/String (Nullable)**. Groups related `HYPOTHETICAL_` events together to represent a single alternative scenario or "branch" of reality/planning.
    - `recorded_at`: **Timestamp with Timezone**. When the event was actually inserted into the system (distinct from `timestamp` which is occurrence time). Useful for auditing and understanding data latency.
    - `meta`: JSON/Dictionary for event-specific context not fitting elsewhere.

---

## How the Model Addresses Requirements:

1. **Event Streams & Time Series:**
    
    - `Stream` acts as the container.
    - Time series are streams of `Event`s (typically point events, `duration`=null) where `data_payload` contains numeric values. The `Concept`'s metadata can define units.
    - General event streams are handled similarly, with richer `data_payload` structures.
2. **Point Events & Span Events:**
    
    - The `duration` attribute explicitly distinguishes them. `duration = NULL` or `0` implies a point event; `duration > 0` implies a span event covering `[timestamp, timestamp + duration)`.
    - This maps well to sampling (point) vs. tracing (span) profiling analogies.
3. **Temporal Modality (Consecutio Temporum inspired):**
    
    - The `temporal_modality` enum directly encodes the state:
        - _Past:_ `PAST_ACTUAL`, `PAST_RECALLED_UNCERTAIN`, `PAST_INFERRED`.
        - _Present:_ `PRESENT_ONGOING` (primarily for spans). "Current" state is often the latest `PAST_ACTUAL` event in a relevant stream.
        - _Future:_ `FUTURE_PLANNED`, `FUTURE_PROJECTED`.
        - _Probable/Uncertain:_ Handled by specific modalities (`PAST_RECALLED_UNCERTAIN`, `PAST_INFERRED`, `HYPOTHETICAL_POSSIBILITY`) often paired with the `confidence` score.
        - _Alternative/Conjunctive:_ Handled by `HYPOTHETICAL_ALTERNATIVE`, `HYPOTHETICAL_POSSIBILITY`, grouped by `scenario_id`.
4. **Hierarchical Concepts & Events:**
    
    - `Concept.parent_concept_id` defines the semantic hierarchy (e.g., "Coding" is part of "Work").
    - `Event.parent_event_id` allows linking specific event instances. A high-level "Work" span manually entered in a diary (`Source`="Manual Diary") can be the parent of multiple automatically tracked "Coding" spans (`Source`="ActivityWatch") that occur within its timeframe. This requires logic during data ingestion or analysis to establish these links if not explicitly provided.

---

## Implementation Considerations:

- **Database Choice:**
    - **Relational (e.g., PostgreSQL):** Good for structured relations, ACID compliance. Handles JSONB well. Time/interval types are native. Recursive queries (CTEs) needed for hierarchy traversal. Indexing on timestamps (`timestamp`, `timestamp + duration`), foreign keys (`stream_id`, `concept_id`), and `temporal_modality` is crucial. TimescaleDB extension for PostgreSQL is excellent for time-series performance.
    - **Document (e.g., MongoDB):** Flexible schema (`data_payload`). Can embed related data but makes complex relational queries (like hierarchy) harder. Geospatial and time-series features are improving.
    - **Time Series (e.g., InfluxDB, TimescaleDB):** Optimized for timestamped data, high ingest/query performance for time-based aggregations. May need careful schema design to handle the rich relationships and modalities. Often paired with another DB for metadata.
    - **Graph (e.g., Neo4j):** Naturally handles hierarchies (`parent_concept_id`, `parent_event_id`) and complex relationships. Querying temporal ranges and modalities might be less optimized than specialized TSDBs.
- **Indexing:** Regardless of DB, heavy indexing on `timestamp`, `stream_id`, `concept_id`, `temporal_modality`, and potentially fields within `data_payload` will be essential for query performance. For spans, indexing the calculated `end_time` (`timestamp + duration`) is often beneficial for range queries.
- **API Design:** The API for ingesting and querying data should reflect the model's richness, allowing filtering by time range, modality, concept hierarchy, event hierarchy, source, etc.
- **Consistency & Logic:** Defining clear rules for setting `temporal_modality`, managing `PRESENT_ONGOING` events (how/when do they transition to `PAST_ACTUAL`?), and linking parent/child events is vital. This logic might reside in the application layer or database triggers/procedures.

---

## Philosophical Reflection:

This TAQS model attempts to capture the fluidity and uncertainty inherent in our experience and recording of time, moving beyond simple factual logs. By explicitly modeling modality (planned, actual, projected, hypothetical), duration, and hierarchy, it allows for a much richer representation of personal data, aligning with the nuanced way we perceive and structure our lives – past, present, and future. It acknowledges that not all data has the same epistemological status, reflecting the inspiration from _consecutio temporum_ – the sequence and relationship of temporal states.

This model provides a robust foundation. The specific implementation details and the precise definitions/use of the `temporal_modality` enum values would need further refinement based on the exact application requirements.

---

## Architecture Evaluation

### 1. Alignment with Architecture Components:

- **`aww-data-vault`**: The TAQS model provides a well-defined structure for the data intended to reside in this vault. The four core entities (`Concept`, `Source`, `Stream`, `Event`) logically organize the diverse data expected.
    
- **Data Sources:** The architecture shows various inputs (Web History, Mobile Activity, Sensors, Manual Input, APIs). The `Source` entity in TAQS directly maps to these, allowing clear tracking of data provenance.
    
- **Data Types:** The architecture implies a mix of data (time series, activity logs, notes). TAQS handles this through:
    
    - Distinction between point events (`duration`=null) and span events (`duration`>0).
        
    - Flexible `data_payload` for varied event content.
        
    - `Stream` and `Concept` entities for organizing different data types (e.g., a stream for "CPU Usage" concept vs. a stream for "Browser History" concept).
        
- **Agentic AI / Processing:** The richness of the TAQS model, particularly the `temporal_modality` and `hierarchy` features, provides valuable semantic context that advanced AI components can leverage for deeper understanding, planning, prediction, and reasoning about uncertainty.
    

### 2. Compatibility with Storage Strategy (Parquet + SQLite + Arrow):

- **`Parquet for Event Data:`** This is an excellent choice.
    
    - **Suitability:** Parquet's columnar format is highly efficient for storing large volumes of event data and performing analytical queries, which are common in QS.
        
    - **Mapping:** The `Event` entity's attributes (timestamps, duration, modality, confidence, payload, IDs) map well to Parquet columns. The JSON `data_payload` can be stored efficiently.
        
    - **Benefit:** Compression and encoding schemes in Parquet will significantly reduce storage footprint.
        
- **``` `` `SQLite for Metadata (Concept, Source, Stream):` `` ```** This is a practical approach for a local-first or desktop application.
    
    - **Suitability:** SQLite is lightweight and provides relational capabilities needed to manage the relationships and hierarchies between Concepts, Sources, and Streams.
        
    - **Mapping:** These entities translate directly into SQLite tables.
        
    - **Function:** SQLite can act as an index or catalog, helping locate relevant data within the Parquet files without needing to scan everything for metadata-based queries.
        
- **Apache Arrow for Interchange:** Using Arrow as the in-memory format for reading/writing Parquet and for passing data between components (`aww-data-vault`, `aww-core`, AI modules) is ideal. It minimizes serialization overhead and leverages a common columnar representation.
    

### 3. Handling Key TAQS Features:

- **Temporal Modality:** Storing the `temporal_modality` enum and `confidence` score in Parquet allows efficient filtering and analysis based on the data's temporal status and certainty.
    
- **Hierarchy:**
    
    - `Concept` hierarchy can be managed within the SQLite metadata database.
        
    - `Event` hierarchy (`parent_event_id`) can be stored directly in the Parquet event records. Querying this hierarchy might involve joins or lookups potentially spanning SQLite and Parquet, or graph-like processing if using appropriate tools.
        
- **Point vs. Span Events:** The `duration` field is easily stored in Parquet. Querying events active during a specific time range will involve checking `timestamp` and `timestamp + duration`, which is feasible with Parquet, though partitioning strategies can optimize this.
    

### 4. Potential Considerations:

- **Query Performance:** Querying across large Parquet datasets, especially for complex time-range or hierarchical queries, needs consideration. Partitioning Parquet files (e.g., by date, `stream_id`) and potentially using query engines optimized for Parquet (like DuckDB, which also integrates well with SQLite and Arrow) can help.
    
- **Consistency:** Maintaining consistency between the SQLite metadata and the Parquet event data requires careful application logic, especially if updates/deletions occur (though much QS data is append-only).
    
- **Schema Evolution:** Plan how schema changes (e.g., adding fields to `data_payload`) will be handled in the Parquet files over time.


#### Areas for Improvement

1. Temporal Edge Cases
   
   - No explicit handling of recurring events (e.g., daily routines, weekly meetings)
   - Missing handling of events with uncertain start/end times

2. Data Validation
   
   - No explicit constraints on data_payload structure per concept type
   - Missing schema validation mechanisms for JSON/Dictionary data
   - Could benefit from explicit data quality indicators beyond confidence

3. Relationship Modeling
   
   - Only hierarchical relationships are modeled ( parent_concept_id , parent_event_id )
   - Missing lateral relationships between events (e.g., "blocked by", "triggered by")
   - No explicit modeling of causal relationships

4. Performance Considerations
   
   - Deep hierarchies might lead to expensive recursive queries
   - No explicit partitioning strategy for high-volume streams
   - Missing indexing recommendations for data_payload contents

**1. `Concept`**
- Add attributes:
    - `payload_schema`: JSON Schema for validating data_payload
    - `validation_rules`: Custom validation rules
    - `quality_metrics`: Required data quality indicators

**3. `Stream`**
- Add attributes:
    - `partition_strategy`: How to partition high-volume data
    - `retention_policy`: Data lifecycle management
    - `index_fields`: Array of data_payload fields to index
    
**4. `Event`**
- Add attributes:
    - `recurrence_pattern`: For recurring events (iCal RRule format)
    - `timezone`: Explicit timezone handling
    - `temporal_distribution`: Statistical representation of temporal uncertainty. Can be:
        - Gaussian mixture (mean, stddev, weights)
        - Von Mises (for circular/periodic time)
        - Fuzzy set (membership function parameters)
        - Human-readable description (for manual entries)
    - `distribution_origin`: How the distribution was derived:
        - `INFERRED`: From probabilistic programming/modeling
        - `OBSERVED`: From statistical analysis of past events
        - `HUMAN_ESTIMATED`: From fuzzy human judgment
        - `LLM_GENERATED`: From language model reasoning

New Entity: **`EventRelation`**
- **Probabilistic Links:**
    - Add `causal_probability` field (0.0 to 1.0)
    - Add `temporal_constraint` field (e.g., "before", "during", "after" with distribution)
    - Add `evidence_source` field (tracking what supports this relation)
- **Attributes:**
    - `relation_id`: Unique identifier
    - `source_event_id`: From Event
    - `target_event_id`: To Event
    - `relation_type`: Enum (BLOCKS, TRIGGERS, CORRELATES, etc.)
    - `strength`: Float (0.0 to 1.0) for correlation strength
    - `meta`: Additional relationship context