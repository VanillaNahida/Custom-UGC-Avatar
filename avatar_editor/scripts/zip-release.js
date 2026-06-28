import { readFileSync, existsSync } from 'fs'
import { execSync } from 'child_process'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const rootDir = join(__dirname, '..')

const pkg = JSON.parse(readFileSync(join(rootDir, 'package.json'), 'utf-8'))
const version = pkg.version
const zipName = `Avatar Editor 头像编辑器_v${version}.zip`

const sourceDir = join(rootDir, 'release', 'win-unpacked')
const destPath = join(rootDir, 'release', zipName)

if (!existsSync(sourceDir)) {
  console.error(`错误: 未找到构建产物目录 ${sourceDir}`)
  console.error('请先运行 build:win 构建项目')
  process.exit(1)
}

console.log(`正在打包: ${zipName}`)
const cmd = `7z a -tzip "${destPath}" "${sourceDir}\\*"`
execSync(cmd)
console.log(`打包完成: release/${zipName}`)
