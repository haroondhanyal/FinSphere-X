FROM node:22-alpine AS deps
WORKDIR /repo
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN corepack enable && corepack prepare pnpm@10.15.1 --activate && corepack pnpm install --frozen-lockfile

FROM node:22-alpine AS builder
WORKDIR /repo
COPY --from=deps /repo/node_modules ./node_modules
COPY --from=deps /repo/apps/web/node_modules ./apps/web/node_modules
COPY . .
RUN corepack enable && corepack pnpm build:web

FROM node:22-alpine AS runner
WORKDIR /repo
ENV NODE_ENV=production
COPY --from=builder /repo /repo
EXPOSE 3000
CMD ["corepack", "pnpm", "--filter", "@finsphere/web", "start"]
