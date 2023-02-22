# -*- coding: utf-8 -*-
import matplotlib.collections
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..misc import find_closest


def eda_plot(eda_signals, sampling_rate=None, static=True):
    """**Visualize electrodermal activity (EDA) data**

    Parameters
    ----------
    eda_signals : DataFrame
        DataFrame obtained from :func:`eda_process()`.
    sampling_rate : int
        The desired sampling rate (in Hz, i.e., samples/second). Defaults to None.
    static : bool
        If True, a static plot will be generated with matplotlib.
        If False, an interactive plot will be generated with plotly.
        Defaults to True.

    Returns
    -------
    fig
        Figure representing a plot of the processed EDA signals.

    Examples
    --------
    .. ipython:: python

      import neurokit2 as nk

      eda_signal = nk.eda_simulate(duration=30, scr_number=5, drift=0.1, noise=0, sampling_rate=250)
      eda_signals, info = nk.eda_process(eda_signal, sampling_rate=250)
      @savefig p_eda_plot1.png scale=100%
      nk.eda_plot(eda_signals)
      @suppress
      plt.close()

    See Also
    --------
    eda_process

    """
    # Determine peaks, onsets, and half recovery.
    peaks = np.where(eda_signals["SCR_Peaks"] == 1)[0]
    onsets = np.where(eda_signals["SCR_Onsets"] == 1)[0]
    half_recovery = np.where(eda_signals["SCR_Recovery"] == 1)[0]

    # Determine unit of x-axis.
    if sampling_rate is not None:
        x_label = "Seconds"
        x_axis = np.linspace(0, len(eda_signals) / sampling_rate, len(eda_signals))
    else:
        x_label = "Samples"
        x_axis = np.arange(0, len(eda_signals))

    if static:
        fig, (ax0, ax1, ax2) = plt.subplots(nrows=3, ncols=1, sharex=True)

        last_ax = fig.get_axes()[-1]
        last_ax.set_xlabel(x_label)
        plt.tight_layout(h_pad=0.2)

        # Plot cleaned and raw electrodermal activity.
        ax0.set_title("Raw and Cleaned Signal")
        fig.suptitle("Electrodermal Activity (EDA)", fontweight="bold")

        ax0.plot(x_axis, eda_signals["EDA_Raw"], color="#B0BEC5", label="Raw", zorder=1)
        ax0.plot(
            x_axis, eda_signals["EDA_Clean"], color="#9C27B0", label="Cleaned", linewidth=1.5, zorder=1
        )
        ax0.legend(loc="upper right")

        # Plot skin conductance response.
        ax1.set_title("Skin Conductance Response (SCR)")

        # Plot Phasic.
        ax1.plot(
            x_axis,
            eda_signals["EDA_Phasic"],
            color="#E91E63",
            label="Phasic Component",
            linewidth=1.5,
            zorder=1,
        )

        # Mark segments.
        risetime_coord, amplitude_coord, halfr_coord = _eda_plot_dashedsegments(
            eda_signals, ax1, x_axis, onsets, peaks, half_recovery
        )

        risetime = matplotlib.collections.LineCollection(
            risetime_coord, colors="#FFA726", linewidths=1, linestyle="dashed"
        )
        ax1.add_collection(risetime)

        amplitude = matplotlib.collections.LineCollection(
            amplitude_coord, colors="#1976D2", linewidths=1, linestyle="solid"
        )
        ax1.add_collection(amplitude)

        halfr = matplotlib.collections.LineCollection(
            halfr_coord, colors="#FDD835", linewidths=1, linestyle="dashed"
        )
        ax1.add_collection(halfr)
        ax1.legend(loc="upper right")

        # Plot Tonic.
        ax2.set_title("Skin Conductance Level (SCL)")
        ax2.plot(
            x_axis, eda_signals["EDA_Tonic"], color="#673AB7", label="Tonic Component", linewidth=1.5
        )
        ax2.legend(loc="upper right")
        return fig
    else:
        # Create interactive plot with plotly.
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

        except ImportError as e:
            raise ImportError(
                "NeuroKit error: ppg_plot(): the 'plotly'",
                " module is required when 'static' is False.",
                " Please install it first (`pip install plotly`).",
            ) from e

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("Raw and Cleaned Signal", "Skin Conductance Response (SCR)", "Skin Conductance Level (SCL)"),
        )

        # Plot cleaned and raw electrodermal activity.
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=eda_signals["EDA_Raw"],
                mode="lines",
                name="Raw",
                line=dict(color="#B0BEC5"),
                showlegend=True,
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=eda_signals["EDA_Clean"],
                mode="lines",
                name="Cleaned",
                line=dict(color="#9C27B0"),
                showlegend=True,
            ),
            row=1,
            col=1,
        )

        # Plot skin conductance response.
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=eda_signals["EDA_Phasic"],
                mode="lines",
                name="Phasic Component",
                line=dict(color="#E91E63"),
                showlegend=True,
            ),
            row=2,
            col=1,
        )

        # Mark segments.
        risetime_coord, amplitude_coord, halfr_coord = _eda_plot_dashedsegments(
            eda_signals, fig, x_axis, onsets, peaks, half_recovery, static=static
        )

        fig.add_trace(
            go.Scatter(
                x=risetime_coord[0],
                y=risetime_coord[1],
                mode="lines",
                name="Rise Time",
                line=dict(color="#FFA726", dash="dash"),
                showlegend=True,
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=amplitude_coord[0],
                y=amplitude_coord[1],
                mode="lines",
                name="SCR Amplitude",
                line=dict(color="#1976D2", dash="solid"),
                showlegend=True,
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=halfr_coord[0],
                y=halfr_coord[1],
                mode="lines",
                name="Half Recovery",
                line=dict(color="#FDD835", dash="dash"),
                showlegend=True,
            ),
            row=2,
            col=1,
        )

        # Plot skin conductance level.
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=eda_signals["EDA_Tonic"],
                mode="lines",
                name="Tonic Component",
                line=dict(color="#673AB7"),
                showlegend=True,
            ),
            row=3,
            col=1,
        )

        return fig



