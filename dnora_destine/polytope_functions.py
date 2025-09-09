import numpy as np
import xarray as xr
import pandas as pd
from dnora import utils
from dnora import msg
from scipy.interpolate import griddata

from dnora.spectra import Spectra
from dnora.wind import Wind
from dnora.ice import Ice
from dnora.type_manager.dnora_types import DnoraDataType

import os

import glob


# This is defined here because the dnora-version doesn't have the ability to keep old files
def setup_temp_dir(
    data_type: DnoraDataType, reader_name: str, clean_old_files: bool = True
) -> str:
    """Sets up a temporery directory for fimex files and cleans out possible old files"""
    temp_folder = f"dnora_{data_type.name.lower()}_temp"
    if not os.path.isdir(temp_folder):
        os.mkdir(temp_folder)
        print("Creating folder %s..." % temp_folder)
    if clean_old_files:
        msg.plain("Removing old files from temporary folder...")
        for f in glob.glob(f"dnora_{data_type.name.lower()}_temp/{reader_name}*.*"):
            os.remove(f)

    return temp_folder


def download_ecmwf_from_destine(start_time, end_time, lon, lat, folder: str) -> str:
    """Downloads 10 m wind data DestinE ClimateDT data portfolio data from the Destine Earth Store System  for a
    given area and time period"""
    start_time = pd.Timestamp(start_time)
    end_time = pd.Timestamp(end_time)
    try:
        from polytope.api import Client
    except ImportError as e:
        msg.advice(
            "The polytope package is required to acces these data! Install by e.g. 'python -m pip install polytope-client' and 'conda install cfgrib eccodes=2.41.0'"
        )
        raise e
    c = Client(address="polytope.lumi.apps.dte.destination-earth.eu")

    filename = f"{folder}/ECMWF_temp.grib"  # Switch to this in production. Then the files will be cleaned out
    # filename = f"{folder}/destine_temp.grib"
    request_winds = {
        "class": "d1",
        "expver": "0001",
        "dataset": "extremes-dt",
        "stream": "oper",
        "type": "fc",
        "levtype": "sfc",
        "param": "165/166",
        "time": "00",
        "step": "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23",
        "area": [
            int(np.ceil(lat[1])),
            int(np.floor(lon[0])),
            int(np.floor(lat[0])),
            int(np.ceil(lon[1])),
        ],
    }
    date_str = start_time.strftime("%Y%m%d")
    request_winds["date"] = date_str

    c.retrieve("destination-earth", request_winds, filename)
    return filename


def ds_polytope_read(
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    url: str,
    lon: np.ndarray,
    lat: np.ndarray,
    **kwargs,
):

    grib_file = download_ecmwf_from_destine(
        start_time, end_time, lon=lon, lat=lat, folder="dnora_wind_temp"
    )

    ds = xr.open_dataset(grib_file, engine="cfgrib", decode_timedelta=True)
    lons, lats, u10, v10 = (
        ds.u10.longitude.values,
        ds.u10.latitude.values,
        ds.u10.values,
        ds.v10.values,
    )
    native_dlon, native_dlat = 1 / 8, 1 / 30
    xi = np.arange(min(lons), max(lons), native_dlon)
    yi = np.arange(min(lats), max(lats), native_dlat)
    Xi, Yi = np.meshgrid(xi, yi)

    Nt = len(ds.step)
    u10i = np.zeros((Nt, len(yi), len(xi)))
    v10i = np.zeros((Nt, len(yi), len(xi)))
    # If this becomes slow, we need to think about 3D interpolation / resuing weights
    for n in range(Nt):
        u10i[n, :, :] = griddata(
            list(zip(lons, lats)), u10[n, :], (Xi, Yi), method="nearest"
        )
        v10i[n, :, :] = griddata(
            list(zip(lons, lats)), v10[n, :], (Xi, Yi), method="nearest"
        )

    data = Wind(lon=xi, lat=yi, time=ds.time + ds.step)
    data.set_u(u10i)
    data.set_v(v10i)
    lo, la = utils.grid.expand_area(
        lon, lat, expansion_factor=1, dlon=native_dlon, dlat=native_dlat
    )
    data = data.sel(lon=slice(*lo), lat=slice(*la))

    return data.sel(time=slice(start_time, end_time)).ds()


def download_ecmwf_wave_from_destine(
    start_time, filename: str, url: str, end_time=None
) -> None:
    """Downloads wave data from DestinE. If no end_time is given, a minimal query is done to get the coordinates of the points"""

    start_time = pd.Timestamp(start_time)

    if end_time is None:
        params = "140221"
        steps = "0"
        end_time = start_time
    else:
        params = "140229/140230/140231"
        # Because the reader is set up to do daily chunks, the start and end time will always be in the same day
        days = [str(l) for l in range(start_time.hour, end_time.hour + 1)]
        steps = "/".join(days)
        # steps = "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23"
    end_time = pd.Timestamp(end_time)

    try:
        from polytope.api import Client
    except ImportError as e:
        msg.advice(
            "The polytope package is required to acces these data! Install by e.g. 'python -m pip install polytope-client' and 'conda install cfgrib eccodes=2.41.0'"
        )
        raise e
    c = Client(address=url)

    request_waves = {
        "class": "d1",
        "expver": "0001",
        "dataset": "extremes-dt",
        "stream": "wave",
        "type": "fc",
        "levtype": "sfc",
        # Tm02/Hs/Dirm/Tp/Tm
        # "param": "140221/140229/140230/140231/140232",
        "param": params,
        "time": "00",
        "step": steps,
    }
    date_str = start_time.strftime("%Y%m%d")
    request_waves["date"] = date_str

    c.retrieve("destination-earth", request_waves, filename)


