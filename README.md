# dnora-destine
Add-on to dnora: Access to DestinE weather products

# Quick Installation

```shell
$ conda create -n dnora_destine python=3.9
$ conda activate dnora_destine
$ python -m pip install dnora_destine 
```

# Minimal example

Download boundary spectra (JONSWAP spectra determined from parameters), wind and ice. Write output files for WAVEWATCH III.

```python
import dnora as dn
import dnora_destine as dnd

grid = dn.grid.EMODNET(
    lon=(5.65, 6.05),
    lat=(68.00, 69.55),
    name="SmallTestDomain",
)
grid.set_spacing(dm=1000)
grid.import_topo()
grid.mesh_grid()
grid.set_boundary_points(dn.grid.mask.Edges(edges=["N", "W", "S", "E"]))

# Data is not saved, so update dates to be close to todays date
model = dnd.modelrun.ECMWF(grid, year=2025, month=8, day=26)
model.import_spectra()
model.import_wind()
model.import_ice()

exporter = dn.export.WW3(model)
exporter.export_grid()
exporter.export_wind()
exporter.export_spectra()
exporter.export_ice()

exe = dn.executer.WW3(model)
exe.write_grid_file()
exe.write_wind_file()
exe.write_ice_file()
exe.write_spectra_file()
exe.write_input_file()
```