"""Pre-agent cron gates settle metadata without inventing conversation turns."""
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('gate', ['skip', 'error', 'cancelled', 'exception'])
def test_pre_agent_gate_ends_canonical_session(tmp_path, monkeypatch, gate):
    from cron import scheduler
    from gateway import session_cron
    from hermes_state import SessionDB

    db = SessionDB(tmp_path / 'state.db')
    db.create_session('fire', source='cron')
    owner = SimpleNamespace(db=db)
    result = (gate == 'skip', 'gate document', '[SILENT]' if gate == 'skip' else '',
              None if gate == 'skip' else gate)

    def prepare(*args):
        if gate == 'exception':
            raise ValueError('gate crashed')
        return result, None

    monkeypatch.setattr(scheduler, '_prepare_job_prompt', prepare)
    monkeypatch.setattr(scheduler, '_construct_cron_agent', lambda *a, **k: pytest.fail('agent constructed'))
    token = session_cron.bind_execution(owner, 'fire', 'job', 'execution')
    try:
        if gate == 'exception':
            with pytest.raises(ValueError, match='gate crashed'):
                scheduler.run_job({'id': 'job', 'name': 'Gate check'}, execution_id='execution')
        else:
            assert scheduler.run_job({'id': 'job', 'name': 'Gate check'}, execution_id='execution') == result
        row = db.get_session('fire')
        assert row['ended_at'] is not None
        assert row['end_reason'] == ('cron_skipped' if gate == 'skip' else 'cron_error')
        assert row['title']
        assert db.get_messages('fire') == []
    finally:
        session_cron._execution.reset(token)
        db.close()


@pytest.mark.asyncio
async def test_wake_gate_retains_canonical_admission_receipt(tmp_path, monkeypatch):
    from cron import jobs, scheduler
    from gateway import run, session_cron
    from gateway.config import GatewayConfig
    from gateway.session import SessionStore
    from gateway.session_authority import SessionAuthority
    from gateway.session_contract import SessionRef
    from hermes_state import SessionDB
    from hermes_state_runtime import begin_runtime_epoch, claim_session_input, settle_session_input

    job = {'id': 'job', 'name': 'Wake check', 'prompt': 'review', 'script': 'check.py', 'model': 'm'}
    monkeypatch.setattr(jobs, 'get_job', lambda jid: job)
    monkeypatch.setattr(run, '_load_gateway_config', lambda: {'model': {}, 'platform_toolsets': {'cli': []}})
    monkeypatch.setattr(scheduler, '_run_job_script_with_claim_heartbeat',
                        lambda *a, **k: (True, '{"wakeAgent": false}'))
    monkeypatch.setattr(scheduler, '_construct_cron_agent', lambda *a, **k: pytest.fail('agent constructed'))
    db = SessionDB(tmp_path / 'state.db')
    runner = SimpleNamespace(_draining=False, adapters={},
                             session_store=SessionStore(tmp_path / 'sessions', GatewayConfig()))
    authority = SessionAuthority(runner, profile_id=str(tmp_path), instance_id='test', db=db,
                                 epoch=begin_runtime_epoch(db, instance_id='test'))
    runner.session_authority = authority
    monkeypatch.setattr(authority, '_schedule', lambda ref: None)
    params = {'job_id': 'job', 'request_id': 'fire', 'extra_prompt': None}
    try:
        receipt = await session_cron.operation(authority, 'submit', params)
        sid = receipt['session_id']
        row = claim_session_input(db, epoch=authority.epoch, session_id=sid)
        policy = next(iter(runner.adapters.values())).policies[sid]
        assert await session_cron.execute(authority, SessionRef(str(tmp_path), sid), row, policy) == '[SILENT]'
        saved = authority.pending_results.pop(row['admission_id'])
        settle_session_input(db, epoch=authority.epoch, admission_id=row['admission_id'],
                             generation=row['generation'], outcome='completed', result=saved)
        state = await session_cron.operation(authority, 'status',
                                             {'session_id': sid, 'admission_id': row['admission_id']})
        assert state['status'] == 'terminal'
        assert state['result'][0] is True and state['result'][2:] == ['[SILENT]', None]
        assert await session_cron.operation(authority, 'submit', params) == receipt
        assert db.get_session(sid)['end_reason'] == 'cron_skipped'
        assert db.get_messages(sid) == []
    finally:
        db.close()


def test_stored_picker_omits_only_ended_empty_cron(tmp_path, monkeypatch):
    from gateway import session_listing
    from gateway.session_contract import Principal
    from hermes_state import SessionDB

    db = SessionDB(tmp_path / 'state.db')
    for sid, source, ended, content in [
        ('skipped', 'cron', True, None), ('pending', 'cron', False, None),
        ('real', 'cron', True, 'real answer'), ('human', 'cli', True, None),
    ]:
        db.create_session(sid, source=source)
        if content:
            db.append_message(sid, 'assistant', content)
        if ended:
            db.end_session(sid, 'cron_complete')
    actor = Principal('owner', 'p', frozenset({'session:read', 'session:create'}), 'native')
    authority = SimpleNamespace(db=db, profile_id='p', _native_legacy_transports={'native': actor})
    monkeypatch.setattr(session_listing, '_closed_local_session',
                        lambda authority, actor, row, tip: {'id': row['id']})
    try:
        rows = session_listing.stored_picker_sessions(authority, actor, limit=20)['sessions']
        assert {row['id'] for row in rows} == {'pending', 'real', 'human'}
    finally:
        db.close()
