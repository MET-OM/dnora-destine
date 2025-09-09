from dnora.modelrun.modelrun import ModelRun
from dnora.type_manager.dnora_types import DnoraDataType
import dnora_destine.spectra, dnora_destine.wind, dnora_destine.ice


class ECMWF(ModelRun):
    _reader_dict = {
        DnoraDataType.SPECTRA: dnora_destine.spectra.ECMWF(),
        DnoraDataType.WIND: dnora_destine.wind.ECMWF(),
        DnoraDataType.ICE: dnora_destine.ice.ECMWF(),
    }
