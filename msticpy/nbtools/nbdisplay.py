# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Module for common display functions."""
from datetime import datetime
from typing import Any, Mapping, Union

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from bokeh.io import output_notebook, show
from bokeh.models import (
    ColumnDataSource,
    DatetimeTickFormatter,
    HoverTool,
    Label,
    Legend,
    RangeTool,
)
from bokeh.palettes import viridis
from bokeh.plotting import figure, reset_output
from bokeh.layouts import column
from IPython.core.display import HTML, display
from IPython.display import Javascript

from .._version import VERSION
from .security_alert import SecurityAlert
from .utility import export

__version__ = VERSION
__author__ = "Ian Hellen"


@export
def display_alert(
    alert: Union[Mapping[str, Any], SecurityAlert], show_entities: bool = False
):
    """
    Display a Security Alert.

    Parameters
    ----------
    alert : Union[Mapping[str, Any], SecurityAlert]
        The alert to display as Mapping (e.g. pd.Series)
        or SecurityAlert
    show_entities : bool, optional
        Whether to display entities (the default is False)

    """
    if isinstance(alert, SecurityAlert):
        display(HTML(alert.to_html(show_entities=False)))
        if show_entities:
            for entity in alert.entities:
                print(entity)
        return

    # Display subset of raw properties
    if isinstance(alert, pd.Series):
        entity = alert["CompromisedEntity"] if "CompromisedEntity" in alert else ""
        title = """
            <h3>Alert: '{name}'</h3><br>time=<b>{start}</b>,
            entity=<b>{entity}</b>, id=<b>{id}</b>
            """.format(
            start=alert["StartTimeUtc"],
            name=alert["AlertDisplayName"],
            entity=entity,
            id=alert["SystemAlertId"],
        )
        display(HTML(title))
        display(pd.DataFrame(alert))
    else:
        raise ValueError("Unrecognized alert object type " + str(type(alert)))


def _print_process(process_row: pd.Series, fmt: str = "html") -> str:
    """
    Format individual process item as text or html.

    Parameters
    ----------
    process_row : pd.Series
        Process series
    fmt : str, optional
        Format ('txt' or 'html')
        (the default is ' html')

    Returns
    -------
    str
        Formatted process summary.

    """
    if process_row.NodeRole == "parent":
        if process_row.Level > 1:
            level = 0
        else:
            level = 1
    elif process_row.NodeRole == "source":
        level = 2
    elif process_row.NodeRole == "child":
        level = 3 + process_row.Level
    else:
        level = 2

    px_spaces = 20 * level * 2
    txt_spaces = " " * (4 * int(level))

    font_col = "red" if process_row.NodeRole == "source" else "white"

    if fmt.lower() == "html":
        l1_span = f'<span style="color:{font_col};font-size:90%">'
        line1_w_tmplt = (
            l1_span
            + "[{NodeRole}:lev{Level}] {TimeGenerated} "
            + "<b>{NewProcessName}</b> "
            + "[PID: {NewProcessId}, "
            + "SubjSess:{SubjectLogonId}, "
            + "TargSess:{TargetLogonId}]"
        )
        line2_w_tmplt = '(Cmdline: "{CommandLine}") [Account: {Account}]</span>' ""
        output_tmplt = (
            f'<div style="margin-left:{px_spaces}px">' + f"{{line1}}<br>{{line2}}</div>"
        )
        line1_lx_tmplt = (
            l1_span
            + "[{NodeRole}:lev{Level}] {TimeGenerated} "
            + "<b>{NewProcessName}</b> "
            + "[PID: {NewProcessId}, "
            + "PPID: {ProcessId}]"
        )
        line2_lx_tmplt = '(Cmdline: "{CommandLine}") [Path: {cwd}]</span>' ""
        output_tmplt = (
            f'<div style="margin-left:{px_spaces}px">' + f"{{line1}}<br>{{line2}}</div>"
        )
    else:
        line1_w_tmplt = (
            "[{NodeRole}:lev{Level}] {TimeGenerated} "
            + "{NewProcessName} "
            + "[PID: {NewProcessId}, "
            + "SubjSess:{SubjectLogonId}, "
            + "TargSess:{TargetLogonId}]"
        )
        line2_w_tmplt = '(Cmdline: "{CommandLine}") [Account: {Account}]'
        line1_lx_tmplt = (
            "[{NodeRole}:lev{Level}] {TimeGenerated} "
            + "{NewProcessName} "
            + "[PID: {NewProcessId}, "
            + "PPID: {ProcessId}]"
        )
        line2_lx_tmplt = '(Cmdline: "{CommandLine}") [Path: {cwd}]'
        output_tmplt = f"\n{txt_spaces}{{line1}}\n{txt_spaces}{{line2}}"
    rows = process_row.to_dict()
    if "TargetLogonId" in rows:
        line1 = line1_w_tmplt.format(**(rows))
        line2 = line2_w_tmplt.format(**(rows))
    else:
        line1 = line1_lx_tmplt.format(**(rows))
        line2 = line2_lx_tmplt.format(**(rows))

    return output_tmplt.format(line1=line1, line2=line2)


