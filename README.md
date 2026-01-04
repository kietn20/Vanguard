# Project Vanguard

> An autonomous, event-driven multi-agent system for industrial factory orchestration

## Overview

Vanguard is a production-grade system that combines AI agents (Python/LangGraph) with high-performance microservices (Java/Spring Boot) to autonomously manage factory operations through real-time event processing.

## Architecture
```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Factory        │         │   AI Brain       │         │   Java          │
│  Simulator      │────────▶│   (LangGraph)    │────────▶│   Services      │
│  (Python)       │  Kafka  │   Agents         │   MCP   │   (Spring Boot) │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                                                    │
                                                                    ▼
                                                          ┌─────────────────┐
                                                          │   PostgreSQL    │
                                                          │   (State Store) │
                                                          └─────────────────┘
```
