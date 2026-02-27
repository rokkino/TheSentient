/**
 * Helper per API e WebSocket in base all'ambiente.
 * - Dev: /api e ws(s)://currentHost/ws (proxy Vite)
 * - Prod: VITE_API_URL assoluto e wss derivato per /api/ws (Nginx)
 */

/**
 * Base URL per le chiamate API (già usata da api.js).
 * In dev: /api (proxy Vite). In prod: https://thesentient.duckdns.org/api
 */
export function getApiBase() {
  return import.meta.env.VITE_API_URL || '/api'
}

/**
 * URL base per le richieste assolute (es. immagini profilo).
 * Se VITE_API_URL è assoluto lo restituisce; altrimenti origin + /api.
 */
export function getApiBaseAbsolute() {
  const base = getApiBase()
  if (base.startsWith('http://') || base.startsWith('https://')) return base
  if (typeof window !== 'undefined' && window.location) {
    return window.location.origin + (base.startsWith('/') ? base : '/' + base)
  }
  return base
}

/**
 * URL WebSocket: ws o wss in base al protocollo, senza hardcodare host.
 * - Produzione (VITE_API_URL assoluto): wss://thesentient.duckdns.org/api/ws (Nginx)
 * - Sviluppo: ws(s)://currentHost/ws (proxy Vite → backend :8000/ws)
 */
export function getWsBase() {
  const apiUrl = import.meta.env.VITE_API_URL
  if (apiUrl && (apiUrl.startsWith('http://') || apiUrl.startsWith('https://'))) {
    const u = new URL(apiUrl)
    const protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${u.host}/api/ws`
  }
  if (typeof window !== 'undefined' && window.location) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/ws`
  }
  return 'ws://localhost:5173/ws'
}
