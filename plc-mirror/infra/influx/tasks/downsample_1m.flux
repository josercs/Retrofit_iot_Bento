option task = {name: "downsample_1m", every: 5m}
from(bucket: "processo_raw")
  |> range(start: -5m)
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> to(bucket: "processo_1m")
