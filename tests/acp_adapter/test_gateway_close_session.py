"""session/close detaches one editor session: the owner ends it once idle, history stays, load reopens."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from acp.schema import TextContentBlock

from acp_adapter.gateway_server import GatewayACPAgent
from hermes_cli.gateway_client import GatewayClientError
from tests.waiting import async_wait_until


def attached_agent():
    agent = GatewayACPAgent()
    agent._snapshots['s'] = {'subscription_id': 'sub-1', 'execution_generation': 7}
    agent._editor_mcp['s'] = {'mcp_servers': []}
    agent._gateway = AsyncMock()
    agent._conn = AsyncMock()
    return agent


@pytest.mark.asyncio
async def test_initialize_advertises_close():
    reply = await GatewayACPAgent().initialize(protocol_version=1)
    assert reply.agent_capabilities.session_capabilities.close is not None


@pytest.mark.asyncio
async def test_close_detaches_and_forgets_the_session():
    agent = attached_agent()
    agent._aliases['held'] = 's'

    await agent.close_session('held')

    assert [(c.args[0], c.kwargs) for c in agent._gateway.rpc.await_args_list] == [
        ('session.detach', {'session_id': 's', 'subscription_id': 'sub-1'})]
    assert 's' not in agent._snapshots and 's' not in agent._editor_mcp
    # A reconnect must not re-attach it, and the editor can no longer address it until it loads again.
    with pytest.raises(GatewayClientError, match='not_found'):
        await agent.cancel('s')


@pytest.mark.asyncio
async def test_close_of_an_unknown_session_is_a_no_op():
    agent = attached_agent()
    await agent.close_session('other')
    agent._gateway.rpc.assert_not_awaited()
    assert 's' in agent._snapshots


@pytest.mark.asyncio
async def test_close_cancels_its_running_prompt_before_detaching():
    agent = attached_agent()
    agent._gateway.rpc.return_value = {'admission_id': 'ours'}
    prompt = asyncio.create_task(agent.prompt([TextContentBlock(type='text', text='hello')], 's'))
    await asyncio.sleep(0)
    agent._gateway.rpc.reset_mock()
    agent._gateway.rpc.return_value = {'admission_id': 'ours', 'status': 'terminal', 'outcome': 'cancelled'}

    close = asyncio.create_task(agent.close_session('s'))
    await async_wait_until(lambda: agent._gateway.rpc.await_args_list, what='close cancels the prompt')
    assert not close.done(), 'close waits for the prompt it cancelled'
    assert 's' in agent._snapshots
    await agent._project({'session_id': 's', 'type': 'message.complete', 'admission_id': 'ours',
                          'payload': {'outcome': 'cancelled', 'text': ''}})

    assert (await asyncio.wait_for(prompt, 2)).stop_reason == 'cancelled'
    await asyncio.wait_for(close, 2)
    methods = [c.args[0] for c in agent._gateway.rpc.await_args_list]
    assert methods[0] == 'prompt.cancel' and methods[-1] == 'session.detach'
    assert 's' not in agent._snapshots


@pytest.mark.asyncio
async def test_close_that_cannot_drain_keeps_the_session_attached(monkeypatch):
    agent = attached_agent()
    agent._submitting.add('s')
    monkeypatch.setattr('acp_adapter.gateway_server._CLOSE_DRAIN_TIMEOUT_S', 0.1)
    with pytest.raises(GatewayClientError, match='close_busy'):
        await agent.close_session('s')
    assert 's' in agent._snapshots
    assert 'session.detach' not in [c.args[0] for c in agent._gateway.rpc.await_args_list]


@pytest.mark.asyncio
async def test_detach_ends_the_idle_acp_row_and_keeps_its_history(tmp_path, monkeypatch):
    from gateway import run
    from gateway.config import GatewayConfig
    from gateway.session import SessionStore
    from gateway.session_authority import initialize_session_authority
    from gateway.session_controls import AuthorityConnection
    from gateway.session_local import create_local_session
    from hermes_state_local import local_receipt

    monkeypatch.setattr(run, '_load_gateway_config', lambda: {'platform_toolsets': {'acp': []}})
    store = SessionStore(tmp_path / 'sessions', GatewayConfig())
    runner = SimpleNamespace(session_store=store, _session_db=store._db, adapters={}, _draining=False,
                             _cached_agent_for=lambda route: None)
    runner._adapter_for_source = lambda source: runner.adapters.get(source.platform)
    authority = await initialize_session_authority(runner, profile_id='fixture', instance_id='owner')
    db = authority.db
    try:
        editor = AuthorityConnection(authority, object(), {'user_id': 'human', 'profile_id': 'fixture'})
        ref = create_local_session(authority, editor.actor, {'request_id': 'editor', 'source': 'acp',
                                                             'cwd': str(tmp_path), 'model': 'frozen',
                                                             'toolsets': []})
        row = local_receipt(db, ref.session_id)['entry']['session_id']
        db.append_message(row, 'user', 'retained')
        resumed = await editor.dispatch({'id': 1, 'method': 'session.resume',
                                         'params': {'session_id': ref.session_id}})
        detached = await editor.dispatch({'id': 2, 'method': 'session.detach', 'params': {
            'session_id': ref.session_id, 'subscription_id': resumed['result']['subscription_id']}})

        assert detached['result']['detached'] is True
        ended = db.get_session(row)
        assert ended['ended_at'] is not None and ended['end_reason'] == 'acp_disconnect'
        assert [m['content'] for m in db.get_messages(row)] == ['retained']
    finally:
        store.close_all_db_handles()


@pytest.mark.asyncio
async def test_close_retires_its_open_permission_cards():
    agent = attached_agent()
    card = asyncio.create_task(asyncio.Event().wait())
    other = asyncio.create_task(asyncio.Event().wait())
    agent._permissions[('s', 'p1', 7)] = card
    agent._permissions[('t', 'p2', 1)] = other

    await agent.close_session('s')
    await asyncio.sleep(0)

    assert card.cancelled() and not other.done()
    assert list(agent._permissions) == [('t', 'p2', 1)]
    other.cancel()


@pytest.mark.asyncio
async def test_recovery_queued_before_close_is_dropped():
    agent = attached_agent()
    await agent.close_session('s')
    agent._gateway.rpc.reset_mock()

    await agent._recover('s', 'ours')

    agent._gateway.rpc.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_prompt_whose_slash_command_outlived_the_close_never_submits(monkeypatch):
    agent = attached_agent()
    monkeypatch.setattr(agent, '_prepare_submit', AsyncMock(return_value=('key', 'input', ('/model x', []))))

    async def slash_while_closing(held_id, session_id, text):
        await agent.close_session(session_id)
        return False, text
    monkeypatch.setattr(agent, '_run_slash', slash_while_closing)

    with pytest.raises(GatewayClientError, match='not_found'):
        await agent.prompt([TextContentBlock(type='text', text='/model x')], 's')
    assert 'prompt.submit' not in [c.args[0] for c in agent._gateway.rpc.await_args_list]
