"""Voice demo that runs a simulated trade proposal through the dialog manager.

Run this script to test the dialog flow in a terminal. It will fall back to typed input if audio
libraries or microphone are not available.
"""

from src.voice.dialog_manager import DialogManager


def demo():
    dm = DialogManager()
    trade = {
        'symbol': 'AAPL',
        'direction': 'LONG',
        'suggested_allocation_pct': 1.0,
        'entry_price': 170.5,
        'stop_loss': 166.5,
        'rationale': 'Momentum breakout on daily chart',
        'backtest_stats': {'return_pct': 8.2, 'sharpe_est': 0.7, 'win_rate': 73}
    }
    result = dm.propose_trade(trade)
    print('Demo result:', result)


if __name__ == '__main__':
    demo()
