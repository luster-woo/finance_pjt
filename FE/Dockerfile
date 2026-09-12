# 빌드 컨텍스트는 FE/
#   docker build -f FE/Dockerfile -t finfit-frontend ./FE

FROM node:22-slim AS build

WORKDIR /app

# Vite 변수는 빌드 시점에 번들에 박힌다. 런타임 변경 불가.
ARG VITE_API_BASE_URL=/api
ARG VITE_KAKAO_MAP_KEY=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_KAKAO_MAP_KEY=$VITE_KAKAO_MAP_KEY

COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .
RUN npm run build
RUN test -f dist/index.html && grep -q '/assets/' dist/index.html

FROM nginx:1.27-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
