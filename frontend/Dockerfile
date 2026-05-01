FROM node:20-alpine AS build

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend .

ARG VITE_API_BASE=/api
ARG VITE_ALLOW_INSECURE_DEV=false
ENV VITE_API_BASE=${VITE_API_BASE}
ENV VITE_ALLOW_INSECURE_DEV=${VITE_ALLOW_INSECURE_DEV}
RUN npm run build

FROM nginx:1.27-alpine AS runtime

ARG BACKEND_UPSTREAM=http://backend:8000
ENV BACKEND_UPSTREAM=${BACKEND_UPSTREAM}

COPY frontend/nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
