## Bars / Market Data Design Notes
### Real-time data handling
* Use **native Python bar objects** (or lightweight structures).
  * DataFrame row insertion is **relatively expensive**.
  * Real-time systems require **frequent incremental updates** (tick → bar).
  * Objects allow **O(1) mutation** (update high/low/volume easily).

```
tick → BarBuilder → Bar object → strategy engine
```
* During tick aggregation, **object representation is more natural**.
OHLCV are **simple field updates in objects**, but awkward in DataFrames.

### Static / historical datasets
* Use **DataFrame** for completed bar series.
  * efficient **vectorized operations**
  * fast **indicator computation**
  * easy **time slicing and filtering**
  * convenient for **analysis and research**
  * MA, RSI, signals, backtesting

### Typical system architecture
```
Live system
    tick → Bar object → strategy

Storage / research
    bars → DataFrame → indicators → signals
```
```
[Practical hybrid approach]
Real-time bars (objects)
        ↓
Periodic archive
        ↓
DataFrame (historical data)
```

## Note keeping
- using fdr prices update is temporary and might be unstable (due to the KRX policy change)
- fdr prices are adjusted based on the outstanding number of stocks (e.g., stock splits, etc)
    * internally, it checks if fdr # of stocks is changed from the lastest date in the existing db
    * if changed, prices are fully re-downloaded
- volumes are not adjusted by splits...