def format_process_tree(process_tree: pd.DataFrame, fmt: str = "html"):
    """
    Display process tree data frame.

    Parameters
    ----------
    process_tree : pd.DataFrame
        Process tree DataFrame
    fmt : str, optional
        Format ('txt' or 'html')
        (the default is ' html')

    Returns
    -------
    str
        Formatted process tree.

    The display module expects the columns NodeRole and Level to
    be populated. NoteRole is one of: 'source', 'parent', 'child'
    or 'sibling'. Level indicates the 'hop' distance from the 'source'
    node.

    """
    if "TimeCreatedUtc" in process_tree.index:
        tree = process_tree.sort_values(by=["TimeCreatedUtc"], ascending=True)
    else:
        tree = process_tree.sort_values(by=["TimeGenerated"], ascending=True)

    if fmt.lower() == "html":
        out_string = "<h3>Process tree:</h3>"
    else:
        out_string = "Process tree:"
        out_string = out_string + "\n" + "_" * len(out_string)

    for _, line in tree.iterrows():
        out_string += _print_process(line, fmt)

    return out_string


@export
def display_process_tree(process_tree: pd.DataFrame):
    """
    Display process tree data frame. (Deprecated).

    Parameters
    ----------
    process_tree : pd.DataFrame
        Process tree DataFrame

    The display module expects the columns NodeRole and Level to
    be populated. NoteRole is one of: 'source', 'parent', 'child'
    or 'sibling'. Level indicates the 'hop' distance from the 'source'
    node.

    """
    display(HTML(format_process_tree(process_tree)))


@export
def exec_remaining_cells():
    """Execute all cells below currently selected cell."""
    Javascript("Jupyter.notebook.execute_cells_below()")


