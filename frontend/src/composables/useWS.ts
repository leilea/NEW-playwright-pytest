import { ref, onUnmounted, watch } from 'vue'

export interface UseWSOptions {
  onMessage: (text: string) => void
  onOpen?: () => void
  onClose?: (code: number) => void
  reconnectMs?: number
}

export function useWS(url: () => string | null, opts: UseWSOptions) {
  const connected = ref(false)
  const error = ref<string | null>(null)
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let stopped = false

  function connect() {
    const u = url()
    if (!u || stopped) return
    if (ws && ws.readyState === WebSocket.OPEN) return
    ws = new WebSocket(u)
    ws.onopen = () => {
      connected.value = true
      error.value = null
      opts.onOpen?.()
    }
    ws.onmessage = (e) => opts.onMessage(e.data)
    ws.onclose = (e) => {
      connected.value = false
      opts.onClose?.(e.code)
      if (!stopped) {
        reconnectTimer = setTimeout(connect, opts.reconnectMs ?? 3000)
      }
    }
    ws.onerror = () => { error.value = 'WebSocket error'; ws?.close() }
  }

  function send(text: string) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(text)
  }

  function close() {
    stopped = true
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws?.close()
  }

  onUnmounted(close)

  return { connected, error, connect, send, close }
}
