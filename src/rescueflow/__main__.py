from .demo import demo_history, inventory_catalog
from .forecast import train_and_forecast
from .decisions import make_recommendations

if __name__ == '__main__':
    history = demo_history()
    result = train_and_forecast(history)
    decisions = make_recommendations(inventory_catalog(), result.forecasts)
    print(f"Training rows: {len(history)} | Backtest mean MAE: {result.metrics.mae.mean():.2f}")
    print(decisions[['product', 'order_units', 'donation_units']].to_string(index=False))
