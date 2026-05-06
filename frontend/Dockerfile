# Development stage
FROM node:20-alpine as development
WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ENV VITE_POLL=1000
ENV NODE_ENV=development

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Production stage
FROM node:20-alpine as production
WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

FROM node:20-alpine
WORKDIR /app

RUN npm install -g serve

COPY --from=production /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
