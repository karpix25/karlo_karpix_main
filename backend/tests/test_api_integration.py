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
