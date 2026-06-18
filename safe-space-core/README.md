# Safe Space Core

> **Codex Reference:** §4.1 — Sovereign Social Hub

The community-driven social platform. No algorithms. No ads. Just truth.

## Features
- **Posts & Feed:** Create, like, and comment on posts
- **Communities:** Topic-based community hubs
- **Content Integrity:** Every post is SHA-512 hashed for tamper detection
- **Palantir Telemetry:** All user actions emit events to the data lake

## API (GraphQL)

| Operation | Type | Description |
|---|---|---|
| `getUser(id)` | Query | Fetch a user profile |
| `getFeed(limit)` | Query | Get the latest posts |
| `getPost(id)` | Query | Get a specific post |
| `listCommunities` | Query | List all communities |
| `createPost(content)` | Mutation | Create a new post |
| `likePost(id)` | Mutation | Like a post |
| `addComment(postId, content)` | Mutation | Comment on a post |

## Tech Stack
- **Language:** Node.js
- **Framework:** Express + Apollo GraphQL
- **Port:** 4000
