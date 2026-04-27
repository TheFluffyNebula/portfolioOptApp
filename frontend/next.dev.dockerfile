FROM node:18-alpine
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

ENV NODE_ENV=development
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
# Enable polling so Next.js detects synced files inside the container
ENV WATCHPACK_POLLING=true

EXPOSE 3000
CMD ["npm", "run", "dev"]
