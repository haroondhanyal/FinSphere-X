# syntax=docker/dockerfile:1.7
FROM node:22-alpine AS deps
WORKDIR /repo
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN --mount=type=cache,id=finspherex-pnpm-store,target=/root/.local/share/pnpm/store \
    corepack enable && corepack prepare pnpm@10.15.1 --activate && \
    corepack pnpm install --frozen-lockfile --fetch-retries=5 --fetch-timeout=120000

FROM node:22-alpine AS builder
WORKDIR /repo
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
COPY --from=deps /repo/node_modules ./node_modules
COPY --from=deps /repo/apps/web/node_modules ./apps/web/node_modules
COPY . .
RUN corepack enable && corepack pnpm build:web

FROM node:22-alpine AS runner
WORKDIR /repo
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000
RUN addgroup --system --gid 10001 app && adduser --system --uid 10001 --ingroup app app
COPY --from=builder --chown=10001:10001 /repo/apps/web/.next/standalone ./
COPY --from=builder --chown=10001:10001 /repo/apps/web/.next/static ./apps/web/.next/static
USER 10001:10001
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
