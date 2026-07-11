/**
 * CrossHub Express Demo API（桩服务）
 *
 * 职责：健康检查与尚未迁移至 Java 的演示接口。
 * 店铺绑定（platform_account）已统一由 Java `/api/platform-accounts` 提供；
 * Vite 代理将 `/api/platform-accounts` 转发至 `:18080`，请勿在此重复实现。
 */
import cors from 'cors'
import express from 'express'

const PORT = process.env.PORT || 3000

const app = express()
app.use(cors())
app.use(express.json())

app.get('/api/health', (_req, res) => {
  res.json({ success: true, message: 'ok' })
})

app.listen(PORT, () => {
  console.log(`CrossHub Express demo API at http://localhost:${PORT}`)
  console.log('Platform accounts: use Java API at /api/platform-accounts (:18080)')
})
