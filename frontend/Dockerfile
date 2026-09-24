FROM node:20-alpine

WORKDIR /app

# We mount volume at runtime for fast dev, but we can copy package.json first
COPY package.json ./

RUN npm install

COPY . .

EXPOSE 8502

CMD ["npm", "run", "dev", "--", "--host"]
