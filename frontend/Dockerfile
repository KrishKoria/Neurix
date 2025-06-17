FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN npm install -g pnpm
RUN pnpm install

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Start development server
CMD ["pnpm", "dev", "--host", "0.0.0.0"]