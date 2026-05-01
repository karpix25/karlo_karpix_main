from __future__ import annotations

def auth_headers() -> dict[str, str]:
    return {'X-Telegram-Init-Data': 'user_id=1&username=tester'}


def test_api_lifecycle(client) -> None:
    headers = auth_headers()

    r = client.put('/api/settings/sources', json={'channels': ['@test_channel']}, headers=headers)
    assert r.status_code == 200

    r = client.post('/api/runs/trigger', json={'trigger_source': 'manual'}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body['status'] == 'completed'

    inbox_resp = client.get('/api/inbox?status=accepted', headers=headers)
    assert inbox_resp.status_code == 200
    inbox = inbox_resp.json()
    assert len(inbox) >= 1

    drafts_resp = client.get('/api/drafts?platform=telegram&status=in_review', headers=headers)
    assert drafts_resp.status_code == 200
    drafts = drafts_resp.json()
    assert len(drafts) >= 1

    draft_id = drafts[0]['id']
    update_resp = client.put(
        f'/api/drafts/{draft_id}',
        json={'content': 'Updated content for approval', 'cta': 'CTA', 'hashtags': '#test'},
        headers=headers,
    )
    assert update_resp.status_code == 200

    approve_resp = client.post(f'/api/drafts/{draft_id}/approve', headers=headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()['status'] == 'published'

    anti_abuse_get = client.get('/api/settings/anti-abuse', headers=headers)
    assert anti_abuse_get.status_code == 200
    assert anti_abuse_get.json()['enabled'] is True

    anti_abuse_put = client.put(
        '/api/settings/anti-abuse',
        json={
            'enabled': True,
            'messages_per_channel': 2,
            'channel_jitter_min_ms': 1000,
            'channel_jitter_max_ms': 1500,
            'batch_size': 5,
            'batch_pause_min_s': 5,
            'batch_pause_max_s': 10,
            'max_retries': 2,
            'retry_backoff_s': [1, 3, 6],
            'floodwait_extra_jitter_min_s': 1,
            'floodwait_extra_jitter_max_s': 2,
            'channel_error_threshold': 2,
            'channel_cooldown_default_s': 600,
            'manual_bypass_cooldown': False,
        },
        headers=headers,
    )
    assert anti_abuse_put.status_code == 200
    assert anti_abuse_put.json()['messages_per_channel'] == 2

    guard_status = client.get('/api/settings/anti-abuse/guard-status', headers=headers)
    assert guard_status.status_code == 200
    guard_payload = guard_status.json()
    assert 'cooldowns' in guard_payload
    assert 'recent_events' in guard_payload
