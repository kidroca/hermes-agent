import { PassThrough } from 'node:stream'

import { renderSync } from '@hermes/ink'
import { RECONNECT_BASE_MS, WS_HEARTBEAT_DEAD_MS, WS_HEARTBEAT_INTERVAL_MS } from '@hermes/shared/gateway-client'
import React, { useEffect } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { createGatewayEventHandler } from '../app/createGatewayEventHandler.js'
import { resetOverlayState } from '../app/overlayStore.js'
import { turnController } from '../app/turnController.js'
import { resetTurnState } from '../app/turnStore.js'
import { getUiState, patchUiState, resetUiState } from '../app/uiStore.js'
import { useSessionLifecycle } from '../app/useSessionLifecycle.js'
import type * as Environment from '../config/env.js'
import { GatewayClient } from '../gatewayClient.js'
import type { Msg } from '../types.js'

vi.mock('../lib/parentLog.js', () => ({ recordParentLifecycle: vi.fn() }))
vi.mock('../config/env.js', async importOriginal => ({
  ...await importOriginal<typeof Environment>(), STARTUP_QUERY: 'do not resend', STARTUP_IMAGE: ''
}))

const transcript = [{ role: 'user', text: 'one prompt' }, { role: 'assistant', text: 'saved answer' }]

class DelayedCloseSocket extends EventTarget {
  static instances: DelayedCloseSocket[] = []
  static canonical = false
  readyState = 0
  sent: { id: number; method: string; params: Record<string, unknown> }[] = []
  deferClose = true
  deferResume = false

  constructor(_url: string) {
    super()
    DelayedCloseSocket.instances.push(this)
  }

  send(text: string) {
    const frame = JSON.parse(text)
    this.sent.push(frame)

    if (frame.method === 'gateway.ping' || (frame.method === 'session.resume' && this.deferResume)) { return }
    queueMicrotask(() => {
      if (this.readyState !== 1) { return }
      const result = this.result(frame.method)
      this.dispatchEvent(new MessageEvent('message', { data: JSON.stringify({ jsonrpc: '2.0', id: frame.id, result }) }))
    })
  }

  close() {
    this.readyState = 2

    if (!this.deferClose) { this.finishClose() }
  }

  finishClose() {
    this.readyState = 3
    this.dispatchEvent(Object.assign(new Event('close'), { code: 1006 }))
  }

  open() {
    this.readyState = 1
    this.dispatchEvent(new Event('open'))
    this.dispatchEvent(new MessageEvent('message', { data: JSON.stringify({
      jsonrpc: '2.0', method: 'event', params: { type: 'gateway.ready', payload: {
        heartbeat: true, session_authority: DelayedCloseSocket.canonical
      } }
    }) }))
  }

  private result(method: string) {
    if (method === 'runtime.describe') { return { session_create: { sources: ['tui'], parameters: ['source', 'request_id'] } } }

    if (method === 'config.get') { return { config: { display: { tui_auto_resume_recent: false } } } }

    if (method === 'setup.status') { return { provider_configured: true } }

    if (method === 'session.resume') {
      if (DelayedCloseSocket.canonical) {
        return {
          session_id: 'durable-existing', stored_session_id: 'durable-existing', subscription_id: 'viewer',
          messages: transcript.map(({ role, text }) => ({ role, content: text })), display_messages: transcript,
          authority_epoch: 1, execution_generation: 1, running: false,
          info: { model: 'test', skills: {}, tools: {} }
        }
      }

      return { session_id: 'runtime-existing', stored_session_id: 'durable-existing', messages: transcript, running: false }
    }

    if (method === 'session.create') { return { session_id: 'blank-replacement', stored_session_id: 'blank-replacement' } }

    return {}
  }
}

const mountSession = (gw: GatewayClient) => {
  let lifecycle: ReturnType<typeof useSessionLifecycle>
  let history: Msg[] = transcript as Msg[]

  const setHistoryItems = (update: Msg[] | ((items: Msg[]) => Msg[])) => {
    history = typeof update === 'function' ? update(history) : update
  }

  const rpc = gw.request.bind(gw)

  const Probe = () => {
    const session = useSessionLifecycle({
      colsRef: { current: 80 }, composerActions: { setComposerTokens: vi.fn() } as any,
      gw, panel: vi.fn(), rpc, scrollRef: { current: null }, setHistoryItems,
      setLastUserMsg: vi.fn(), setSessionStartedAt: vi.fn(), setStickyPrompt: vi.fn(),
      setVoiceProcessing: vi.fn(), setVoiceRecording: vi.fn(), sys: vi.fn()
    })

    useEffect(() => { lifecycle = session })

    return null
  }

  const stream = () => Object.assign(new PassThrough(), { columns: 80, isTTY: false, rows: 24 })

  const view = renderSync(React.createElement(Probe), {
    patchConsole: false, stdout: stream() as any, stderr: stream() as any, stdin: stream() as any
  })

  return { api: () => lifecycle!, history: () => history, unmount: () => view.unmount() }
}

