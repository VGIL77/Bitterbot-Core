BitterBot Memory & Dream Engine System
Last updated:  2025 05 01
Why consolidate?
Memory and the Dream Engine are two sides of the same coin: the Dream Engine generates and compresses experiences, while the Memory System stores and retrieves them. Treating them as a single subsystem clarifies data flow, avoids duplication, and gives developers one place to extend or audit BitterBot’s long term cognition.
________________________________________
1 High Level Architecture
┌─────────────── Local Node ────────────────┐        ┌────── Parent Brain Cluster ──────┐
│    UI  │  Orchestrator │  Dream Engine │  │  ⇆   │  Aggregator  │  Memory Graph  │
│         ↘ store_mem()  ↙ retrieve_mem() │       │  DP Filter   │  Cluster Embed │
└───────────────────────────────────────────┘        └───────────────────────────────────┘
•	Local Node — personalised, encrypted, ≤ 200 MB.
•	Parent Brain — federated, DP anonymised global knowledge.
________________________________________
2 Local Node Memory Layers
Layer	Purpose	Storage	Size Limit
Working	Active LangGraph context	RAM	transient
Episodic	Per query traces, tool paths	SQLite table episodic	30 d or 10 k rows
Embeddings	Vectorised semantics of user patterns	Qdrant (local) or FAISS file	128 k vectors
Personal Notes	Explicit facts, reminders	notes.json (encrypted)	user bounded
Dream Compression	Curated, high utility lessons	SQLite dream_lessons + vector index	5 k lessons
2.1 Trace Schema (JSON)
{
  "id": "uuid",
  "timestamp": "2025 05 01T07:18:00Z",
  "conversation_id": "abc 123",
  "input": "Book me a flight to Paris",
  "tools": ["serpapi", "gpt 4o"],
  "output": "Here are flight options…",
  "embedding": [0.013, 0.42, …],
  "importance": 0.74,
  "hits": 3,
  "dream_tagged": false
}
________________________________________
3 Dream Engine (Downtime Optimisation)
3.1 Modules
Module	Action
Trace Replayer	Re runs stored traces; measures outcome delta
Prompt Mutator	Generates “what if” variants of past prompts
Critique Module	LLM rates decisions → adjusts importance
Memory Consolidator	Writes new/updated lessons to dream_lessons
Curiosity Updater	Calculates novelty_score ⇒ replay queue
3.2 Curiosity Heuristic
novelty = entropy(plugin_path) + unexplored_model + surprise(outcome)
if novelty > τ: schedule_for_replay()
3.3 Safeguards
•	No external network calls in dream mode.
•	Writes marked dream_tagged; require confidence ≥ 0.8.
•	Dreams auditable via Dev UI “Dream Log”.
________________________________________
4 Parent Brain Global Memory
Component	Purpose	Tech
DP Filter	Strip PII, add Gaussian noise	Opacus style DP SGD
Cluster Embeddings	Thematic vector clusters	Qdrant multi tenant
Memory Graph	Cross node concept/task graph	Neo4j / RDF store
Prompt Template Library	Evolving best practice prompts	Git versioned repo
Cross Client Curiosity Feed	Surprising traces broadcast	Gossip over libp2p
Weekly digest pushes “cluster summary” back to nodes → cached in local embeddings.
________________________________________
5 APIs
5.1 LangGraph helper
def store_mem(item: dict):
    # insert into SQLite + vector DB and return id

def retrieve_mem(query: str, k: int = 4) -> list[dict]:
    # similarity search & importance sort
5.2 Dream Engine trigger
POST /api/dream/run   {"mode": "idle", "max_minutes": 20}
________________________________________
6 Roadmap
1.	MVP (May 2025) – SQLite + FAISS, live save & simple retrieve.
2.	Nightly Dream Job – replay + compression, curiosity metric.
3.	DP sync → Parent Brain – FedAvg of anonymised lessons.
4.	Global Cluster Digest – push down distilled templates & skills.
5.	Memory Visualiser UI – graph of concepts, user can prune.
________________________________________
7 Summary
The consolidated Memory & Dream subsystem gives BitterBot a lightweight yet powerful cognitive loop: experience → memory → dream → skill → better experience. Local personalisation stays private, while federated distillation drives collective intelligence—paving the road to an emergent, self-improving agent network.

