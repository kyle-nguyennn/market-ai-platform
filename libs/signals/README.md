# Signal research

Signals live **here**, inside `market-ai-platform`, and consume point-in-time
features to produce forecasts or alpha scores. Organize implementations under
`momentum/`, `mean_reversion/`, `order_flow/`, and `ml/`.

Future signal contracts should explicitly define instrument/universe, prediction
time, prediction horizon, units, direction, model version, and data cutoff.
Training and inference must not leak future observations.

Signal research does **not** send orders or import venue SDKs. Strategies consume
signals and decide how to trade them. The inference gateway may serve a promoted
version of a signal model, but deployment is not part of this skeleton.
