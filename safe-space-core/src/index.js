/**
 * Safe Space Core — Sovereign Social Hub (v4.0)
 * Codex §4.1: GraphQL API for posts, comments, communities, DMs.
 * All user actions emit telemetry to Palantir Lake (Codex §5.1).
 */
const express = require('express');
const { ApolloServer, gql } = require('apollo-server-express');
const crypto = require('crypto');

// ---------------------------------------------------------------------------
// Telemetry (Palantir Mandate — Codex §5.1)
// ---------------------------------------------------------------------------
function emitTelemetry(eventType, payload) {
  const envelope = {
    source: 'safe-space-core',
    event_type: eventType,
    timestamp: new Date().toISOString(),
    data: payload,
    verification_status: 'PENDING_MERKLE_HASH',
  };
  // In production: send to Kafka bronze_raw_ingress topic
  console.log('[Telemetry]', JSON.stringify(envelope));
}

// ---------------------------------------------------------------------------
// In-memory data store (replace with PostgreSQL in production)
// ---------------------------------------------------------------------------
const users = new Map();
const posts = new Map();
const communities = new Map();
let postIdCounter = 1;

// Seed data
users.set('1', { id: '1', username: 'SovereignCitizen', displayName: 'Sovereign Citizen', is_verified: true, bio: 'Builder.', createdAt: new Date().toISOString() });
communities.set('1', { id: '1', name: 'Main Hub', description: 'The central Safe Space community.', memberCount: 1, createdAt: new Date().toISOString() });

// ---------------------------------------------------------------------------
// GraphQL Schema
// ---------------------------------------------------------------------------
const typeDefs = gql`
  type User {
    id: ID!
    username: String!
    displayName: String
    is_verified: Boolean!
    bio: String
    createdAt: String
  }

  type Post {
    id: ID!
    author: User!
    content: String!
    communityId: String
    likes: Int!
    comments: [Comment!]
    contentHash: String!
    createdAt: String!
  }

  type Comment {
    id: ID!
    author: User!
    content: String!
    createdAt: String!
  }

  type Community {
    id: ID!
    name: String!
    description: String
    memberCount: Int!
    createdAt: String
  }

  type Query {
    getUser(id: ID!): User
    getFeed(limit: Int): [Post!]!
    getPost(id: ID!): Post
    getCommunity(id: ID!): Community
    listCommunities: [Community!]!
  }

  type Mutation {
    createPost(content: String!, communityId: String): Post!
    likePost(id: ID!): Post
    addComment(postId: ID!, content: String!): Post
  }
`;

// ---------------------------------------------------------------------------
// Resolvers
// ---------------------------------------------------------------------------
const resolvers = {
  Query: {
    getUser: (_, { id }) => users.get(id) || null,

    getFeed: (_, { limit = 20 }) => {
      const allPosts = Array.from(posts.values())
        .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
        .slice(0, limit);
      emitTelemetry('feed_viewed', { limit, resultCount: allPosts.length });
      return allPosts;
    },

    getPost: (_, { id }) => posts.get(id) || null,
    getCommunity: (_, { id }) => communities.get(id) || null,
    listCommunities: () => Array.from(communities.values()),
  },

  Mutation: {
    createPost: (_, { content, communityId }) => {
      const id = String(postIdCounter++);
      const contentHash = crypto.createHash('sha512').update(content).digest('hex');
      const post = {
        id,
        author: users.get('1'),
        content,
        communityId: communityId || '1',
        likes: 0,
        comments: [],
        contentHash,
        createdAt: new Date().toISOString(),
      };
      posts.set(id, post);

      emitTelemetry('post_created', {
        postId: id,
        communityId: post.communityId,
        contentHash,
      });

      return post;
    },

    likePost: (_, { id }) => {
      const post = posts.get(id);
      if (!post) return null;
      post.likes += 1;
      emitTelemetry('post_liked', { postId: id, totalLikes: post.likes });
      return post;
    },

    addComment: (_, { postId, content }) => {
      const post = posts.get(postId);
      if (!post) return null;
      const comment = {
        id: String(Date.now()),
        author: users.get('1'),
        content,
        createdAt: new Date().toISOString(),
      };
      post.comments.push(comment);
      emitTelemetry('comment_added', { postId, commentId: comment.id });
      return post;
    },
  },
};

// ---------------------------------------------------------------------------
// Server
// ---------------------------------------------------------------------------
async function startServer() {
  const app = express();

  // Health check (Codex §5.4)
  app.get('/health', (_, res) => {
    res.json({ status: 'online', service: 'safe-space-core', version: '4.0.0' });
  });

  const server = new ApolloServer({ typeDefs, resolvers });
  await server.start();
  server.applyMiddleware({ app });

  const PORT = process.env.PORT || 4000;
  app.listen({ port: PORT }, () =>
    console.log(`[Safe Space] GraphQL Server ready at http://localhost:${PORT}${server.graphqlPath}`)
  );
}

startServer();
