# ==============================
# 前端 Dockerfile（frontend/）
# 多阶段构建：build → nginx 静态服务
# ==============================

# ---- Stage 1: 构建 ----
FROM node:20-alpine AS builder

WORKDIR /app

# 先复制依赖文件，利用缓存
COPY package.json package-lock.json* ./
RUN npm install

# 复制全部前端源码
COPY . .

# 生产构建
RUN npm run build

# ---- Stage 2: Nginx 托管静态文件 ----
FROM nginx:alpine

# 删除默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 使用项目自己的 nginx.conf
COPY nginx.conf /etc/nginx/conf.d/app.conf

# 把构建产物复制到 nginx 根目录
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