def ds_wave_polytope_read(
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    url: str,
    ## Partial variables from ProductReader
    inds: list[int],
    ## Partial variables in ProductConfiguration
    freq0: float,
    nfreq: int,
    finc: float,
    ndirs: int,
    **kwargs,
):
    name = "ECMWF"
    folder = setup_temp_dir(DnoraDataType.SPECTRA, name)

    temp_file = f"{name}_temp.grib"
    grib_file = f"{folder}/{temp_file}"
    download_ecmwf_wave_from_destine(start_time, grib_file, url, end_time)

    ds = xr.open_dataset(grib_file, engine="cfgrib", decode_timedelta=True)
    ds = ds.isel(values=inds)
    ii = np.where(
        np.logical_and(
            ds.valid_time.values >= start_time, ds.valid_time.values <= end_time
        )
    )[0]
    ds = ds.isel(step=ii)
    msg.plain("Calculating JONSWAP spectra with given Hs and Tp...")
    fp = 1 / ds.pp1d.values
    m0 = ds.swh.values**2 / 16

    freq = np.array([freq0 * finc**n for n in np.linspace(0, nfreq - 1, nfreq)])
    dD = 360 / ndirs
    dirs = np.linspace(0, 360 - dD, ndirs)
    E = utils.spec.jonswap1d(fp=fp, m0=m0, freq=freq)

    msg.plain("Expanding to cos**2s directional distribution around mean direction...")
    Ed = utils.spec.expand_to_directional_spectrum(E, freq, dirs, dirp=ds.mwd.values)
    obj = Spectra.from_ds(ds, freq=freq, dirs=dirs, time=ds.valid_time.values)
    obj.set_spec(Ed)

    return obj.ds()


def download_ecmwf_ice_from_destine(start_time, end_time, lon, lat, folder: str) -> str:
    """Downloads DestinE ClimateDT data portfolio data from the Destine Earth Store System for a
    given area and time period"""
    start_time = pd.Timestamp(start_time)
    end_time = pd.Timestamp(end_time)
    try:
        from polytope.api import Client
    except ImportError as e:
        msg.advice(
            "The polytope package is required to acces these data! Install by e.g. 'python -m pip install polytope-client' and 'conda install cfgrib eccodes=2.41.0'"
        )
        raise e
    c = Client(address="polytope.lumi.apps.dte.destination-earth.eu")

    filename = f"{folder}/ECMWF_temp_ice.grib"  # Switch to this in production. Then the files will be cleaned out
    # filename = f"{folder}/destine_temp.grib"
    request_ice = {
        "class": "d1",
        "expver": "0001",
        "dataset": "extremes-dt",
        "stream": "oper",
        "type": "fc",
        "levtype": "sfc",
        "param": "31",
        "time": "00",
        "step": "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23",
        "area": [
            int(np.ceil(lat[1])),
            int(np.floor(lon[0])),
            int(np.floor(lat[0])),
            int(np.ceil(lon[1])),
        ],
    }
    date_str = start_time.strftime("%Y%m%d")
    request_ice["date"] = date_str

    c.retrieve("destination-earth", request_ice, filename)
    return filename


def ds_ice_polytope_read(
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    url: str,
    lon: np.ndarray,
    lat: np.ndarray,
    **kwargs,
):

    grib_file = download_ecmwf_ice_from_destine(
        start_time, end_time, lon=lon, lat=lat, folder="dnora_ice_temp"
    )

    ds = xr.open_dataset(grib_file, engine="cfgrib", decode_timedelta=True)
    lons, lats, sic = (
        ds.siconc.longitude.values,
        ds.siconc.latitude.values,
        ds.siconc.values,
        # ds.sit.values,
    )
    native_dlon, native_dlat = 1 / 8, 1 / 30
    xi = np.arange(min(lons), max(lons), native_dlon)
    yi = np.arange(min(lats), max(lats), native_dlat)
    Xi, Yi = np.meshgrid(xi, yi)

    Nt = len(ds.step)
    sici = np.zeros((Nt, len(yi), len(xi)))
    # siti = np.zeros((Nt, len(yi), len(xi)))
    # If this becomes slow, we need to think about 3D interpolation / resuing weights
    for n in range(Nt):
        sici[n, :, :] = griddata(
            list(zip(lons, lats)), sic[n, :], (Xi, Yi), method="nearest"
        )
        # siti[n, :, :] = griddata(
        #    list(zip(lons, lats)), sit[n, :], (Xi, Yi), method="nearest"
        # )

    data = Ice(lon=xi, lat=yi, time=ds.time + ds.step)
    data.set_sic(sici)
    # data.set_sit(siti)
    lo, la = utils.grid.expand_area(
        lon, lat, expansion_factor=1, dlon=native_dlon, dlat=native_dlat
    )
    data = data.sel(lon=slice(*lo), lat=slice(*la))

    return data.sel(time=slice(start_time, end_time)).ds()
