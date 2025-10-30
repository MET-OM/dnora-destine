from dnora_destine.polytope_functions import download_ecmwf_from_destine

import xarray as xr
import numpy as np
from dnora.waveseries import WaveSeries
import pandas as pd

from dnora.read.ds_read_functions import setup_temp_dir
from dnora.type_manager.dnora_types import DnoraDataType
import geo_parameters as gp


def ds_polytope_waveseries_read(
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    url: str,
    ## Partial variables from ProductReader
    inds: list[int],
):
    name = "ECMWF"
    folder = setup_temp_dir(DnoraDataType.WAVESERIES, name)

    temp_file = f"{name}_temp.grib"
    grib_file = f"{folder}/{temp_file}"
    download_ecmwf_from_destine(
        start_time=start_time,
        url=url,
        out_file=grib_file,
        params="140229/140230/140231/140232",
        end_time=end_time,
    )
    ds = xr.open_dataset(grib_file, engine="cfgrib", decode_timedelta=True)
    ds = ds.isel(values=inds)
    ii = np.where(
        np.logical_and(
            ds.valid_time.values >= start_time, ds.valid_time.values <= end_time
        )
    )[0]
    ds = ds.isel(step=ii)
    data = WaveSeries.from_ds(
        ds,
        ds_aliases={"mwd": gp.wave.Dirm, "pp1d": gp.wave.Tp, "mwp": gp.wave.Tm01},
        time=ds.valid_time.values,
    )
    return data.ds()
