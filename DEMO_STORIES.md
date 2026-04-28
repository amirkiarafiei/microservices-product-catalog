# Context Layer — Demo Stories (Step-by-Step)

This guide provides the exact scripts and prompts for demonstrating the **Context Layer** using Claude Code.

## 🏁 Preparation Checklist
1. **Activate Persona**: Copy the "Siloed Agent Persona" block from `AGENTS.md` into this repo's `CLAUDE.md`.
2. **Start Claude Code**: Run `claude` in the root of this repository.
3. **Connect MCP**: Ensure your Claude Desktop/Code is connected to the Context Layer MCP (remote or local).

---

## 🏗️ Story 1: The "Blind" Saga Trace
**Goal**: Show Claude failing to trace a cross-repo transaction, then solving it with one "Narrative" call.

### 1. The "Without" Phase (The Pain)
**Prompt**: 
> *"I'm investigating a bug in the Product Offering Publication flow. A user published an offering in the `offering-service`, but it's not showing up in the Store Search. Where does the data go after it leaves the Offering service?"*

**Expected Claude Behavior**:
Claude will look at `services/offering-service/`, see it starts a saga, and say:
*"I see the publication starts here, but I have no visibility into which service consumes the events or handles the store indexing. I'd need access to every other repo in the company to find out. I'm stuck."*

### 2. The Trigger
**Prompt**: 
> *"Use Context Layer. Check the Workspace Narrative."*

### 3. The "With" Phase (The Wow)
**Expected Claude Behavior**:
Claude calls `get_wiki_content(scope: 'workspace')` and reports:
*"The Context Layer Narrative reveals that the `offering-publication-saga` spans four services. The missing search data is handled by the `store-query-service` (specifically the `create-store-entry` worker). You should check `services/store-service` for indexing failures."*

---

## 🛡️ Story 2: The "Multi-Repo Minefield"
**Goal**: Show that per-repo security reviews miss systemic risks in shared dependencies.

### 1. The "Without" Phase (The Pain)
**Prompt**: 
> *"Do a security review of the `catalog-service`. Is it safe to deploy?"*

**Expected Claude Behavior**:
Claude reviews the service in isolation and says:
*"The code in `catalog-service` looks clean. No obvious vulnerabilities found. However, I can't see the security posture of the services it depends on (like Auth or Identity)."*

### 2. The Trigger
**Prompt**: 
> *"Run a cross-repo intelligence audit."*

### 3. The "With" Phase (The Wow)
**Expected Claude Behavior**:
Claude calls `get_code_intelligence(topic: 'overview')` and reports:
*"While `catalog-service` is clean, the Context Layer has identified **2 High-Severity** vulnerabilities in its upstream dependencies:*
1. *`sec-001` in **identity-service**: RSA private key is exposed in env vars.*
2. *`sec-002` in **offering-service**: SSRF vulnerability in the Camunda client.*
*Conclusion: Do not deploy until identity-service is patched."*

---

## 🧪 Story 3: The "Black Box" Library
**Goal**: Show Claude using an internal SDK correctly without ever reading its source code.

### 1. The "Without" Phase (The Pain)
**Prompt**: 
> *"I need to implement a new saga step using the `shared-chassis` library. How do I use the `SagaManager` to execute a task?"*

**Expected Claude Behavior**:
Claude will guess:
*"I haven't seen the `shared-chassis` source code. I'll guess it's `SagaManager.start(saga_id, payload)`, but I might be wrong. I'd need to burn thousands of tokens indexing the whole library to be sure."*

### 2. The Trigger
**Prompt**: 
> *"Ask the Context Layer about the SDK."*

### 3. The "With" Phase (The Wow)
**Expected Claude Behavior**:
Claude calls `ask_context_layer(question: 'How do I use SagaManager from shared-chassis?')` and reports:
*"The Context Layer reports that `SagaManager` requires an `IdempotencyKey`. The correct call is `execute(saga_id, payload, idempotency_key)`. Here is the correct implementation..."* (Claude writes the code perfectly on the first try).

---

## 🏁 Wrap Up
Tell the client: *"Context Layer doesn't just make the AI smarter—it makes your entire company's codebase legible to the AI."*