@export
# pylint: disable=too-many-arguments
def draw_alert_entity_graph(
    nx_graph: nx.Graph,
    font_size: int = 12,
    height: int = 15,
    width: int = 15,
    margin: float = 0.3,
    scale: int = 1,
):
    """
    Draw networkX graph with matplotlib.

    Parameters
    ----------
    nx_graph : nx.Graph
        The NetworkX graph to draw
    font_size : int, optional
        base font size (the default is 12)
    height : int, optional
        Image height (the default is 15)
    width : int, optional
        Image width (the default is 15)
    margin : float, optional
        Image margin (the default is 0.3)
    scale : int, optional
        Position scale (the default is 1)

    """
    alert_node = [
        n
        for (n, node_type) in nx.get_node_attributes(nx_graph, "node_type").items()
        if node_type == "alert"
    ]
    entity_nodes = [
        n
        for (n, node_type) in nx.get_node_attributes(nx_graph, "node_type").items()
        if node_type == "entity"
    ]

    # now draw them in subsets  using the `nodelist` arg
    plt.rcParams["figure.figsize"] = (width, height)

    plt.margins(x=margin, y=margin)

    pos = nx.kamada_kawai_layout(nx_graph, scale=scale, weight="weight")
    nx.draw_networkx_nodes(
        nx_graph, pos, nodelist=alert_node, node_color="red", alpha=0.5, node_shape="o"
    )
    nx.draw_networkx_nodes(
        nx_graph,
        pos,
        nodelist=entity_nodes,
        node_color="green",
        alpha=0.5,
        node_shape="s",
        s=200,
    )
    nlabels = nx.get_node_attributes(nx_graph, "description")
    nx.relabel_nodes(nx_graph, nlabels)
    nx.draw_networkx_labels(nx_graph, pos, nlabels, font_size=font_size)
    nx.draw_networkx_edges(nx_graph, pos)
    elabels = nx.get_edge_attributes(nx_graph, "description")
    nx.draw_networkx_edge_labels(
        nx_graph, pos, edge_labels=elabels, font_size=font_size * 2 / 3, alpha=0.6
    )


# Constants
_WRAP = 50
_WRAP_CMDL = "WrapCmdl"


