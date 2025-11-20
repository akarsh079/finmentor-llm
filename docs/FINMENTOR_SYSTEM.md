# FinMentor System Design

## 1. What is FinMentor?
A finance education engine for teens/young adults that answers questions using curated financial concepts and a structured question dataset.

## 2. Who is it for?
- High school seniors
- College undergraduates
- STEM majors unfamiliar with finance
- First-time investors 

## 3. What problems does it solve?
- Young adults have zero formal financial education and don’t understand basic concepts like credit scores, taxes, APR, or investing.
- Online financial content (TikTok, Reddit, YouTube) is full of misinformation, hype, and oversimplified “get-rich” advice.
- Beginners don’t know what questions to ask or how financial concepts relate to each other.
- Financial topics feel “too complicated,” leading to avoidance and poor decisions (high-interest debt, no savings, overspending).
- Existing tools either give personalized financial advice (dangerous) or are too advanced for novices.

## 4. What data does it use?

### 4A. Static curated data
FinMentor uses a manually curated JSON file (finmentor_questions_v1.json) as its primary knowledge base. This file contains:
 - Financial literacy categories (e.g., Budgeting & Cash Flow, Credit & Debt, Investing Basics,   Banking & Accounts)
 - Category descriptions defining the scope of each topic
 - Example subtopics that represent common beginner questions
 - A structured list of actual user-facing questions mapped to each category

Data Structure:
Each category entry follows this schema:
{
  "category": "Budgeting & Cash Flow",
  "description": "Understanding income, expenses, savings, and basic money management.",
  "example_topics": ["budgeting methods", "emergency funds", "tracking spending"],
  "questions": [
    "How do I start a budget?",
    "How much should I save?",
    "What is an emergency fund?"
  ]
}

This JSON dataset serves as the single source of truth for:
 - question classification
 - category retrieval
 - structured context fed into the LLM
 - ensuring explanations are beginner-safe and grounded
 - preventing hallucinated or unsafe financial guidance

All MVP logic operates exclusively on this static curated JSON file.

### 4B. Future dynamic data (NOT in MVP)
FinMentor will eventually integrate dynamic, real-time financial data sources to provide up-to-date context and examples. These data sources are not part of the MVP and will be implemented in later versions.

Planned future data sources include:
 - Live stock prices (e.g., AAPL, S&P 500, ETFs)
 - ETF and index fund metadata (expense ratios, holdings, performance history)
 - Savings account APY rates from major banks
 - Credit card APRs and reward structures
 - Inflation and CPI data
 - Tax bracket data by year and filing status
 - Loan and mortgage rate data

These integrations will require:
 - external APIs,
 - validation layers,
 - caching systems,
 - rate-limit handling, and
 - safety filters to prevent misuse.
 
All of this is future-scope and explicitly excluded from the MVP system.

### 4C. Explanation engine
<!-- Say that explanations come from: LLM + curated financial facts from your JSON / future knowledge base. -->

## 5. High-level features (eventual)
<!-- What FinMentor should eventually be able to do. Keep it high-level. -->
- Explain financial concepts
- Answer user questions
- Map questions to categories/topics
- Provide beginner-safe, non-technical explanations
- Avoid giving personalized investment advice
- Avoid hallucinated numbers

## 6. MVP Scope (what you will build NOW)
<!-- This is critical. Nail this. Explicitly list what MVP DOES and DOES NOT do. -->

**MVP DOES:**
- Load JSON categories and questions
- Take a user question as input
- Classify question into a category (simple rules/keywords first)
- Retrieve relevant questions/topics from JSON
- Call an LLM to generate an explanation using that content

**MVP DOES NOT:**
- Use embeddings
- Use vector databases
- Scrape the web
- Train custom models
- Pull live financial data

## 7. Architecture (textual)

**Pipeline:**

User → Query Router → Category Classifier → Content Retriever → LLM Explanation → Output

### 7.1 Components

- **User Interface**
  - Where the user types a question (CLI / simple web UI later).
- **Query Router**
  - Receives raw user question, cleans it, sends to classifier.
- **Category Classifier**
  - Maps question → one (or few) category IDs from your JSON.
- **Content Retriever**
  - Given category ID, pulls relevant questions/answers/notes from JSON.
- **LLM Explanation Engine**
  - Combines user question + retrieved content → final explanation.
- **Output Formatter**
  - Ensures the response is clear, safe, and beginner-friendly.

### 7.2 Data Flow

1. User sends question: `"How do I start a budget as a college freshman?"`
2. Query Router normalizes text (lowercase, strip, etc.).
3. Category Classifier tags it as: `Budgeting & Cash Flow`.
4. Content Retriever grabs relevant entries from your JSON under that category.
5. LLM Explanation Engine uses:
   - user question
   - retrieved curated content
   to generate a clear explanation.
6. Output is returned to UI.
