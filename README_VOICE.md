# Bilingual voice demo using Hindi as default, English as fallback

from src.voice.dialog_manager import HindiDialogManager


def demo():
    dm = HindiDialogManager(language='hi')
    trade = {
        'symbol': 'AAPL',
        'direction': 'LONG',
        'suggested_allocation_pct': 1.0,
        'entry_price': 170.5,
        'stop_loss': 166.5,
        'rationale': 'Daily momentum breakout',
        'backtest_stats': {'return_pct': 8.2, 'sharpe_est': 0.7, 'win_rate': 73}
    }
    print(dm.propose_trade(trade))


if __name__ == '__main__':
    demo()
