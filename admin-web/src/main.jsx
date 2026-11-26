// Điểm khởi chạy React: gắn ứng dụng vào phần tử root của trang HTML.
// Điểm khởi chạy React: gắn ứng dụng vào phần tử root của trang HTML.
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
