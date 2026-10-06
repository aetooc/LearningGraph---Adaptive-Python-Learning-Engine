FROM node:24-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --no-audit --no-fund
COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "dev"]