# Need to refactor this to allow multiple data sets.
# pylint: disable=too-many-arguments, too-many-locals
# pylint: disable=too-many-statements, too-many-branches
@export  # noqa: C901, MC0001
def display_timeline(
    data: dict, alert: SecurityAlert = None, title: str = None, height: int = 300
):
    """

    Display a timeline of events.

    Parameters
    ----------
    data : dict
        Data points to plot on the timeline.
            Need to contain:
                Key - Name of data type to be displayed in legend
                Value - dict of data containing:
                    data : pd.DataFrame
                        Data to plot
                    time_column : str
                        Name of the timestamp column
                    source_columns : list
                        List of source columns to use in tooltips
                    color: str
                        Color of datapoints for this data
    alert : SecurityAlert, optional
        Input alert (the default is None)
    title : str, optional
        Title to display (the default is None)
    height : int, optional
        the height of the plot figure (under 300 limits access
        to Bokeh tools)(the default is 300)

    """
    reset_output()
    output_notebook()

    # Take each item that is passed in data and fill in blanks and add a y_index
    y_index = 1
    for key, val in data.items():
        val["data"]["y_index"] = y_index
        y_index += 1
        if not val["source_columns"]:
            val["source_columns"] = ["NewProcessName", "EventID", "CommandLine"]
        if val["time_column"] not in val["source_columns"]:
            val["source_columns"].append(val["time_column"])
        if "y_index" not in val["source_columns"]:
            val["source_columns"].append("y_index")
        if "CommandLine" in val["source_columns"]:
            graph_df = val["data"][val["source_columns"]].copy()
            graph_df[_WRAP_CMDL] = graph_df.apply(
                lambda x: _wrap_text(x.CommandLine, _WRAP), axis=1
            )
        else:
            graph_df = val["data"][val["source_columns"]].copy()
        val["source"] = ColumnDataSource(graph_df)

    # build the tool tips from columns of the first dataset
    prim_data = list(data.keys())[0]
    excl_cols = [data[prim_data]["time_column"], "CommandLine", "y_index"]
    tool_tip_items = [
        (f"{col}", f"@{col}")
        for col in data[prim_data]["source_columns"]
        if col not in excl_cols
    ]
    if _WRAP_CMDL in data[prim_data]["data"]:
        tool_tip_items.append(("CommandLine", f"@{_WRAP_CMDL}"))
    hover = HoverTool(tooltips=tool_tip_items, formatters={"Tooltip": "printf"})

    if not title:
        title = "Event Timeline"
    else:
        title = "Timeline {}".format(title)

    plot = figure(
        x_range=(
            data[prim_data]["data"][data[prim_data]["time_column"]][
                int(len(data[prim_data]["data"].index) * 0.33)
            ],
            data[prim_data]["data"][data[prim_data]["time_column"]][
                int(len(data[prim_data]["data"].index) * 0.66)
            ],
        ),
        min_border_left=50,
        plot_height=height,
        plot_width=900,
        x_axis_label="Event Time",
        x_axis_type="datetime",
        x_minor_ticks=10,
        tools=[hover, "xwheel_zoom", "box_zoom", "reset", "save", "xpan"],
        title=title,
    )
    plot.yaxis.visible = False
    # Create plot bar to act as as range selector
    select = figure(
        title="Drag the middle and edges of the selection box to change the range above",
        plot_height=130,
        plot_width=900,
        x_axis_type="datetime",
        y_axis_type=None,
        tools="",
        toolbar_location=None,
    )
    for key, val in data.items():
        select.circle(
            x=val["time_column"], y="y_index", color=val["color"], source=val["source"]
        )
    range_tool = RangeTool(x_range=plot.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    select.toolbar.active_multi = range_tool

    # Tick formatting for different zoom levels
    # '%H:%M:%S.%3Nms
    tick_format = DatetimeTickFormatter()
    tick_format.days = ["%m-%d %H:%M"]
    tick_format.hours = ["%H:%M:%S"]
    tick_format.minutes = ["%H:%M:%S"]
    tick_format.seconds = ["%H:%M:%S"]
    tick_format.milliseconds = ["%H:%M:%S.%3N"]
    plot.xaxis[0].formatter = tick_format

    for key, val in data.items():
        plot.circle(
            x=val["time_column"],
            y="y_index",
            color=val["color"],
            alpha=0.5,
            size=10,
            source=val["source"],
            legend=key,
        )

    plot.legend.location = "top_left"
    plot.legend.click_policy = "hide"

    if alert is not None:
        x_alert_label = pd.Timestamp(alert["StartTimeUtc"])
        plot.line(x=[x_alert_label, x_alert_label], y=[0, y_index + 1])
        alert_label = Label(
            x=x_alert_label,
            y=0,
            y_offset=10,
            x_units="data",
            y_units="data",
            text="< Alert time",
            render_mode="css",
            border_line_color="red",
            border_line_alpha=1.0,
            background_fill_color="white",
            background_fill_alpha=1.0,
        )

        plot.add_layout(alert_label)

        print("Alert start time = ", alert["StartTimeUtc"])

    show(column(plot, select))


def _wrap_text(source_string, wrap_len):
    if len(source_string) <= wrap_len:
        return source_string
    out_string = ""
    input_parts = source_string.split()
    out_line = ""
    for part in input_parts:
        if len(part) > wrap_len:
            if out_line:
                out_string += out_line + "\n"
                out_line = ""
            out_line = part[0:wrap_len] + "..."
        else:
            if out_line:
                out_line += " " + part
            else:
                out_line = part
            if len(out_line) > wrap_len:
                out_string += out_line + "\n"
                out_line = ""
    return out_string


@export  # noqa: C901, MC0001
def display_timeline_multi(
    data: pd.DataFrame,
    group_by: str,
    sort_by: str = None,
    ref_time: datetime = None,
    title: str = None,
    time_column: str = "TimeGenerated",
    legend_column: str = None,
    source_columns: list = None,
):
    """
    Display a timeline of events.

    Parameters
    ----------
    data : pd.DataFrame
        Input DataFrame
    group_by : str
        The column to group timelines on
    ref_time : datetime, optional
        Input reference line to display (the default is None)
    title : str, optional
        Title to display (the default is None)
    time_column : str, optional
        Name of the timestamp column
        (the default is 'TimeGenerated')
    legend_column : str, optional
        Name of the column used to generate the legend lables
        (the default is None/no legend)
    source_columns : list
        List of source columns to use in tooltips
        (the default is None)

    """
    reset_output()
    output_notebook()

    # create group frame so that we can color each group separately
    if not sort_by:
        sort_by = group_by
    group_count = (
        data[[group_by, time_column]]
        .groupby(group_by)
        .count()
        .sort_values(sort_by)
        .reset_index()
        .rename(columns={time_column: "count"})
    )
    group_count["y_index"] = group_count.index

    colors = viridis(len(group_count))
    group_count["color"] = group_count.apply(lambda x: colors[x.y_index], axis=1)

    # If the time column not explicity specified in source_columns, add it
    if not source_columns:
        source_columns = []
    if time_column not in source_columns:
        source_columns.append(time_column)

    # re-join with the original data
    graph_df = data.merge(group_count, on=group_by)[
        list(set(source_columns + [group_by, "y_index", "color"]))
    ]

    # build the tool tips from columns (excluding these)
    excl_cols = [time_column]
    tool_tip_items = [
        (f"{col}", f"@{col}") for col in source_columns if col not in excl_cols
    ]
    hover = HoverTool(
        tooltips=tool_tip_items,
        formatters={"Tooltip": "printf"}
        # display a tooltip whenever the cursor is vertically in line with a glyph
        # ,mode='vline'
    )

    if not title:
        title = "Event Timeline"
    else:
        title = "Timeline {}".format(title)

    ht_per_row = 40
    if len(group_count) > 15:
        ht_per_row = 25
    plot_height = max(ht_per_row * len(group_count), 300)

    # tools = 'pan, box_zoom, wheel_zoom, reset, undo, redo, save, hover'
    plot = figure(
        min_border_left=50,
        plot_height=plot_height,
        plot_width=1200,
        x_axis_label="Event Time",
        x_axis_type="datetime",
        x_minor_ticks=10,
        tools=[hover, "pan", "xwheel_zoom", "box_zoom", "reset"],
        toolbar_location="above",
        title=title,
    )
    plot.yaxis.visible = True
    y_labels = {
        idx: str(lbl)
        for idx, lbl in group_count[[group_by]].to_dict()[group_by].items()
    }
    plot.yaxis.major_label_overrides = y_labels
    plot.ygrid.minor_grid_line_color = "navy"
    plot.ygrid.minor_grid_line_alpha = 0.3
    plot.xgrid.minor_grid_line_color = "navy"
    plot.xgrid.minor_grid_line_alpha = 0.3

    # Tick formatting for different zoom levels
    # '%H:%M:%S.%3Nms
    tick_format = DatetimeTickFormatter()
    tick_format.days = ["%m-%d %H:%M"]
    tick_format.hours = ["%H:%M:%S"]
    tick_format.minutes = ["%H:%M:%S"]
    tick_format.seconds = ["%H:%M:%S"]
    tick_format.milliseconds = ["%H:%M:%S.%3N"]

    plot.xaxis[0].formatter = tick_format

    # plot groups individually so that we can create an interactive legend
    legend_items = []
    for _, group_id in group_count[group_by].items():
        row_source = ColumnDataSource(graph_df[graph_df[group_by] == group_id])
        p_series = plot.diamond(
            x=time_column,
            y="y_index",
            color="color",
            alpha=0.5,
            size=10,
            source=row_source,
        )
        if legend_column:
            legend_label = graph_df[graph_df[group_by] == group_id][legend_column].iloc[
                0
            ]
            legend_items.append((legend_label, [p_series]))

    # Create the legend box outside of the plot area
    if legend_column:
        ext_legend = Legend(
            items=legend_items,
            location="center",
            click_policy="hide",
            label_text_font_size="8pt",
        )
        plot.add_layout(ext_legend, "right")

    # if we have a reference time, plot the time as a line
    if ref_time is not None:
        ref_label_tm = pd.Timestamp(ref_time)
        plot.line(x=[ref_label_tm, ref_label_tm], y=[0, len(group_count)])
        ref_label = Label(
            x=ref_label_tm,
            y=0,
            y_offset=10,
            x_units="data",
            y_units="data",
            text="< Ref time",
            render_mode="css",
            border_line_color="red",
            border_line_alpha=1.0,
            background_fill_color="white",
            background_fill_alpha=1.0,
        )

        plot.add_layout(ref_label)

    show(plot)


# Constants for Windows logon
_WIN_LOGON_TYPE_MAP = {
    0: "Unknown",
    2: "Interactive",
    3: "Network",
    4: "Batch",
    5: "Service",
    7: "Unlock",
    8: "NetworkCleartext",
    9: "NewCredentials",
    10: "RemoteInteractive",
    11: "CachedInteractive",
}
_WINDOWS_SID = {
    "S-1-0-0": "Null SID",
    "S-1-5-18": "LOCAL_SYSTEM",
    "S-1-5-19": "LOCAL_SERVICE",
    "S-1-5-20": "NETWORK_SERVICE",
}
_ADMINISTRATOR_SID = "500"
_GUEST_SID = "501"
_DOM_OR_MACHINE_SID = "S-1-5-21"


@export
def display_logon_data(
    logon_event: pd.DataFrame, alert: SecurityAlert = None, os_family: str = None
):
    """
    Display logon data for one or more events.

    Parameters
    ----------
    logon_event : pd.DataFrame
        Dataframe containing one or more logon events
    alert : SecurityAlert, optional
        obtain os_family from the security alert
        (the default is None)
    os_family : str, optional
         explicitly specify os_family (Linux or Windows)
         (the default is None)

    """
    if not os_family:
        os_family = alert.os_family if alert else "Windows"

    for _, logon_row in logon_event.iterrows():
        print("### Account Logon")
        print("Account: ", logon_row["TargetUserName"])
        print("Account Domain: ", logon_row["TargetDomainName"])
        print("Logon Time: ", logon_row["TimeGenerated"])

        if os_family == "Windows":
            logon_type = logon_row["LogonType"]
            logon_desc_idx = logon_type
            if logon_type not in _WIN_LOGON_TYPE_MAP:
                logon_desc_idx = 0
            print(
                f"Logon type: {logon_type} ", f"({_WIN_LOGON_TYPE_MAP[logon_desc_idx]})"
            )

        account_id = logon_row.TargetUserSid
        print("User Id/SID: ", account_id)
        if os_family == "Windows":
            _print_sid_info(account_id)
        else:
            print("Audit user: ", logon_row["audit_user"])

        session_id = logon_row["TargetLogonId"]
        print(f"Session id '{session_id}'", end="  ")
        if session_id in ["0x3e7", "-1"]:
            print("System logon session")

        print()
        domain = logon_row["SubjectDomainName"]
        if not domain:
            subj_account = logon_row.SubjectUserName
        else:
            subj_account = f"{domain}/{logon_row.SubjectUserName}"
        print("Subject (source) account: ", subj_account)

        print("Logon process: ", logon_row["LogonProcessName"])
        print("Authentication: ", logon_row["AuthenticationPackageName"])
        print("Source IpAddress: ", logon_row["IpAddress"])
        print("Source Host: ", logon_row["WorkstationName"])
        print("Logon status: ", logon_row["Status"])
        print()


def _print_sid_info(sid):
    if sid in _WINDOWS_SID:
        print("    SID {} is {}".format(sid, _WINDOWS_SID[sid]))
    elif sid.endswith(_ADMINISTRATOR_SID):
        print("    SID {} is administrator".format(sid))
    elif sid.endswith(_GUEST_SID):
        print("    SID {} is guest".format(sid))
    if sid.startswith(_DOM_OR_MACHINE_SID):
        print("    SID {} is local machine or domain account".format(sid))
