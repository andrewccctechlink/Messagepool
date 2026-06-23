# Quattro Message Pool — User Guide

## 一、安裝（只需做一次）

### 你需要：
1. **Python** — 下載安裝 [python.org](https://python.org)（安裝時勾選 "Add to PATH"）
2. **Message Pool 檔案** — 解壓 zip 到任何位置（例如 `C:\MessagePool\`）

### 首次啟動：
1. 雙擊 `start.bat`
2. 等待安裝 dependencies（首次約 1-2 分鐘）
3. 瀏覽器自動打開 `http://localhost:8080`
4. 進入 **Settings** 頁面，貼入你嘅 Gemini API Key
   - 免費取得：https://aistudio.google.com/apikey

---

## 二、日常使用

### 方法 1：Watch Folder 自動匯入（最推薦！）

1. 啟動 Message Pool 後，Dashboard 會顯示 Watch Folder 路徑
2. 預設路徑：程式所在位置下嘅 `watch/` 資料夾
3. **從 Outlook 選中 email → 直接拖到 Watch Folder**
4. 程式每 3 秒自動檢查，自動分析，結果即時出現
5. 唔使打開瀏覽器做任何操作！

> 建議：將 Watch Folder 釘到 Windows 快速存取（Quick Access），方便隨時拖入

### 方法 2：瀏覽器拖拽檔案

1. 打開 Message Pool（雙擊 `start.bat`）
2. 瀏覽器顯示主界面
3. Click「Analyze」頁面
4. **直接將檔案拖入虛線框**

支援格式：
| 格式 | 說明 |
|------|------|
| .msg | Outlook 郵件（含附件） |
| .eml | Gmail/其他郵件（含附件） |
| .pdf | PDF 文件 |
| .xlsx / .xls | Excel 表格 |
| .pptx | PowerPoint |
| .docx | Word 文件 |
| .jpg / .png | 圖片 / 截圖 |
| .csv / .txt | 文字檔案 |

> **可以一次拖入多個檔案**（例如 3 封 email 一齊分析）

### 方法 2：貼上文字

1. 複製 WhatsApp / WeChat / Email 內容
2. 貼入「Paste text」文字框
3. 揀 Source Type（WhatsApp / WeChat / Email / Document）
4. Click「Analyze with AI」

---

## 三、Email 專用流程

### Outlook（電腦版）→ Message Pool

1. 打開 Outlook
2. **將 email 從 Outlook 拖到桌面**（自動產生 .msg 檔案）
3. 將 .msg 檔案拖入 Message Pool 瀏覽器窗口
4. AI 自動讀取 email 內文 + 所有附件（PDF/Excel/圖片）

### Gmail → Message Pool

1. 打開 Gmail，打開目標 email
2. Click 右上角 ⋮ →「下載郵件」（產生 .eml 檔案）
3. 將 .eml 檔案拖入 Message Pool

### 多封 Email 一齊分析

1. 從 Outlook 選中多封 email → 拖到桌面（每封變一個 .msg）
2. 全選所有 .msg → 一齊拖入 Message Pool
3. AI 一次過分析所有 email + 附件

---

## 四、外出手機使用（iPhone / Android）

### 設置自動收信（首次）：
1. 打開 Settings 頁面
2. 填入 IMAP 設定：
   - Server: `imap.gmail.com`（Gmail）或 `outlook.office365.com`（Outlook 365）
   - Port: `993`
   - Email: 你嘅專用 pool email 地址
   - Password: App 專用密碼（Gmail 需要 App Password）
3. 揀輪詢頻率（建議每 5 分鐘）
4. Click「Save Settings」

### 日常使用：
1. 喺 iPhone 收到 WhatsApp 報價
2. 截圖 → Share → Email → 發送到 pool email 地址
3. 收到 PDF/Excel 附件 → Forward 到 pool email
4. **唔使做任何其他嘢**
5. Message Pool 自動每 5 分鐘檢查收件箱
6. 回到電腦打開 Message Pool → 所有報價已分析好

---

## 五、搜索報價

1. Click「Search」頁面
2. 輸入搜索（支援自然語言）：
   - `air fryer under USD20`（價格低於 USD20 嘅氣炸鍋）
   - `vendor Kitchen Master`（供應商名稱）
   - `toaster between 10 and 30 USD`（價格範圍）
   - `kettle`（產品名稱）
3. 結果顯示：產品、價格、貨幣、供應商、MOQ、來源、**日期**

---

## 六、數據安全

- ✅ 所有報價數據存在你自己電腦（`data/` 資料夾）
- ✅ 冇任何人可以睇到你嘅資料
- ✅ AI 分析只係將文字發送到 Google Gemini API（一次性處理，唔保留）
- ✅ 關閉軟件後數據不會消失
- ✅ 重開軟件所有歷史記錄仍然存在

---

## 七、常見問題

**Q: 關閉軟件後數據會消失嗎？**
A: 不會。數據永久儲存在 `data/message_pool.db`。重開後所有歷史仍在。

**Q: 可以多個同事一齊用嗎？**
A: 單機版每人獨立安裝。如需共享，可部署到公司伺服器（所有人用瀏覽器打開同一地址）。

**Q: API Key 會唔會被人偷？**
A: Key 只存在你電腦本地嘅 `config.json`，唔會上傳到任何地方。

**Q: 圖片（截圖）都可以辨識？**
A: 是。iPhone 截圖、WhatsApp 截圖、拍攝嘅報價單照片，AI Vision 都可以提取文字同價格。

---

## 八、技術支援

如遇到問題，請聯絡 Quattro Dynamics 技術支援。
# force rebuild Tue Jun 23 15:47:03 UTC 2026
