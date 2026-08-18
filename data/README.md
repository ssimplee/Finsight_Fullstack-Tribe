# Data

Authoritative disease profiles, sources, knowledge chunks, image metadata, and evaluation cases live here.

Member 2 owns most of this folder. Member 1 should keep backend loaders compatible with these filenames.

## Current contents

- `knowledge/conditions.json`: five scoped condition profiles.
- `knowledge/sources.json`: source registry with stable IDs and locators.
- `knowledge/knowledge_chunks.jsonl`: retrieval-ready evidence chunks.
- `images/image_sources.json`: licensed candidate image sources; no clinical images are committed yet.
- `evaluation/cases/`: synthetic cases for testing, not real clinical records.

## Safety and provenance

Clinical signs support a differential but do not confirm a diagnosis. Keep `source_id` and `locator` attached when ingesting chunks into RAG. Do not turn the old pharmaceutical measures in the FAO species table into treatment recommendations; FAO explicitly says their inclusion is not an endorsement.
