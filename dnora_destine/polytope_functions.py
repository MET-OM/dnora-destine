import numpy as np
import pandas as pd
from dnora import msg
import os

import glob


def get_destine_steps(start_time: str, end_time: str) -> tuple[str, list[int]]:
    """DestinE data in daily runs, so first step (0) is 00:00

    Function calculates which steps are needed to cover exactly start_time and end_time

    returns the start date and list of steps
    """
    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)

    date_str = start_time.strftime("%Y%m%d")
    start_of_day = pd.to_datetime(f"{date_str} 00:00:00")

    first_step = int(pd.to_timedelta(start_time - start_of_day).total_seconds() / 3600)
    last_step = int(pd.to_timedelta(end_time - start_of_day).total_seconds() / 3600) + 1
    all_steps = range(first_step, last_step)

    return date_str, list(all_steps)


def download_ecmwf_from_destine(
    start_time,
    url: str,
    out_file: str,
    params: str,
    end_time: str = None,
    lon: tuple[float] = None,
    lat: tuple[float] = None,
    levelist: int = None,
) -> None:
    """Downloads 10 m wind data DestinE ClimateDT data portfolio data from the Destine Earth Store System  for a
    given area and time period"""
    try:
        from polytope.api import Client
    except ImportError as e:
        msg.advice(
            "The polytope package is required to acces these data! Install by e.g. 'python -m pip install polytope-client' and 'conda install cfgrib eccodes=2.41.0'"
        )
        raise e

    start_time = pd.Timestamp(start_time)
    if end_time is None:
        params = params.split("/")[0]
        end_time = start_time

    date_str, steps = get_destine_steps(start_time, end_time)
    steps = "/".join([f"{h:.0f}" for h in steps])
    request_data = {
        "class": "d1",
        "expver": "0001",
        "dataset": "extremes-dt",
        "type": "fc",
        "levtype": "sfc",
        "param": params,
        "time": "00",
        "date": date_str,
        "step": steps,  # "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23",
    }

    if lon is not None and lat is not None:
        request_data["stream"] = "oper"
        request_data["area"] = [
            int(np.ceil(lat[1])),
            int(np.floor(lon[0])),
            int(np.floor(lat[0])),
            int(np.ceil(lon[1])),
        ]
    else:
        request_data["stream"] = "wave"

    if levelist:
        levelist = str(levelist)
        request_data["levtype"] = "pl"
        request_data["levelist"] = levelist

    c = Client(address=url)

    c.retrieve("destination-earth", request_data, out_file)
