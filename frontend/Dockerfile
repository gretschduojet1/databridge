FROM node:20-alpine

WORKDIR /app

# Install dependencies before copying source so this layer is cached
# and npm install only re-runs when package.json changes
COPY package.json .
RUN npm install

COPY . .

CMD ["npm", "run", "dev"]
