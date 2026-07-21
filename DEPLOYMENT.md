# 部署说明

这个项目是 Flask 动态应用，完整功能上线需要支持 Python 后端的平台。

## 推荐：Render

1. 把项目推送到 GitHub。
2. 在 Render 新建 Web Service，选择该仓库。
3. Render 会读取 `render.yaml`。
4. 在 Render 环境变量里填入：
   - `LLM_PROVIDER`
   - `LLM_API_KEY`
   - `LLM_BASE_URL`
   - `LLM_MODEL`
   - 可选：`BROKER_ENABLED`、`BROKER_PROVIDER`、`BROKER_API_URL`、`BROKER_API_KEY`
5. 部署完成后访问 `/analysis`。

## Railway

Railway 可使用 `Procfile` 启动：

```text
waitress-serve --host=0.0.0.0 --port=$PORT wsgi:app
```

环境变量同 Render。

## Fly.io / 云服务器

可以使用 `Dockerfile` 构建部署。服务监听端口由环境变量 `PORT` 控制，默认 `5001`。

## 注意

- 不要上传 `.env`，里面有密钥。
- 生产环境必须配置 `FLASK_SECRET_KEY`，Render 会自动生成。
- `data/`、`reports/`、`logs/` 属于运行时目录，不应提交到代码仓库。
