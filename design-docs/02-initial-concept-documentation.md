# Aptitude Search — Initial Concept Documentation

## Overview

Aptitude Search is an exploratory project focused on building a multi-stage LLM pipeline for aptitude-driven job search, career targeting, and search strategy generation.

The core idea is to move beyond traditional AI-assisted job search tools that focus primarily on resume optimization or application tracking.

Instead, this project explores the creation of a structured reasoning system that:

1. Interprets a resume and infers an aptitude profile
2. Transforms that profile into a career targeting strategy
3. Generates optimized search strategies and job search queries

The emphasis is on reasoning and transformation rather than simple text generation.

---

# Initial Project Motivation

The project originated from an existing set of LLM prompts representing various stages of a job-search workflow.

One important existing prompt performs analysis of a resume in order to:

* infer broad aptitudes
* identify transferable strengths
* identify adjacent role possibilities
* determine likely fit areas
* support more intelligent job targeting

This led to the realization that the prompt chain itself may represent a reusable system that could eventually be offered to other users.

At the current stage, this is ideation and architectural exploration rather than an immediate commercialization effort.

---

# Architectural Framing

The key architectural insight is that this is not merely a collection of prompts.

It is better understood as a pipeline composed of discrete reasoning stages.

## Proposed Pipeline

### Stage 1 — Resume Interpretation

Input:

* raw resume text

Output:

* structured aptitude profile

Responsibilities:

* infer core skills
* infer secondary skills
* identify domain experience
* identify likely strengths
* identify possible adjacent roles
* infer seniority level
* infer working style tendencies where appropriate

Conceptual role:

* structured profiler

---

### Stage 2 — Job Targeting Strategy

Input:

* aptitude profile

Output:

* job targeting strategy

Responsibilities:

* determine likely target roles
* identify adjacent roles
* identify avoid/mismatch roles
* identify search keyword clusters
* identify suitable company types
* identify appropriate seniority bands

Conceptual role:

* career strategist

---

### Stage 3 — Job Search Query Generation

Input:

* job targeting strategy
* optional constraints

Output:

* search queries and search strategies

Responsibilities:

* generate Boolean search queries
* generate LinkedIn-style search strings
* generate Indeed-style search strings
* produce multiple search variants
* optimize discoverability

Conceptual role:

* search query optimizer

---

# System Wrapper Concept

The long-term framing is a unified orchestration layer:

## User Inputs

* resume text
* optional location preferences
* salary preferences
* remote preferences
* industry preferences
* industry exclusions

## System Outputs

* aptitude profile
* job targeting strategy
* optimized search queries
* recommended next actions

---

# Prompt Engineering Principles

Each prompt/module should follow a standardized structure.

## Suggested Internal Prompt Contract

### ROLE

Defines the system identity and operational responsibility.

### OBJECTIVE

Defines the exact transformation being performed.

### INPUT FORMAT

Defines expected structured inputs.

### OUTPUT FORMAT

Defines structured outputs.

### RULES

Examples:

* no extra commentary
* structured output only
* JSON-like formatting
* optimized for downstream consumption

---

# Productization-Oriented Features

Even at the experimental stage, several features were identified as valuable.

## Explainability

Each stage should provide concise reasoning summaries explaining why conclusions were reached.

Not chain-of-thought.

Rather:

* lightweight justification
* user-facing rationale
* transparency signals

---

## Confidence Signaling

Potential fields:

* high-confidence skills
* low-confidence inferences
* uncertain role mappings

This helps distinguish:

* explicit evidence
* inferred evidence

---

## Iteration Hooks

The system should support correction loops.

Example:

* user clarifies strengths
* user corrects inferred preferences
* system regenerates downstream strategy

This creates a more adaptive workflow.

---

# Comparison with Existing Tools

A comparison was performed against Careerflow.ai.

## Observations About Careerflow.ai

Careerflow.ai appears to focus primarily on:

* resume optimization
* ATS scoring
* LinkedIn optimization
* job tracking
* application management
* AI-assisted resume rewriting
* application workflow organization

Architecturally, Careerflow.ai resembles:

* a CRM/job-tracking system
* with AI features embedded into workflow touchpoints

Its AI functionality appears primarily reactive.

---

# Identified Difference in Direction

The Aptitude Search concept differs in several important ways.

## Focus on Reasoning

Rather than optimizing applications directly, the system aims to optimize:

* career targeting
* role selection
* search strategy
* role adjacency analysis
* aptitude inference

The proposed system therefore operates earlier in the job-search decision funnel.

---

# Core Conceptual Distinction

Careerflow.ai:

* helps users execute job applications more efficiently

Aptitude Search:

* attempts to help users decide what they should target in the first place

This distinction was identified as strategically important.

---

# Initial Monetization Exploration

Several low-friction monetization approaches were discussed.

## Potential Monetization Models

### Prompt Workflow Pack

Package the prompts and workflows directly.

Possible delivery:

* downloadable prompt pack
* Gumroad/Lemon Squeezy distribution

---

### Interactive Notion Template

Provide:

* guided workflow
* structured prompt execution
* examples
* step-by-step usage

---

### Lightweight Web Application

Potential architecture:

* lightweight frontend
* optional user-configured API key model
* serverless execution

---

### Pay-Per-Use Tool

Instead of subscriptions:

* charge per search session
* charge for bundled executions

---

### Browser Extension

Potential future direction:

* integrate directly into LinkedIn or job board workflows
* perform fit analysis inline

---

# Strategic Insight

A major insight from the discussion:

The value may not ultimately be the prompts themselves.

The more important asset may be:

* structured transformation logic
* reasoning orchestration
* aptitude modeling
* search strategy synthesis

---

# Repository Naming Discussion

The following repository naming directions were explored:

* careerflow
* rolemap
* role-pipeline
* career-lab
* llm-career-pipeline
* aptitude-search

Final selected repository name:

# aptitude-search

Reasons:

* accurately reflects the core differentiator
* aptitude-driven search
* technically descriptive
* broad enough for future evolution
* avoids over-branding

---

# Repository Description

Current short description:

> A multi-stage LLM pipeline for aptitude-driven job search, career targeting, and search strategy generation.

---

# Licensing Position

The current repository status:

* private repository
* no open-source license

Rationale:

* exploratory phase
* architecture still forming
* prompts and orchestration may represent core IP
* desire to maintain a hands-off stance regarding reuse at the current stage

Current recommendation:

* retain private repo status
* defer licensing decisions until project direction stabilizes

---

# Current Strategic Direction

The current goal is not to build:

* a job board clone
* a resume rewriting tool
* a CRUD-heavy application tracker

Instead, the project direction is:

> a modular reasoning pipeline for aptitude-driven career targeting and job-search strategy generation

---

# Immediate Next Steps

Potential near-term tasks:

1. Create initial repository structure
2. Formalize schemas for pipeline stages
3. Convert existing prompts into modular prompt contracts
4. Define intermediate data structures
5. Establish versioned pipeline architecture
6. Create lightweight orchestration layer
7. Prototype iterative feedback loops

---

# Status

Current status:

* exploratory architecture phase
* ideation active
* no commitment to immediate full-scale development
* emphasis on thoughtful iteration rather than rapid uncontrolled expansion

