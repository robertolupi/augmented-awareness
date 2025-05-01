# taqs.md tech-choices.md How could fuzzy logic and temporal distributions be encoded in parquet files?

Based on the TAQS model and tech choices, here's how fuzzy temporal data could be encoded in Parquet files:

1. **For the `temporal_distribution` field** (added to the `Event` entity), we can use Parquet's complex types:

```markdown:/Users/rlupi/src/augmented-awareness/doc/taqs.md
**4. `Event`**
- `temporal_distribution`: **STRUCT Type** in Parquet containing:
    - `distribution_type`: ENUM (GAUSSIAN, VON_MISES, FUZZY_SET, DESCRIPTIVE)
    - `parameters`: MAP<STRING, DOUBLE> (distribution-specific parameters)
    - `human_description`: STRING (optional human-readable explanation)
```

2. **Example Parquet schema additions**:

```plaintext:/Users/rlupi/src/augmented-awareness/doc/tech-choices.md
# Data Storage and formats
## Parquet Schema Extensions for Temporal Distributions

For fuzzy temporal data, the Parquet schema would include:

1. Basic temporal fields:
   - `timestamp`: TIMESTAMP (MICROS) with timezone
   - `duration`: INT64 (microseconds)
   
2. Distribution fields (nested structure):
   - `temporal_distribution.distribution_type`: ENUM
   - `temporal_distribution.parameters`: MAP<STRING, DOUBLE>
     - Gaussian: {"mean": 0.0, "stddev": 1.0}
     - Von Mises: {"mu": 3.14, "kappa": 2.0}
     - Fuzzy: {"membership_function": "trapezoidal", "a": 0, "b": 1, "c": 2, "d": 3}
   - `temporal_distribution.human_description`: STRING
```

3. **Implementation considerations** from both files:

- **Python/Rust/Julia**: All support Parquet writing with complex types
- **Arrow**: Provides native support for these nested types before Parquet serialization
- **Performance**: The MAP type allows flexible parameters while maintaining query efficiency
- **Validation**: The `payload_schema` in `Concept` can specify expected distribution formats

4. **Example data encoding**:

For a fuzzy event with uncertain timing:
```json
"temporal_distribution": {
    "distribution_type": "FUZZY_SET",
    "parameters": {
        "membership_function": "triangular",
        "a": "2023-01-01T00:00:00Z",
        "b": "2023-01-01T12:00:00Z", 
        "c": "2023-01-02T00:00:00Z"
    },
    "human_description": "Probably happened midday Jan 1st"
}
```

This approach leverages Parquet's strengths while maintaining compatibility with the Arrow-based processing pipeline specified in the tech choices.

# Consider the following markdown excerpt, that encodes a schedule using the format used in obsidian.py and test_obsidian.py , where each event roughly ends when another one starts. Use the fuzzy encoding for temporal distribution that you proposed to encode the same data in JSON:

```
06:03 wake up
06:45 #consume/read/web
08:12 #create/write/blog  post [[How Beelzebub Was Born]] to HN, substack, medium, and share with friends
08:33 #consume/read/web
10:26 Chiamata con Nonna
10:56 #consume/read/web
13:00 lunch
13:30 #aww  documentation
14:03 #consume/read/web
14:48 #aww
15:54 pause
```

Here's how you could encode this schedule with fuzzy temporal distributions in JSON format, following the TAQS model's proposed structure:

