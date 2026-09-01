# ---------- Stage 1: build the React bundle ----------
FROM node:20-alpine AS build

WORKDIR /app

# Cache-friendly dependency install
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .

# Same-origin API: leave REACT_APP_BACKEND_URL empty so requests go to /api on this host
ARG REACT_APP_BACKEND_URL=""
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN yarn build

# ---------- Stage 2: nginx serves the static build + proxies /api ----------
FROM nginx:1.27-alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