# =============================================================================
# Internals
# =============================================================================
def _eda_plot_dashedsegments(eda_signals, ax, x_axis, onsets, peaks, half_recovery, static=True):
    end_onset = pd.Series(
        eda_signals["EDA_Phasic"][onsets].values, eda_signals["EDA_Phasic"][peaks].index
    )

    # Rise time
    risetime_start = eda_signals["EDA_Phasic"][onsets]
    risetime_end = eda_signals["EDA_Phasic"][peaks]
    risetime_coord = np.array([list(zip(risetime_start, risetime_end))])

    # SCR Amplitude
    peak_top = eda_signals["EDA_Phasic"][peaks]
    amplitude_coord = np.array([list(zip(end_onset, peak_top))])

    # Half recovery
    peak_x_values = x_axis[peaks]
    recovery_x_values = x_axis[half_recovery]

    if static:
        # Plot with matplotlib.
        # Mark onsets, peaks, and half-recovery.
        scat_onset = ax.scatter(
            x_axis[onsets],
            eda_signals["EDA_Phasic"][onsets],
            color="#FFA726",
            label="SCR - Onsets",
            zorder=2,
        )
        scat_peak = ax.scatter(
            x_axis[peaks],
            eda_signals["EDA_Phasic"][peaks],
            color="#1976D2",
            label="SCR - Peaks",
            zorder=2,
        )
        scat_halfr = ax.scatter(
            x_axis[half_recovery],
            eda_signals["EDA_Phasic"][half_recovery],
            color="#FDD835",
            label="SCR - Half recovery",
            zorder=2,
        )

        scat_endonset = ax.scatter(x_axis[end_onset.index], end_onset.values, alpha=0)
        """
        # Rise time.
        risetime_start = scat_onset.get_offsets()
        risetime_end = scat_endonset.get_offsets()
        risetime_coord = [(risetime_start[i], risetime_end[i]) for i in range(0, len(onsets))]

        # SCR Amplitude.
        peak_top = scat_peak.get_offsets()
        amplitude_coord = [(peak_top[i], risetime_end[i]) for i in range(0, len(onsets))]

        # Half recovery.
        peak_x_values = peak_top.data[:, 0]
        recovery_x_values = x_axis[half_recovery]

        peak_list = []
        for i, index in enumerate(half_recovery):
            value = find_closest(
                recovery_x_values[i], peak_x_values, direction="smaller", strictly=False
            )
            peak_list.append(value)

        peak_index = []
        for i in np.array(peak_list):
            index = np.where(i == peak_x_values)[0][0]
            peak_index.append(index)

        halfr_index = list(range(0, len(half_recovery)))
        halfr_end = scat_halfr.get_offsets()
        halfr_start = [(peak_top[i, 0], halfr_end[x, 1]) for i, x in zip(peak_index, halfr_index)]
        halfr_coord = [(halfr_start[i], halfr_end[i]) for i in halfr_index]
        """
    else:
        # Plot with plotly.
        # Mark onsets, peaks, and half-recovery.
        ax.add_trace(
            go.Scatter(
                x=x_axis[onsets],
                y=eda_signals["EDA_Phasic"][onsets],
                mode="markers",
                name="SCR - Onsets",
                marker=dict(color="#FFA726"),
                showlegend=True,
            ),
            row=2,
            col=1,
        )
        ax.add_trace(
            go.Scatter(
                x=x_axis[peaks],
                y=eda_signals["EDA_Phasic"][peaks],
                mode="markers",
                name="SCR - Peaks",
                marker=dict(color="#1976D2"),
                showlegend=True,
            ),
            row=2,
            col=1,
        )
        ax.add_trace(
            go.Scatter(
                x=x_axis[half_recovery],
                y=eda_signals["EDA_Phasic"][half_recovery],
                mode="markers",
                name="SCR - Half recovery",
                marker=dict(color="#FDD835"),
                showlegend=True,
            ),
            row=2,
            col=1,
        )
        ax.add_trace(
            go.Scatter(
                x=x_axis[end_onset.index],
                y=end_onset.values,
                mode="markers",
                marker=dict(color="#FDD835", opacity=0),
                showlegend=False,
            )
            row=2,
            col=1,
        )
        """
        # Rise time.
        risetime_start = ax.data[0].x
        risetime_end = ax.data[3].x
        risetime_coord = [(risetime_start[i], risetime_end[i]) for i in range(0, len(onsets))]

        # SCR Amplitude.
        peak_top = ax.data[1].x
        amplitude_coord = [(peak_top[i], risetime_end[i]) for i in range(0, len(onsets))]

        # Half recovery.
        peak_x_values = peak_top
        recovery_x_values = x_axis[half_recovery]

        peak_list = []
        for i, index in enumerate(half_recovery):
            value = find_closest(
                recovery_x_values[i], peak_x_values, direction="smaller", strictly=False
            )
            peak_list.append(value)

        peak_index = []
        for i in np.array(peak_list):
            index = np.where(i == peak_x_values)[0][0]
            peak_index.append(index)

        halfr_index = list(range(0, len(half_recovery)))
        halfr_end = ax.data[2].x
        halfr_start = [(peak_top[i], halfr_end[x]) for i, x in zip(peak_index, halfr_index)]
        halfr_coord = [(halfr_start[i], halfr_end[i]) for i in halfr_index]
    """

    peak_list = []
    for i, index in enumerate(half_recovery):
        value = find_closest(
            recovery_x_values[i], peak_x_values, direction="smaller", strictly=False
        )
        peak_list.append(value)

    peak_index = []
    for i in np.array(peak_list):
        index = np.where(i == peak_x_values)[0][0]
        peak_index.append(index)

    halfr_index = list(range(0, len(half_recovery)))
    halfr_end = eda_signals["EDA_Phasic"][half_recovery]
    halfr_start = [(peak_top[i], halfr_end[x]) for i, x in zip(peak_index, halfr_index)]
    halfr_coord = [(halfr_start[i], halfr_end[i]) for i in halfr_index]

    return risetime_coord, amplitude_coord, halfr_coord
