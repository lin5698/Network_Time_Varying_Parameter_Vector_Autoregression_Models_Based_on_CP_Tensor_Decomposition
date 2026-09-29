# NYC Taxi Fixed-Commit Source Preflight

**Date:** 2026-07-19

**Source preflight:** PASS

- Repository: `xinychen/vars`
- Observed origin: `https://github.com/xinychen/vars.git`
- Commit: `7e63ba9734021171eaf49edb92be8a7e7e8802eb`
- Dataset path: `datasets/NYC-taxi`
- Git worktree clean: `True`
- Scientific execution authorized: `false`
- R006e/R006f outcomes authorized: `false` / `false`

| File | Size (bytes) | SHA-256 | Symlink |
|---|---:|---|---:|
| `yellow_taxi_trip_2012.npz` | 1865245 | `152a2c68b8a0e7bfed4a09d28d6b9dbbb9473d9e55b9939c4edaf16ca2408adc` | `False` |
| `yellow_taxi_trip_2013.npz` | 1852865 | `c852bcfdce0735932b93659fb946842eefe06d6eabf6d3c09103147338b8023b` | `False` |
| `yellow_taxi_trip_2014.npz` | 1831133 | `9fa81c54ccd0067c7f6482250a0c2285f129d00f322636c8a0591b99ed600824` | `False` |
| `yellow_taxi_trip_2015.npz` | 1784995 | `c6f1e05873e8cf5fd57a0d6d25e921d4549579b741d1bc2e5f6234e42622b60f` | `False` |
| `yellow_taxi_trip_2016.npz` | 1745305 | `9bfc4fc32529d229f5eb4e033e6a364a83ad443bd8a43c5b52a91d1f77bcee35` | `False` |
| `yellow_taxi_trip_2017.npz` | 1686068 | `1d5d1c1fe1af58f1af9f8460a141496dabc218ae2903ad0a40f416574b99e87a` | `False` |
| `yellow_taxi_trip_2018.npz` | 1644986 | `ab2e140574266b918a25ae2ae21099b7e777e2397dceae236bc8d5b4daddccda` | `False` |
| `yellow_taxi_trip_2019.npz` | 1578958 | `69b1918a5dcb5d9f7cd8b72be5dd356e965e81b653eb7772ab0f8ae66777d8f3` | `False` |
| `yellow_taxi_trip_2020.npz` | 1163976 | `ad2c41401836dab97831b10897143da89d05a3d105a8590bdf29c3ad3832ca09` | `False` |
| `yellow_taxi_trip_2021.npz` | 1290141 | `c76eb7046ff14ff39fe9cdf444838cf252e0d90e00c7cb1ca164ca8957e389f1` | `False` |

## Boundary

The public NYC source identity is verified, but the joint RCEP/NYC production run remains closed until the RCEP helper candidate and schema-v2 trust manifest receive explicit author approval.

This preflight verifies source identity and file provenance only. It does not load arrays, construct a panel, validate scientific dimensions, reproduce any archived NYC value or authorize manuscript claims.