```json:/Users/rlupi/src/augmented-awareness/python/aww/observe/obsidian_events.json
{
  "events": [
    {
      "name": "wake up",
      "timestamp": "2023-06-15T06:03:00Z",
      "temporal_distribution": {
        "distribution_type": "GAUSSIAN",
        "parameters": {
          "mean": 0,
          "stddev": 300
        },
        "human_description": "Probably woke up around 6:03am ±5 minutes"
      },
      "duration": {
        "distribution_type": "FUZZY_SET",
        "parameters": {
          "membership_function": "triangular",
          "a": 2400,
          "b": 2520,
          "c": 2640
        },
        "human_description": "Took about 40-45 minutes to fully wake up"
      },
      "tags": [],
      "temporal_modality": "PAST_RECALLED_UNCERTAIN",
      "confidence": 0.85
    },
    {
      "name": "web reading",
      "timestamp": "2023-06-15T06:45:00Z",
      "temporal_distribution": {
        "distribution_type": "GAUSSIAN",
        "parameters": {
          "mean": 0,
          "stddev": 600
        }
      },
      "duration": {
        "distribution_type": "FUZZY_SET",
        "parameters": {
          "membership_function": "trapezoidal",
          "a": 5400,
          "b": 5800,
          "c": 6200,
          "d": 6600
        }
      },
      "tags": ["consume/read/web"],
      "temporal_modality": "PAST_RECALLED_UNCERTAIN",
      "confidence": 0.8
    },
    {
      "name": "blog post writing",
      "timestamp": "2023-06-15T08:12:00Z",
      "temporal_distribution": {
        "distribution_type": "GAUSSIAN",
        "parameters": {
          "mean": 0,
          "stddev": 300
        }
      },
      "duration": {
        "distribution_type": "FUZZY_SET",
        "parameters": {
          "membership_function": "triangular",
          "a": 1200,
          "b": 1260,
          "c": 1320
        }
      },
      "tags": ["create/write/blog"],
      "temporal_modality": "PAST_ACTUAL",
      "confidence": 0.95,
      "data_payload": {
        "title": "How Beelzebub Was Born",
        "platforms": ["HN", "substack", "medium"]
      }
    },
    // ... similar encoding for other events ...
    {
      "name": "pause",
      "timestamp": "2023-06-15T15:54:00Z",
      "temporal_distribution": {
        "distribution_type": "DESCRIPTIVE",
        "human_description": "Approximate time recalled from memory"
      },
      "duration": null,
      "tags": [],
      "temporal_modality": "PAST_RECALLED_UNCERTAIN",
      "confidence": 0.7
    }
  ],
  "metadata": {
    "source": "manual_entry",
    "recorded_at": "2023-06-15T20:00:00Z",
    "timezone": "Europe/Rome"
  }
}
```

Key aspects of this encoding:

1. Each event has both precise timestamps and fuzzy temporal distributions
2. Duration uncertainty is modeled using fuzzy sets (triangular/trapezoidal membership functions)
3. Different confidence levels reflect recall certainty
4. The `temporal_modality` field indicates whether events were directly observed or recalled
5. Tags are preserved from the original format
6. Additional context is stored in `data_payload` where relevant
7. The entire schedule has source metadata

The parameters for the fuzzy distributions would need to be calibrated based on:
- For timestamps: How precisely the time was recorded/remembered
- For durations: The natural variability in activity durations
- Confidence scores: How certain you are about each event's timing

# Now read the JSON representation, and translate it into natural language.

Here's a natural language translation of the JSON schedule representation, incorporating the temporal uncertainty modeling from the TAQS framework:

"On June 15th, I likely woke up around 6:03am, give or take 5 minutes (85% confident about this timing). The waking up process probably took between 40-45 minutes to feel fully alert. 

Around 6:45am (with a possible 10-minute margin of error), I spent approximately 90-110 minutes reading content on the web (80% confidence in this estimate). 

At roughly 8:12am (±5 minutes), with high confidence (95%), I worked on writing and publishing a blog post titled 'How Beelzebub Was Born' - this took me about 20-22 minutes. I shared it on Hacker News, Substack, and Medium.

[Additional events would follow the same pattern...]

The day included a call with Grandma around 10:26am, more web reading sessions (each with their own temporal uncertainty estimates), lunch at approximately 1pm, documentation work for the AWW project starting around 1:30pm, and a pause beginning at about 3:54pm (70% confident about this last timing).

All these timings represent my best recollection with varying degrees of certainty, where more precisely recorded activities (like the blog post) have higher confidence scores than those I'm estimating after the fact."

Key aspects preserved from the JSON/TAQS model:
- Explicit confidence levels for each event
- Temporal distributions represented as natural ranges
- Distinction between precise recordings and fuzzy recollections
- Duration uncertainty modeled as time ranges
- Source attribution ("my best recollection")