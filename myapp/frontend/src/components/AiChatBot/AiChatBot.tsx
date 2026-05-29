// ==== AiChatBot 组件 ====
// 全局悬浮 AI 机器人入口：右下角触发按钮 + iframe 聊天面板
// 启动时请求 /myapp/navbar_bottom 接口，返回空数组则不显示任何内容

import React, { useState, useRef, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { getNavbarBottom } from '../../api/kubeflowApi'
import { INavbarBottomItem } from '../../api/interface/kubeflowInterface'
import './AiChatBot.less'

const resolveIframeUrl = (url: string) => {
  const rawUrl = url.trim()

  if (!rawUrl || typeof window === 'undefined') return rawUrl

  const { protocol, hostname, origin } = window.location

  if (/^\/\//.test(rawUrl)) {
    return rawUrl.replace(/^\/\/(?=:)/, `//${hostname}`).replace(/^\/\//, `${protocol}//`)
  }

  if (/^[a-z][a-z\d+.-]*:\/\/(?=:)/i.test(rawUrl)) {
    return rawUrl.replace(/^([a-z][a-z\d+.-]*:\/\/)(?=:)/i, `$1${hostname}`)
  }

  if (/^:\d+/.test(rawUrl)) {
    return `${protocol}//${hostname}${rawUrl}`
  }

  try {
    return new URL(rawUrl, origin).toString()
  } catch {
    return rawUrl
  }
}

// ==== Section: 主组件 ====

// AiChatBot 悬浮聊天机器人组件（无 props，全局单例挂载在 App 最底部）
type DragTarget = 'button' | 'panel'

interface Position {
  left: number
  top: number
}

interface DragState {
  target: DragTarget
  pointerId: number
  startX: number
  startY: number
  startLeft: number
  startTop: number
  moved: boolean
}

const CHATBOT_BUTTON_POSITION_KEY = 'aichatbot-button-position'
const CHATBOT_PANEL_POSITION_KEY = 'aichatbot-panel-position'
const CHATBOT_MARGIN = 12
const CHATBOT_HEADER_OFFSET = 60
const CHATBOT_BUTTON_SIZE = 48
const CHATBOT_PANEL_WIDTH = 520
const CHATBOT_MINIMIZED_HEIGHT = 62

const getViewport = () => ({
  width: typeof window === 'undefined' ? 1440 : window.innerWidth,
  height: typeof window === 'undefined' ? 900 : window.innerHeight,
})

const getPanelSize = (isMinimized: boolean) => {
  const viewport = getViewport()
  return {
    width: Math.min(CHATBOT_PANEL_WIDTH, Math.max(320, viewport.width - CHATBOT_MARGIN * 2)),
    height: isMinimized
      ? CHATBOT_MINIMIZED_HEIGHT
      : Math.max(320, viewport.height - CHATBOT_HEADER_OFFSET - CHATBOT_MARGIN),
  }
}

const clampPosition = (position: Position, size: { width: number; height: number }, minTop = CHATBOT_MARGIN): Position => {
  const viewport = getViewport()
  const maxLeft = Math.max(CHATBOT_MARGIN, viewport.width - size.width - CHATBOT_MARGIN)
  const maxTop = Math.max(minTop, viewport.height - size.height - CHATBOT_MARGIN)
  return {
    left: Math.min(Math.max(position.left, CHATBOT_MARGIN), maxLeft),
    top: Math.min(Math.max(position.top, minTop), maxTop),
  }
}

const readStoredPosition = (key: string, fallback: Position, size: { width: number; height: number }, minTop = CHATBOT_MARGIN) => {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return clampPosition(fallback, size, minTop)
    const parsed = JSON.parse(raw)
    if (typeof parsed?.left !== 'number' || typeof parsed?.top !== 'number') {
      return clampPosition(fallback, size, minTop)
    }
    return clampPosition(parsed, size, minTop)
  } catch {
    return clampPosition(fallback, size, minTop)
  }
}

const saveStoredPosition = (key: string, position: Position) => {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(key, JSON.stringify(position))
  } catch {
    // Ignore storage failures. Dragging should still work for the current session.
  }
}

