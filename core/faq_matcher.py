import difflib
import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import FAQ

logger = logging.getLogger(__name__)

# In-memory cache: list of (question_lower, answer) tuples
_faq_cache: list[tuple[str, str]] = []
_cache_loaded: bool = False


async def _load_cache(db: AsyncSession):
    global _faq_cache, _cache_loaded
    result = await db.execute(select(FAQ))
    faqs = result.scalars().all()
    _faq_cache = [(faq.question.lower(), faq.answer) for faq in faqs]
    _cache_loaded = True
    logger.info(f"FAQ cache loaded: {len(_faq_cache)} entries")


def invalidate_faq_cache():
    """Call after any FAQ insert/delete to force reload on next request."""
    global _cache_loaded
    _cache_loaded = False


async def find_faq_match(db: AsyncSession, user_message: str) -> str | None:
    global _cache_loaded
    if not _cache_loaded:
        await _load_cache(db)

    if not _faq_cache:
        return None

    questions = [q for q, _ in _faq_cache]
    matches = difflib.get_close_matches(
        user_message.lower(), questions, n=1, cutoff=0.55  # lowered from 0.7
    )

    if matches:
        matched_q = matches[0]
        for q, answer in _faq_cache:
            if q == matched_q:
                return answer
    return None
