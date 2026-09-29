"""Hindi-first bilingual dialog manager with language switching support.

This module calls the language-aware prompts and accepts either English or Hindi commands.
It keeps paper-first enforcement and safe confirmation flow.
"""

from typing import Dict, Any, Optional
import time
import os

from src.voice import tts, asr
from src.voice.command_parser import parse_allocation, parse_confirm
from src.voice.language import normalize_language, choose_text

DEFAULT_LANGUAGE = 'hi'
VOICE_TIMEOUT_SEC = int(os.getenv('VOICE_TIMEOUT_SEC', '30'))
MAX_TRADE_ALLOCATION_PCT = float(os.getenv('MAX_TRADE_ALLOCATION_PCT', '2.0'))


class HindiDialogManager:
    def __init__(self, store=None, language: str = DEFAULT_LANGUAGE, allow_live: bool = False):
        self.store = store
        self.language = normalize_language(language)
        self.allow_live = allow_live

    def speak(self, text: str):
        tts.speak(text)

    def _hard_overrides(self):
        if self.store is not None:
            try:
                if hasattr(self.store, 'get_flag') and self.store.get_flag('kill_switch'):
                    return True, 'Emergency kill-switch is active.'
            except Exception:
                pass
        return False, None

    def _safety_check_allocation_pct(self, pct):
        if pct <= 0:
            return False, choose_text(self.language, 'blocked', reason='Allocation must be greater than zero.')
        if pct > MAX_TRADE_ALLOCATION_PCT:
            return False, choose_text(self.language, 'blocked', reason=f'Requested allocation {pct}% exceeds max {MAX_TRADE_ALLOCATION_PCT}%.')
        return True, None

    def propose_trade(self, trade_brief: Dict[str, Any]) -> Dict[str, Any]:
        bt = trade_brief.get('backtest_stats', {})
        summary = (
            f"{choose_text(self.language, 'trade_summary')} "
            f"{choose_text(self.language, 'symbol')}: {trade_brief.get('symbol')}. "
            f"{choose_text(self.language, 'direction')}: {trade_brief.get('direction')}. "
            f"{choose_text(self.language, 'suggested_allocation')}: {trade_brief.get('suggested_allocation_pct')}%. "
            f"{choose_text(self.language, 'entry')}: {trade_brief.get('entry_price')}. "
            f"{choose_text(self.language, 'stop_loss')}: {trade_brief.get('stop_loss')}. "
            f"{choose_text(self.language, 'rationale')}: {trade_brief.get('rationale')}. "
            f"{choose_text(self.language, 'backtest')}: Return {bt.get('return_pct', 'N/A')}%, Sharpe {bt.get('sharpe_est', 'N/A')}, Win Rate {bt.get('win_rate', 'N/A')}%."
        )
        self.speak(summary)
        print('[Trade summary]', summary)

        self.speak(choose_text(self.language, 'ask_allocation'))
        allocation_pct = None
        start = time.time()
        while True:
            response = asr.listen(prompt='Response>', timeout=VOICE_TIMEOUT_SEC)
            print('[User reply]', response)
            val, unit = parse_allocation(response)
            if unit == 'use_suggested':
                allocation_pct = float(trade_brief.get('suggested_allocation_pct', 1.0))
            elif val is not None and unit == 'pct':
                allocation_pct = float(val)
            elif val is not None and unit == 'usd':
                # Dollar conversion fallback to percent using account value if available; if not, ask again
                if self.store is not None and hasattr(self.store, 'get_account_value'):
                    try:
                        acct_val = float(self.store.get_account_value())
                        allocation_pct = (float(val) / acct_val) * 100.0
                    except Exception:
                        allocation_pct = None
                else:
                    allocation_pct = None
            else:
                self.speak('मैं समझ नहीं पाया। कृपया प्रतिशत बताइए या “सुझाव अनुसार” कहें।')
                if time.time() - start > VOICE_TIMEOUT_SEC:
                    self.speak(choose_text(self.language, 'timeout'))
                    return {'status': 'cancelled', 'allocation_pct': None, 'reason': 'timeout'}
                continue

            if allocation_pct is None:
                self.speak('कृपया प्रतिशत में आवंटन बताइए।')
                continue

            ok, reason = self._safety_check_allocation_pct(allocation_pct)
            if not ok:
                self.speak(reason)
                return {'status': 'blocked', 'allocation_pct': None, 'reason': reason}

            self.speak(f"आपने {allocation_pct} प्रतिशत आवंटन चुना है। क्या यह सही है? 'पुष्टि करें' या 'रद्द करें' कहें।")
            final_resp = asr.listen(prompt='Final confirmation>', timeout=VOICE_TIMEOUT_SEC)
            decision = parse_confirm(final_resp)
            if decision == 'confirm':
                blocked, reason = self._hard_overrides()
                if blocked:
                    self.speak(choose_text(self.language, 'override', reason=reason))
                    return {'status': 'blocked', 'allocation_pct': allocation_pct, 'reason': reason}
                self.speak(choose_text(self.language, 'confirm_success'))
                return {'status': 'confirmed', 'allocation_pct': allocation_pct, 'reason': None}
            if decision == 'cancel':
                self.speak(choose_text(self.language, 'cancelled'))
                return {'status': 'cancelled', 'allocation_pct': None, 'reason': 'user_cancelled'}
            self.speak('मैं समझ नहीं पाया। कृपया “पुष्टि करें” या “रद्द करें” कहें।')
            if time.time() - start > VOICE_TIMEOUT_SEC:
                self.speak(choose_text(self.language, 'timeout'))
                return {'status': 'cancelled', 'allocation_pct': None, 'reason': 'timeout'}
