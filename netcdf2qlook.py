#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import numpy as np
import xarray as xr
from pathlib import Path
from bokeh.plotting import figure, output_file, save
from bokeh.layouts import gridplot


SCIS_DIR = Path("../scis").expanduser()
CALS_DIR = Path("../cals").expanduser()
QLOOK_DIR = Path("../qlooks").expanduser()
PLOT_TYPE = ["otfmap", "psw", "timestream"]
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
T_AMB = 273.
FREQ = (128 - 0.1) + np.linspace(0., 2.5, 2**15)


class NetCDF2Qlook(object):
    """
    """
    def __init__(self, sci_id, ptype, cal_id=None, title="Q-Look Plot"):
        self.scis = [
            SCIS_DIR / f"xffts{sci_id}.xfftsx.0{i}.nc" for i in [1, 2, 3, 4]
        ]
        if not all([f.exists() for f in self.scis]):
            raise AssertionError

        if cal_id is not None:
            self.cals = [
                CALS_DIR / f"xffts{cal_id}.xfftsx.0{i}.nc" for i in [1, 2, 3, 4]
            ]
            if not all([f.exists() for f in self.cals]):
                raise AssertionError

        if not ptype in PLOT_TYPE:
            raise AssertionError
        self.ptype = ptype

        self.sci_id = sci_id
        self.cal_id = cal_id
        self.title = title
        self.qlook = QLOOK_DIR / f"{sci_id}_{ptype}.html"

    def otfmap(self):
        """
        """
        print("unimplemented...")
        sys.exit()

    def psw(self):
        """
        """
        Rs, ONs, OFFs = [], [], []
        for s, c in zip(self.scis, self.cals):
            with xr.open_dataset(s) as sci, xr.open_dataset(c) as cal:
                Rs.append((cal["array"]/cal["integtime"]).mean("t"))
                ONs.append((sci["array"]/sci["integtime"])[sci["bufpos"]=="ON"])
                OFFs.append((sci["array"]/sci["integtime"])[sci["bufpos"]=="REF"])
        Tcals = [
            T_AMB * (on - off[1:]) / (r - off[1:])
            for r, on, off in zip(Rs, ONs, OFFs)
        ]

        plots = []
        colors = ["tomato", "olivedrab", "palevioletred", "steelblue"]
        for i, (t, c) in enumerate(zip(Tcals, colors)):
            if i == 0:
                p = figure(title=self.title, plot_width=640, plot_height=360)
            else:
                p = figure(plot_width=640, plot_height=360)
            p.line(FREQ, t.mean("t").values,
                   color=c, line_width=1., legend=IF_LABELS[i])
            plots.append(self._create_looks(p))

        plots = gridplot([plots[0], plots[1]], [plots[2], plots[3]])
        return plots

    def timestream(self):
        """
        """
        plots = []
        colors = ["tomato", "olivedrab", "palevioletred", "steelblue"]
        for i, (s, c) in enumerate(zip(self.scis, colors)):
            with xr.open_dataset(s) as data:
                _arrays = data["array"]
                _integ_data = np.average(_arrays, axis=1)
                # _integ_data = _arrays[:, 8000:24000].mean("array_dim0").values
                _x = np.arange(len(_integ_data))

            if i == 0:
                p = figure(title=self.title, plot_width=640, plot_height=360)
            else:
                p = figure(plot_width=640, plot_height=360)
            p.line(_x, _integ_data,
                   color=c, line_width=1., legend=IF_LABELS[i])
            plots.append(self._create_looks(p))

        plots = gridplot([plots[0], plots[1]], [plots[2], plots[3]])
        return plots

        # with xr.open_dataset(self.scis[1]) as data:
        #     _arrays = data["array"]
        #     _integ_data = np.average(_arrays, axis=1)
        #     _x = np.arange(len(_integ_data))
        #
        # p = figure(title=self.title, plot_width=960, plot_height=540)
        # p.line(_x, _integ_data, legend="Timestream",
        #        line_color="midnightblue", line_width=1.)
        # return self._create_looks(p)
        #
    def save(self):
        """
        """
        output_file(self.qlook)
        if self.ptype == "otfmap":
            p = self.otfmap()
        elif self.ptype == "psw":
            p = self.psw()
        elif self.ptype == "timestream":
            p = self.timestream()
        else:
            raise AssertionError
        save(p)

    def _create_looks(self, plot, power_unit="a.u."):
        """whwh
        """
        plot.title.text_font_size = "16pt"
        plot.legend.location = "top_right"
        plot.legend.background_fill_alpha = 0.5
        plot.xaxis.axis_label = AXIS_LABEL_DICT[self.ptype]["x"]
        plot.xaxis.axis_label_text_font_size = "12pt"
        plot.xaxis.axis_label_text_font_style = "bold"
        plot.yaxis.axis_label = AXIS_LABEL_DICT[self.ptype]["y"]
        plot.yaxis.axis_label_text_font_size = "12pt"
        plot.yaxis.axis_label_text_font_style = "bold"
        return plot


def main():
    """
    """
    usage = "python netcdf2qlook.py SCI, CAL PTYPE [--title <title>] [--help]"
    parser = argparse.ArgumentParser(
        prog="netcdf2qlook",
        usage=usage,
        description="create Q-look plot (Bokeh html file)",
        add_help=True,
    )
    parser.add_argument("sci", help="ID of the science data")
    parser.add_argument("ptype", type=str, default="timestream",
                        choices=["otfmap", "psw", "timestream"],
                        help="type of plot ('otfmap', 'psw', 'timestream')")
    parser.add_argument("-c", "--calibration", type=str,
                        dest="cal", help="ID of the calibration data")
    parser.add_argument("-t", "--title", type=str,
                        dest="title", help="title of plot")
    args = parser.parse_args()

    if args.title:
        n2q = NetCDF2Qlook(args.sci, args.ptype,
                           cal_id=args.cal, title=args.title)
    else:
        n2q = NetCDF2Qlook(args.sci, args.ptype, cal_id=args.cal)

    n2q.save()
    return


if __name__ == "__main__":
    main()
