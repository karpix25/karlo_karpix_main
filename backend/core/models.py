from __future__ import annotations

from enum import Enum


class CandidateStatus(str, Enum):
    accepted = 'accepted'
    rejected = 'rejected'


class DraftPlatform(str, Enum):
    telegram = 'telegram'
    threads = 'threads'
    reels = '5s Reels'
    avatar = 'Аватар'
    carousel = 'Карусель'


class DraftStatus(str, Enum):
    generated = 'generated'
    in_review = 'in_review'
    approved = 'approved'
    published = 'published'
    rejected = 'rejected'
    ready_for_manual_publish = 'ready_for_manual_publish'
    error = 'error'


class RunStatus(str, Enum):
    pending = 'pending'
    running = 'running'
    completed = 'completed'
    failed = 'failed'
    skipped = 'skipped'