describe.each(['legacy', 'canonical'])('%s reconnect preserves the mounted conversation', wire => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.stubEnv('HERMES_TUI_GATEWAY_URL', 'ws://gateway.test/api/ws')
    vi.stubEnv('HERMES_TUI_SIDECAR_URL', '')
    vi.stubEnv('HERMES_TUI_ACTIVE_SESSION_FILE', '')
    vi.stubGlobal('WebSocket', DelayedCloseSocket)
    DelayedCloseSocket.instances = []
    DelayedCloseSocket.canonical = wire === 'canonical'
    resetUiState()
    resetTurnState()
    resetOverlayState()
    turnController.fullReset()
  })

  afterEach(() => {
    turnController.fullReset()
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it.each(['late', 'missing', 'synchronous', 'missed-exit', 'ordinary', 'closing', 'resume-disconnect', 'late-no-poll', 'missing-no-poll'] as const)('preserves the conversation across %s transport replacement', async close => {
    const gw = new GatewayClient()
    const mounted = mountSession(gw)
    const recoverSidRef = { current: null as string | null }
    const submitLiteral = vi.fn()
    const existingSid = wire === 'canonical' ? 'durable-existing' : 'runtime-existing'

    const exits = vi.fn(() => {
      recoverSidRef.current = getUiState().storedSid ?? getUiState().sid
      patchUiState({ gatewayConnected: false })
    })

    gw.on('exit', exits)

    try {
      await vi.advanceTimersByTimeAsync(0)
      // Establish the transport before mounting its ready handler, then attach an existing view.
      gw.start()
      gw.drain()
      const first = DelayedCloseSocket.instances[0]!
      first.open()
      await vi.advanceTimersByTimeAsync(0)
      patchUiState({ sid: existingSid, storedSid: 'durable-existing', gatewayConnected: true })
      const session = mounted.api()

      const onEvent = createGatewayEventHandler({
        gateway: { gw, rpc: gw.request.bind(gw) },
        session: { ...session, STARTUP_RESUME_ID: close === 'missed-exit' ? 'startup-other' : '', colsRef: { current: 80 }, recoverSidRef, setCatalog: vi.fn() },
        composer: { dequeue: vi.fn(), queueEditRef: { current: null }, sendQueued: vi.fn(), setInput: vi.fn() },
        submission: { submitRef: { current: vi.fn() }, submitLiteralRef: { current: submitLiteral } },
        system: { bellOnComplete: false, sys: vi.fn() },
        transcript: { appendMessage: vi.fn(), panel: vi.fn(), setHistoryItems: vi.fn() },
        voice: { setProcessing: vi.fn(), setRecording: vi.fn(), setVoiceEnabled: vi.fn() }
      } as any)

      gw.on('event', onEvent)
      first.deferClose = close !== 'synchronous'

      if (close === 'missed-exit') {
        gw.start()
      } else if (close === 'ordinary') {
        first.finishClose()
      } else if (close === 'closing') {
        first.close()
      } else {
        await vi.advanceTimersByTimeAsync(WS_HEARTBEAT_INTERVAL_MS + WS_HEARTBEAT_DEAD_MS)
      }

      const noPoll = close === 'late-no-poll' || close === 'missing-no-poll'
      const polls = noPoll ? [] : [gw.request('session.list').catch(() => null), gw.request('session.list').catch(() => null)]
      await vi.advanceTimersByTimeAsync(0)

      if (noPoll) {
        expect(exits).toHaveBeenCalledOnce()
        await vi.advanceTimersByTimeAsync(RECONNECT_BASE_MS)
      }

      if (close === 'late' || close === 'late-no-poll') { first.finishClose() }
      const second = DelayedCloseSocket.instances[1]!
      expect(second).toBeDefined()
      second.deferResume = close === 'resume-disconnect'
      second.open()
      await vi.advanceTimersByTimeAsync(0)
      await Promise.all(polls)

      if (close === 'resume-disconnect') {
        expect(second.sent.some(frame => frame.method === 'session.resume')).toBe(true)
        second.finishClose()
      }

      await vi.advanceTimersByTimeAsync(RECONNECT_BASE_MS)

      if (close === 'resume-disconnect') {
        DelayedCloseSocket.instances[2]!.open()
        await vi.advanceTimersByTimeAsync(0)
      }

      expect(getUiState()).toMatchObject({ sid: existingSid, storedSid: 'durable-existing', gatewayConnected: true })
      expect(mounted.history().filter(message => message.role === 'user' || message.role === 'assistant')).toEqual(transcript)
      const requests = DelayedCloseSocket.instances.flatMap(socket => socket.sent)
      expect(requests.filter(frame => frame.method === 'session.resume').map(frame => frame.params.session_id)).toEqual(
        close === 'resume-disconnect' ? ['durable-existing', 'durable-existing'] : ['durable-existing']
      )
      expect(requests.some(frame => frame.method === 'session.create' || frame.method === 'prompt.submit')).toBe(false)
      expect(submitLiteral).not.toHaveBeenCalled()
      expect(DelayedCloseSocket.instances).toHaveLength(close === 'resume-disconnect' ? 3 : 2)
      expect(exits).toHaveBeenCalledTimes(close === 'missed-exit' ? 0 : close === 'resume-disconnect' ? 2 : 1)
    } finally {
      gw.kill()
      mounted.unmount()
    }
  })
})
