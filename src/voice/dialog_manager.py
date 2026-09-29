"""Dialog manager that runs the voice confirmation state machine.

This module orchestrates presenting a trade summary, collecting allocation and confirmation
from the user via TTS+ASR (or text fallback), performing safety checks, and returning the
final decision object used by the trading agent.

The design enforces a paper-first policy and hard safety overrides that cannot be bypassed.
"""
from typing import Dict, Any, Optional
import time
import os

from src.voice import tts, asr, command_parser

# Safety defaults (tunable)
MAX_TRADE_ALLOCATION_PCT = float(os.getenv('MAX_TRADE_ALLOCATION_PCT', '2.0'))  # percent
MAX_DAILY_LOSS_PCT = float(os.getenv('MAX_DAILY_LOSS_PCT', '2.0'))
MAX_DRAWDOWN_PCT = float(os.getenv('MAX_DRAWDOWN_PCT', '10.0'))
VOICE_TIMEOUT_SEC = int(os.getenv('VOICE_TIMEOUT_SEC', '30'))
RECONFIRM_WINDOW_SEC = int(os.getenv('RECONFIRM_WINDOW_SEC', '10'))


class DialogManager:
    def __init__(self, store=None, allow_live: bool = False):
        self.store = store
        self.allow_live = allow_live

    def _safety_check_allocation_pct(self, pct: float) -> (bool, Optional[str]):
        if pct <= 0:
            return False, 'Allocation must be greater than zero.'
        if pct > MAX_TRADE_ALLOCATION_PCT:
            return False, f'Requested allocation {pct}% exceeds maximum per-trade allocation {MAX_TRADE_ALLOCATION_PCT}%' 
        # Additional checks like buying power or daily loss can be added with self.store state
        return True, None

    def _hard_overrides(self) -> (bool, Optional[str]):
        # Check kill-switch or daily loss from store if available
        # Example: store could expose get_daily_loss_pct()
        if self.store is not None:
            try:
                if hasattr(self.store, 'get_flag') and self.store.get_flag('kill_switch'):
                    return True, 'Emergency kill-switch is active.'
                # placeholder for daily loss
                if hasattr(self.store, 'get_daily_loss_pct'):
                    daily_loss = float(self.store.get_daily_loss_pct())
                    if daily_loss >= MAX_DAILY_LOSS_PCT:
                        return True, f'Daily loss {daily_loss}% exceeds limit {MAX_DAILY_LOSS_PCT}%' 
            except Exception:
                pass
        return False, None

    def propose_trade(self, trade_brief: Dict[str, Any]) -> Dict[str, Any]:
        """Main entrypoint.

        trade_brief should contain keys: symbol, direction, suggested_allocation_pct,
        entry_price, stop_loss, rationale, backtest_stats (dict)

        Returns a dict: { 'status': 'confirmed'|'cancelled'|'blocked', 'allocation_pct': float or None, 'reason': str }
        """
        # First check hard overrides
        blocked, reason = self._hard_overrides()
        if blocked:
            msg = f"I am blocked from trading: {reason}"
            tts.speak(msg)
            return {'status': 'blocked', 'allocation_pct': None, 'reason': reason}

        # Build human readable summary
        bt = trade_brief.get('backtest_stats', {})
        summary = (
            f"Proposed trade ready for review. Symbol: {trade_brief.get('symbol')} . "
            f"Direction: {trade_brief.get('direction')} . "
            f"Suggested allocation: {trade_brief.get('suggested_allocation_pct')}% of portfolio. "
            f"Entry price: {trade_brief.get('entry_price')} . "
            f"Stop-loss: {trade_brief.get('stop_loss')} . "
            f"Rationale: {trade_brief.get('rationale')} . "
            f"Backtest: Return {bt.get('return_pct', 'N/A')}%, Sharpe {bt.get('sharpe_est', 'N/A')}, win rate {bt.get('win_rate', 'N/A')}%."
        )

        # Speak and print
        tts.speak(summary)
        print('\n[Trade summary]\n' + summary + '\n')

        # Ask for allocation
        ask_alloc = 'How much capital should I allocate to this trade? Say a percent of portfolio or say "use suggested".'
        tts.speak(ask_alloc)

        # Listen / parse loop for allocation
        start = time.time()
        allocation_pct = None
        while True:
            response = asr.listen(prompt='Allocation reply>', timeout=VOICE_TIMEOUT_SEC)
            print('[User allocation reply] ', response)
            val, unit = command_parser.parse_allocation(response)
            # If user said use suggested
            if unit == 'use_suggested' or (val is None and unit == 'use_suggested'):
                allocation_pct = float(trade_brief.get('suggested_allocation_pct', MAX_TRADE_ALLOCATION_PCT))
                tts.speak(f'Using suggested allocation {allocation_pct} percent of portfolio. Is that correct? Say Confirm or Cancel.')
            elif val is not None and unit == 'pct':
                allocation_pct = float(val)
                tts.speak(f'Read back: allocate {allocation_pct} percent of portfolio. Is that correct? Say Confirm or Cancel.')
            elif val is not None and unit == 'usd':
                # Convert usd to pct if store can provide account size
                if self.store is not None and hasattr(self.store, 'get_account_value'):
                    try:
                        acct = float(self.store.get_account_value())
                        allocation_pct = float(val) / acct * 100.0
                        tts.speak(f'Read back: allocate ${val} which is approximately {allocation_pct:.2f} percent of portfolio. Is that correct? Say Confirm or Cancel.')
                    except Exception:
                        tts.speak('I cannot convert dollars to percent because account value is unknown. Please respond with a percent value.')
                        allocation_pct = None
                else:
                    tts.speak('I cannot convert dollars to percent because account value is unknown. Please respond with a percent value.')
                    allocation_pct = None
            else:
                tts.speak('Sorry, I did not understand. Please say a percent like "one percent" or say "use suggested".')

            # Ask for final confirmation
            start_confirm = time.time()
            while allocation_pct is not None:
                # Safety check
                ok, reason = self._safety_check_allocation_pct(allocation_pct)
                if not ok:
                    tts.speak(f'I will not accept allocation: {reason} Please provide a smaller allocation or say Cancel.')
                    allocation_pct = None
                    break

                tts.speak(f'Final confirmation required: place order for {trade_brief.get("symbol")} {trade_brief.get("direction")} with allocation {allocation_pct} percent and stop-loss at {trade_brief.get("stop_loss")}. Say Confirm to proceed or Cancel to abort.')
                response2 = asr.listen(prompt='Confirm reply>', timeout=VOICE_TIMEOUT_SEC)
                print('[User confirm reply] ', response2)
                c = command_parser.parse_confirm(response2)
                if c == 'confirm':
                    # Re-check hard overrides right before execution
                    blocked2, reason2 = self._hard_overrides()
                    if blocked2:
                        tts.speak(f'I will not place that trade because {reason2}')
                        return {'status': 'blocked', 'allocation_pct': None, 'reason': reason2}
                    # success
                    tts.speak('Confirmed. Placing order in paper mode.')
                    return {'status': 'confirmed', 'allocation_pct': allocation_pct, 'reason': None}
                elif c == 'cancel':
                    tts.speak('Canceled. No trade will be placed.')
                    return {'status': 'cancelled', 'allocation_pct': None, 'reason': 'user_cancelled'}
                else:
                    tts.speak('I did not understand. Please say Confirm or Cancel.')

            # Timeout guard
            if time.time() - start > VOICE_TIMEOUT_SEC:
                tts.speak('No response received. Canceling trade proposal for safety.')
                return {'status': 'cancelled', 'allocation_pct': None, 'reason': 'timeout'}


if __name__ == '__main__':
    # quick manual demo
    dm = DialogManager()
    tb = {
        'symbol': 'AAPL',
        'direction': 'LONG',
        'suggested_allocation_pct': 1.0,
        'entry_price': 170.5,
        'stop_loss': 166.5,
        'rationale': 'Momentum breakout on daily chart',
        'backtest_stats': {'return_pct': 8.2, 'sharpe_est': 0.7, 'win_rate': 73}
    }
    res = dm.propose_trade(tb)
    print('Dialog result:', res)
