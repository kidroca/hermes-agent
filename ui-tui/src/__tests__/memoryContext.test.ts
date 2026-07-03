import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createGatewayEventHandler } from '../app/createGatewayEventHandler.js'
import { turnController } from '../app/turnController.js'
import { getTurnState, resetTurnState } from '../app/turnStore.js'
import { patchUiState, resetUiState } from '../app/uiStore.js'
import type { Msg } from '../types.js'

const ref = <T>(current: T) => ({ current })

const buildCtx = (appended: Msg[]) =>
  ({
    composer: {
      dequeue: () => undefined,
      queueEditRef: ref<null | number>(null),
      sendQueued: vi.fn(),
      setInput: vi.fn()
    },
    gateway: {
      gw: { request: vi.fn() },
      rpc: vi.fn(async () => null)
    },
    session: {
      STARTUP_RESUME_ID: '',
      colsRef: ref(80),
      newSession: vi.fn(),
      resetSession: vi.fn(),
      resumeById: vi.fn(),
      setCatalog: vi.fn()
    },
    submission: {
      submitRef: { current: vi.fn() }
    },
    system: {
      bellOnComplete: false,
      sys: vi.fn()
    },
    transcript: {
      appendMessage: (msg: Msg) => appended.push(msg),
      panel: vi.fn(),
      setHistoryItems: vi.fn()
    },
    voice: {
      setProcessing: vi.fn(),
      setRecording: vi.fn(),
      setVoiceEnabled: vi.fn()
    }
  }) as any

describe('TUI memory recall context events', () => {
  beforeEach(() => {
    resetUiState()
    resetTurnState()
    turnController.fullReset()
    patchUiState({ showReasoning: true })
  })

  it('attaches memory recall context to the completed assistant message', () => {
    const appended: Msg[] = []
    const onEvent = createGatewayEventHandler(buildCtx(appended))

    onEvent({
      payload: { memory_context: '## Hindsight\nPeter likes compact output.', text: 'final answer' },
      type: 'message.complete'
    } as any)

    expect(appended).toHaveLength(1)
    expect(appended[0]).toMatchObject({
      memoryContext: '## Hindsight\nPeter likes compact output.',
      role: 'assistant',
      text: 'final answer'
    })
  })

  it('attaches memory recall context to an already-streamed final assistant segment', () => {
    const appended: Msg[] = []
    const onEvent = createGatewayEventHandler(buildCtx(appended))

    onEvent({ payload: { text: 'streamed final answer' }, type: 'message.delta' } as any)
    turnController.flushStreamingSegment()
    onEvent({
      payload: { memory_context: '## Hindsight\nstreamed context', text: 'streamed final answer' },
      type: 'message.complete'
    } as any)

    expect(appended).toHaveLength(1)
    expect(appended[0]).toMatchObject({
      memoryContext: '## Hindsight\nstreamed context',
      role: 'assistant',
      text: 'streamed final answer'
    })
  })

  it('surfaces memory recall context before assistant streaming completes', () => {
    const appended: Msg[] = []
    const onEvent = createGatewayEventHandler(buildCtx(appended))

    onEvent({
      payload: { memory_context: '## Hindsight\nearly context' },
      type: 'memory_context.available'
    } as any)

    expect(getTurnState().streamSegments).toHaveLength(1)
    expect(getTurnState().streamSegments[0]).toMatchObject({
      kind: 'memory',
      memoryContext: '## Hindsight\nearly context',
      role: 'assistant',
      text: ''
    })

    onEvent({ payload: { text: 'streamed final answer' }, type: 'message.delta' } as any)
    turnController.flushStreamingSegment()
    onEvent({ payload: { text: 'streamed final answer' }, type: 'message.complete' } as any)

    expect(appended).toHaveLength(2)
    expect(appended[0]).toMatchObject({
      kind: 'memory',
      memoryContext: '## Hindsight\nearly context',
      role: 'assistant',
      text: ''
    })
    expect(appended[1]).toMatchObject({ role: 'assistant', text: 'streamed final answer' })
  })
})
