#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import numpy as np
import xarray as xr
from datetime import datetime
from pathlib import Path
from bokeh.plotting import figure, output_file, save
from bokeh.layouts import gridplot


SCIS_DIR = Path("../scis").expanduser()
CALS_DIR = Path("../cals").expanduser()
QLOOK_DIR = Path("../qlooks").expanduser()
PLOT_TYPE = ["otfmap", "psw", "timestream"]
IF_NUM = 4
IF_LABELS = [
    "IF1: B-POL (LSB)",
    "IF2: B-POL (USB)",
    "IF3: A-POL (LSB)",
    "IF4: A-POL (USB)",
]
AXIS_LABEL_DICT = {
    "otfmap": {"x": "unknow", "y": "unknown"},
    "psw": {"x": "Frequency [GHz]", "y": "Power [K]"},
    "timestream": {"x": "Time stream", "y": "Power [a.u.]"},
}
COLORS = ["tomato", "olivedrab", "palevioletred", "steelblue"]
T_AMB = 273.
USB_FREQ = (145.7 - 0.1) + np.linspace(0., 2.5, 2**15)
LSB_FREQ = (132. - 0.1) + np.linspace(0., 2.5, 2**15)


class NetCDF2Qlook(object):
    """Create quick-look plot from NetCDF file

    Args:
        obs_id (str): ID of the observational data.
        plot_type (str): Plot type.
            Allowed values are 'otfmap', 'psw', or 'timestream'.
            Defaults to 'timestream'
        cal_id (str): ID of the calibration data.
            If you plot 'otfmap' or 'psw', you need this ID.
            Defaults to None.
        title (str): Title of quick-look plot.
            Defaults to 'Q-Look Plot'.

    Raises:
        FileNotFoundError: If doesn't exists files corresponded to ID
        TypeError: If the plot type is invalid
    """
    def __init__(self, obs_id, plot_type, cal_id=None, title="Q-Look Plot"):
        self.scis = [
            SCIS_DIR / f"xffts{obs_id}.xfftsx.0{i}.nc"
            for i in [1, 2, 3, 4]
        ]
        if not all([f.exists() for f in self.scis]):
            raise FileNotFoundError(f"Data (ID : {obs_id}) : not found")

        if not plot_type in PLOT_TYPE:
            raise TypeError(f"{plot_type} : invalid type of plot")
        self.type = plot_type

        if cal_id is not None:
            self.cals = [
                CALS_DIR / f"xffts{cal_id}.xfftsx.0{i}.nc"
                for i in [1, 2, 3, 4]
            ]
            if not all([f.exists() for f in self.cals]):
                raise FileNotFoundError(
                    f"Calibration data (ID : {cal_id}) : not found"
                )

        self.qlook = QLOOK_DIR / f"{obs_id}_{plot_type}.html"

        self.obs_id = obs_id
        self.cal_id = cal_id
        self.title = title

    def otfmap(self):
        """Plot the OTF map

        Args:
            None

        Return:
            plots (bokeh.models.layouts.Column): Plot of OTF map
        """
        print("not implemented...")
        sys.exit()

    def psw(self):
        """Plot the PSW data

        Args:
            None

        Return:
            plots (bokeh.models.layouts.Column): Plot of PSW data
        """
        Rs, ONs, OFFs = [], [], []
        for s, c in zip(self.scis, self.cals):
            with xr.open_dataset(s) as sci, xr.open_dataset(c) as cal:
                Rs.append((cal["array"] / cal["integtime"]).mean("t"))
                ONs.append(
                    (sci["array"] / sci["integtime"])[sci["bufpos"] == "ON"]
                )
                OFFs.append(
                    (sci["array"] / sci["integtime"])[sci["bufpos"] == "REF"]
                )
        # print(ONs[0])
        # print(OFFs[0])
        Tcals = [
            # T_AMB * (on - off[1:]) / (r - off[1:])
            T_AMB * (on[4:] - off) / (r - off)
            for r, on, off in zip(Rs, ONs, OFFs)
        ]

        plots = []
        for i, (t, c) in enumerate(zip(Tcals, COLORS)):
            if i == 0:
                p = figure(title=self.title, plot_width=640, plot_height=360)
            else:
                p = figure(plot_width=640, plot_height=360)

            if i == 0 or i == 2:
                p.line(LSB_FREQ, t.mean("t").values,
                    color=c, line_width=1., legend=IF_LABELS[i])
            if i == 1 or i == 3:
                p.line(USB_FREQ, t.mean("t").values,
                    color=c, line_width=1., legend=IF_LABELS[i])
            plots.append(self._create_looks(p))

        plots = gridplot([plots[0], plots[1]], [plots[2], plots[3]])
        return plots

    def timestream(self):
        """Plot the time stream data

        Args:
            None

        Return:
            plots (bokeh.models.layouts.Column): Plot of time stream data
        """
        plots = []
        for i, (s, c) in enumerate(zip(self.scis, COLORS)):
            with xr.open_dataset(s) as data:
                time = np.array(
                    [d[:-4] for d in data["date"].values],
                    "datetime64[us]",
                )
                flag = time < time[-1]
                arrays = data["array"]
                time = time[flag]
                integ_data = np.average(arrays, axis=1)[flag]
                # integ_data = arrays[:, 12000:18000].mean("array_dim0").values
                del(arrays)
                # x = np.arange(len(integ_data))

            if i == 0:
                p = figure(title=self.title, x_axis_type="datetime",
                           plot_width=640, plot_height=360)
            else:
                p = figure(x_axis_type="datetime",
                           plot_width=640, plot_height=360)
            p.line(time, integ_data, color=c,
                   line_width=1., legend=IF_LABELS[i])
            plots.append(self._create_looks(p))

        plots = gridplot([plots[0], plots[1]], [plots[2], plots[3]])
        return plots

    def save(self):
        """Save the plot

        Args:
            None

        Return:
            None
        """
        output_file(self.qlook)
        if self.type == "otfmap":
            p = self.otfmap()
        elif self.type == "psw":
            p = self.psw()
        elif self.type == "timestream":
            p = self.timestream()
        else:
            raise TypeError(f"{plot_type} : invalid type of plot")
        save(p)
        return

    def _create_looks(self, plot, power_unit="a.u."):
        """Create the looks of the plot

        Args:
            plot (bokeh.plotting.figure.Figure): Instance of the plot

        Return:
            plot (bokeh.plotting.figure.Figure): Instance of the shaped plot
        """
        plot.title.text_font_size = "16pt"
        plot.legend.location = "top_right"
        plot.legend.background_fill_alpha = 0.5
        plot.xaxis.axis_label = AXIS_LABEL_DICT[self.type]["x"]
        plot.xaxis.axis_label_text_font_size = "12pt"
        plot.xaxis.axis_label_text_font_style = "bold"
        plot.yaxis.axis_label = AXIS_LABEL_DICT[self.type]["y"]
        plot.yaxis.axis_label_text_font_size = "12pt"
        plot.yaxis.axis_label_text_font_style = "bold"
        return plot


def main():
    _usage = "python netcdf2qlook OBS_ID" \
        + " [-t --type TYPE] [-c --cal_id CAL_ID] [--title TITLE]"
    parser = argparse.ArgumentParser(
        prog="netcdf2qlook",
        usage=_usage,
        description="create Q-Look plot (Bokeh's html file)",
        add_help=True,
    )
    parser.add_argument("obs_id", type=str,
                        help="ID of the observational data")
    parser.add_argument("-t", "--type", type=str, default="timestream",
                        dest="type", choices=["otfmap", "psw", "timestream"],
                        help="type of plot ('otfmap', 'psw', 'timestream')")
    parser.add_argument("-c", "--cal_id", type=str,
                        dest="cal_id", help="ID of the calibration data")
    parser.add_argument("--title", type=str, dest="title",
                        default="Q-Look plot", help="title of plot")
    args = parser.parse_args()

    n2q = NetCDF2Qlook(args.obs_id, args.type,
                       cal_id=args.cal_id, title=args.title)
    n2q.save()
    return


if __name__ == "__main__":
    main()
