FROM node:22-alpine AS builder

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

# Copy only the files needed for dependency installation and build.
COPY package.json package-lock.json turbo.json tsconfig.json ./
COPY apps/web/package.json ./apps/web/package.json

# Install all workspace dependencies, then build only the Next.js app.
RUN npm ci
COPY apps/web ./apps/web
RUN npm run build:internal --workspace=apps/web

FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Keep runtime image smaller by copying only what is needed to run the web app.
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/apps/web ./apps/web

WORKDIR /app/apps/web

EXPOSE 3000

CMD ["npm", "run", "start"]