const getDefaultButtonPosition = () => {
  const viewport = getViewport()
  return clampPosition({
    left: viewport.width - CHATBOT_BUTTON_SIZE - 16,
    top: viewport.height - CHATBOT_BUTTON_SIZE - 82,
  }, { width: CHATBOT_BUTTON_SIZE, height: CHATBOT_BUTTON_SIZE })
}

const getDefaultPanelPosition = () => {
  const size = getPanelSize(false)
  const viewport = getViewport()
  return clampPosition({
    left: viewport.width - size.width - 24,
    top: CHATBOT_HEADER_OFFSET,
  }, size, CHATBOT_HEADER_OFFSET)
}

const AiChatBot: React.FC = () => {
  const location = useLocation()
  // 后端返回的智能助手配置（null 表示尚未加载）
  const [botConfig, setBotConfig] = useState<INavbarBottomItem | null>(null)
  // 面板开关状态
  const [isOpen, setIsOpen] = useState(false)
  // 面板最小化状态（折叠为仅头部）
  const [isMinimized, setIsMinimized] = useState(false)
  // iframe 加载状态：loading | ok | error
  const [iframeStatus, setIframeStatus] = useState<'loading' | 'ok' | 'error'>('loading')
  const [buttonPosition, setButtonPosition] = useState<Position>(() => readStoredPosition(
    CHATBOT_BUTTON_POSITION_KEY,
    getDefaultButtonPosition(),
    { width: CHATBOT_BUTTON_SIZE, height: CHATBOT_BUTTON_SIZE },
  ))
  const [panelPosition, setPanelPosition] = useState<Position>(() => readStoredPosition(
    CHATBOT_PANEL_POSITION_KEY,
    getDefaultPanelPosition(),
    getPanelSize(false),
    CHATBOT_HEADER_OFFSET,
  ))
  const dragState = useRef<DragState | null>(null)
  const suppressNextClick = useRef(false)
  // 用于在重新打开面板时强制重载 iframe
  const iframeKey = useRef(0)

  // 组件挂载时请求底部助手配置；登录页跳过，避免未认证的 axios 请求触发 gotoLogin 死循环
  useEffect(() => {
    if (location.pathname === '/login') return
    getNavbarBottom()
      .then(res => {
        const list = res.data
        // 只取第一个配置项，空数组则保持 null 不渲染
        if (Array.isArray(list) && list.length > 0) {
          setBotConfig(list[0])
        }
      })
      .catch(() => {
        // 接口失败时静默不显示助手入口
      })
  }, [location.pathname])

  // 切换面板开关，关闭时同时重置最小化状态；重新打开时重置 iframe 状态并刷新 key
  useEffect(() => {
    const handleResize = () => {
      setButtonPosition(prev => {
        const next = clampPosition(prev, { width: CHATBOT_BUTTON_SIZE, height: CHATBOT_BUTTON_SIZE })
        saveStoredPosition(CHATBOT_BUTTON_POSITION_KEY, next)
        return next
      })
      setPanelPosition(prev => {
        const next = clampPosition(prev, getPanelSize(isMinimized), CHATBOT_HEADER_OFFSET)
        saveStoredPosition(CHATBOT_PANEL_POSITION_KEY, next)
        return next
      })
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [isMinimized])

  // 开始拖动
  const startDrag = (target: DragTarget, event: React.PointerEvent<HTMLElement>) => {
    if (event.button !== 0) return
    const startPosition = target === 'button' ? buttonPosition : panelPosition
    dragState.current = {
      target,
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      startLeft: startPosition.left,
      startTop: startPosition.top,
      moved: false,
    }
    event.currentTarget.setPointerCapture?.(event.pointerId)
  }

  // 处理拖动移动事件
  const handleDragMove = (event: React.PointerEvent<HTMLElement>) => {
    const drag = dragState.current
    if (!drag || drag.pointerId !== event.pointerId) return

    const deltaX = event.clientX - drag.startX
    const deltaY = event.clientY - drag.startY
    if (Math.abs(deltaX) > 4 || Math.abs(deltaY) > 4) {
      drag.moved = true
      suppressNextClick.current = true
    }

    if (!drag.moved) return

    event.preventDefault()
    const nextPosition = { left: drag.startLeft + deltaX, top: drag.startTop + deltaY }
    if (drag.target === 'button') {
      setButtonPosition(clampPosition(nextPosition, { width: CHATBOT_BUTTON_SIZE, height: CHATBOT_BUTTON_SIZE }))
    } else {
      setPanelPosition(clampPosition(nextPosition, getPanelSize(isMinimized), CHATBOT_HEADER_OFFSET))
    }
  }

  // 结束拖动
  const endDrag = (event: React.PointerEvent<HTMLElement>) => {
    const drag = dragState.current
    if (!drag || drag.pointerId !== event.pointerId) return

    event.currentTarget.releasePointerCapture?.(event.pointerId)
    if (drag.moved) {
      if (drag.target === 'button') {
        setButtonPosition(prev => {
          const next = clampPosition(prev, { width: CHATBOT_BUTTON_SIZE, height: CHATBOT_BUTTON_SIZE })
          saveStoredPosition(CHATBOT_BUTTON_POSITION_KEY, next)
          return next
        })
      } else {
        setPanelPosition(prev => {
          const next = clampPosition(prev, getPanelSize(isMinimized), CHATBOT_HEADER_OFFSET)
          saveStoredPosition(CHATBOT_PANEL_POSITION_KEY, next)
          return next
        })
      }
      window.setTimeout(() => {
        suppressNextClick.current = false
      }, 0)
    }
    dragState.current = null
  }

  // 切换面板开关
  const handleToggleOpen = () => {
    if (suppressNextClick.current) {
      suppressNextClick.current = false
      return
    }
    setIsOpen(prev => {
      if (prev) {
        setIsMinimized(false)
        const panelSize = getPanelSize(isMinimized)
        const nextButtonPosition = clampPosition({
          left: panelPosition.left + panelSize.width - CHATBOT_BUTTON_SIZE,
          top: panelPosition.top + panelSize.height - CHATBOT_BUTTON_SIZE,
        }, { width: CHATBOT_BUTTON_SIZE, height: CHATBOT_BUTTON_SIZE })
        setButtonPosition(nextButtonPosition)
        saveStoredPosition(CHATBOT_BUTTON_POSITION_KEY, nextButtonPosition)
      } else {
        const panelSize = getPanelSize(false)
        const nextPanelPosition = clampPosition({
          left: buttonPosition.left + CHATBOT_BUTTON_SIZE - panelSize.width,
          top: Math.min(buttonPosition.top, getViewport().height - panelSize.height - CHATBOT_MARGIN),
        }, panelSize, CHATBOT_HEADER_OFFSET)
        setPanelPosition(nextPanelPosition)
        saveStoredPosition(CHATBOT_PANEL_POSITION_KEY, nextPanelPosition)
        iframeKey.current += 1
        setIframeStatus('loading')
      }
      return !prev
    })
  }

  // 后端未返回配置（接口返回空数组或尚未加载完成），不渲染任何内容
  if (!botConfig) return null

  const iframeUrl = resolveIframeUrl(botConfig.url || '')

  // ==== Section: 主渲染 ====

  return (
    <>
      {/* ---- 悬浮触发按钮：面板打开后隐藏 ---- */}
      {!isOpen && (
        <button
          className="aichatbot-float-btn"
          style={{ left: buttonPosition.left, top: buttonPosition.top }}
          onPointerDown={(event) => startDrag('button', event)}
          onPointerMove={handleDragMove}
          onPointerUp={endDrag}
          onPointerCancel={endDrag}
          onClick={handleToggleOpen}
          title="AI 助手"
          aria-label="打开 AI 助手"
        >
          {/* 使用后端返回的 SVG 图标 */}
          <span
            className="aichatbot-float-icon"
            dangerouslySetInnerHTML={{ __html: botConfig.icon }}
          />
        </button>
      )}

      {/* ---- 聊天面板（固定右侧，从底部铺到页面上方）---- */}
      {isOpen && (
        <div
          className={`aichatbot-panel${isMinimized ? ' is-minimized' : ''}`}
          style={{
            left: panelPosition.left,
            top: panelPosition.top,
            width: getPanelSize(isMinimized).width,
            height: getPanelSize(isMinimized).height,
          }}
        >
          {/* 头部：图标 + 标题 + 最小化 / 关闭按钮 */}
          <div
            className="aichatbot-header"
            onPointerDown={(event) => startDrag('panel', event)}
            onPointerMove={handleDragMove}
            onPointerUp={endDrag}
            onPointerCancel={endDrag}
          >
            <div
              className="aichatbot-header-avatar"
              dangerouslySetInnerHTML={{ __html: botConfig.icon }}
            />
            <div className="aichatbot-header-info">
              <div className="aichatbot-header-title">AI 运维助手</div>
              <div className="aichatbot-header-status">
                <span className="aichatbot-status-dot" />
                已连接
              </div>
            </div>
            <div className="aichatbot-header-actions">
              {/* 最小化 / 展开切换 */}
              <button
                className="aichatbot-action-btn"
                onPointerDown={(event) => event.stopPropagation()}
                onClick={() => setIsMinimized(v => !v)}
                title={isMinimized ? '展开' : '最小化'}
              >
                {isMinimized ? (
                  <svg width="14" height="14" viewBox="0 0 48 48" fill="none">
                    <path d="M24 10L24 38" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
                    <path d="M12 26L24 38L36 26" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 48 48" fill="none">
                    <path d="M8 24H40" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
                  </svg>
                )}
              </button>
              {/* 关闭按钮 */}
              <button
                className="aichatbot-action-btn"
                onPointerDown={(event) => event.stopPropagation()}
                onClick={handleToggleOpen}
                title="关闭"
              >
                <svg width="14" height="14" viewBox="0 0 48 48" fill="none">
                  <path d="M12 12L36 36" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
                  <path d="M36 12L12 36" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          </div>

          {/* AI 对话区域，占据头部以下的全部剩余空间 */}
          {!isMinimized && (
            <div className="aichatbot-body">
              {/* URL 为空时直接展示占位提示 */}
              {!iframeUrl ? (
                <div className="aichatbot-placeholder">
                  <span className="aichatbot-placeholder-icon">🤖</span>
                  <div className="aichatbot-placeholder-text">未配置对话地址</div>
                  <div className="aichatbot-placeholder-hint">
                    请在后端配置 AI_ASSISTANT_URL
                  </div>
                </div>
              ) : (
                <>
                  {/* 加载中蒙层，iframe 加载完成后隐藏 */}
                  {iframeStatus === 'loading' && (
                    <div className="aichatbot-loading">
                      <div className="aichatbot-loading-spinner" />
                      <div className="aichatbot-loading-text">连接中…</div>
                    </div>
                  )}
                  {/* 连接失败时展示错误提示，支持手动重试 */}
                  {iframeStatus === 'error' && (
                    <div className="aichatbot-placeholder">
                      <span className="aichatbot-placeholder-icon">⚠️</span>
                      <div className="aichatbot-placeholder-text">服务连接失败</div>
                      <div className="aichatbot-placeholder-hint">
                        无法访问 AI 服务，请检查网络或联系管理员
                      </div>
                      <button
                        className="aichatbot-retry-btn"
                        onClick={() => {
                          iframeKey.current += 1
                          setIframeStatus('loading')
                        }}
                      >
                        重试
                      </button>
                    </div>
                  )}
                  <iframe
                    key={iframeKey.current}
                    className="aichatbot-iframe"
                    src={iframeUrl}
                    title="AI 助手"
                    frameBorder={0}
                    allow="microphone"
                    onLoad={() => {
                      try {
                        setIframeStatus('ok')
                      } catch {
                        setIframeStatus('error')
                      }
                    }}
                    style={{ display: iframeStatus === 'ok' ? 'block' : 'none' }}
                  />
                </>
              )}
            </div>
          )}
        </div>
      )}
    </>
  )
}

export default AiChatBot
