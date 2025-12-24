# FinMentor

FinMentor is a **financial education engine** designed to help college students and young adults learn personal finance concepts clearly, safely, and affordably.

It focuses on **teaching understanding**, not giving personalized financial advice.

---

## What FinMentor Is (and Is Not)

### ✅ What it is
- A **system-level educational engine** for personal finance
- Built around **structured financial knowledge**, not free-form prompts
- Designed with **explicit guardrails** to prevent unsafe or misleading outputs
- Capable of explaining concepts, assessing understanding, and adapting difficulty
- Architected for future use across multiple products (web, API, extensions)

### ❌ What it is not
- A chatbot wrapper around an LLM
- A tool that gives personalized financial advice
- An investment recommendation system
- A frontend-first or UI-driven project

FinMentor prioritizes **correctness, transparency, and safety** over conversational fluency.

---

## Core Principles

1. **Education over advice**  
   FinMentor explains how financial systems work and what tradeoffs exist.  
   It does not tell users what financial decisions to make.

2. **Structured knowledge**  
   All financial content is stored in versioned JSON datasets with defined schemas.

3. **Explicit guardrails**  
   The system enforces boundaries around disallowed queries (e.g. personalized advice).

4. **Reasoning transparency**  
   Responses are generated through a controlled reasoning pipeline, not ad-hoc generation.

5. **Evaluation-first design**  
   Outputs can be tested, validated, and benchmarked for correctness and consistency.

---

## High-Level Architecture

At a high level, FinMentor consists of:

- **Data Layer**  
  Structured financial concepts, questions, and explanations stored in JSON.

- **Domain Layer**  
  Core financial concepts, curriculum logic, and domain rules.

- **Reasoning Layer**  
  Plans explanations, validates outputs, and scores responses.

- **Guardrails Layer**  
  Enforces safety, compliance, and educational framing.

- **Evaluation Layer**  
  Benchmarks correctness and learning quality.

The LLM is treated as a **replaceable component**, not the core of the system.

---

## Repository Structure

