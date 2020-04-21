import geopandas as gpd
import pandas as pd
import json, urllib
from functions import *
from math import pi
from os.path import dirname, join
from bokeh.io import show, curdoc
from bokeh.models import (CDSView, ColorBar, ColumnDataSource, RadioButtonGroup, Div, Button, OpenURL,
                          CustomJS, CustomJSFilter,
                          GeoJSONDataSource, HoverTool, TapTool,
                          LogColorMapper, LinearColorMapper, DatetimeTickFormatter, NumeralTickFormatter)
from bokeh.models.widgets import DataTable, TableColumn, TextEditor, HTMLTemplateFormatter
from bokeh.layouts import column, row, widgetbox, gridplot, layout
from bokeh.palettes import brewer
from bokeh.themes import built_in_themes
from bokeh.plotting import figure,output_file, save

# Geopandas stuffs needed for plotting borders++
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
cities = gpd.read_file(gpd.datasets.get_path('naturalearth_cities'))

# Get and parse Johns Hopkins daily Covid-data. Parse todays date from Norway entry (doesn't matter)
JHcovidurl = "https://pomber.github.io/covid19/timeseries.json"
jhdict = json.loads(urllib.request.urlopen(JHcovidurl).read())
date = jhdict['Norway'][-1]['date']

# Prune JH dict / Fix syntactic differences between geopandas country-id and JH covid country-id Discard leftovers.
jhdict = fix_JH_dict(world, jhdict)

# Merge Geopandas data and todays JH covid data
world = merge_today(world, jhdict)

# Adds a column 'flags', which is just 'country' with all spaces replaced with dashes (for filenames in tooltip to work)
world = add_flags(world)

# Put rest of JH covid data into dict -> dataframe
stats = format_graph_stats(jhdict)

# Parse metadata from s1 (local, v1, v1.1 etc. Leave commented for easy trouble shooting)
#metadataurl = "current.tsv"
#metadataurl = "https://s1.sfb.uit.no/public/mar/CoronaDB/Metadatabase/SarsCoV2DB.v1/SarsCoV2DB_2020-04-14.tsv"
metadataurl = "https://s1.sfb.uit.no/public/mar/SarsCoV2DB/Metadatabase/current.tsv"

# Change this to url from s1 when ready
metadata = pd.read_csv(metadataurl, sep="\t")

# Map number of current available datasets to the world df in its own column 'datasets'. Provide a dict with rename_mapper to fix typos in country names
world = merge_datasets(world, metadata)

# Create JSON geodatasource from merged geopandas data / JHopkins daily data
worldgeosource = GeoJSONDataSource(geojson = world.to_json())
citiesgeosource = GeoJSONDataSource(geojson = cities.to_json())

# Function to make radio buttons update world map based on click
def update_radio_buttons(active):
    # Map active list indices to pandas column to be plotted and chosen color
    color_by = {
            0: ["confirmed", "Confirmed Infections", "Oranges"],
            1: ["recovered", "Confirmed Recoveries", "Greens"],
            2: ["deaths", "Confirmed Deaths", "Reds"],
            3: ["datasets", "Datasets", "Purples"]}

    view = color_by[active][0]
    infix = color_by[active][1]
    palette = color_by[active][2]

    # Update wmap with selected view and palette
    dashboard.children[2].children[0] = draw_wmap(view, infix, palette)

# Main world map renderer. 
def draw_wmap(view, infix, palette):

    # Define color palettes
    palette = brewer[palette][8]
    palette = palette[::-1] # reverse order of colors so higher values have darker colors

    # Get max infected. LogColorMapper maps numbers from a range into a sequence of colors. 0 -> max_infected. Use LinearColorMapper for datasets.
    max_value = world[view].max()
    
    if view == 'datasets':
        palette = palette[2:]
        color_mapper = LinearColorMapper(palette = palette, low = 0, high = 1)
    else:
        color_mapper = LogColorMapper(palette = palette, low = 1, high = max_value)

    # Create figure object.
    titlestring = "Covid19 {} world wide, as of {}. Statistics are updated on a daily basis from the Johns Hopkins Data Repository".format(infix, date)
    wmap = figure(title = titlestring,
            plot_height = 600,
            plot_width = 1200,
            toolbar_location = None,
            tools = 'pan, wheel_zoom, reset, tap')

    wmap.xgrid.grid_line_color = None
    wmap.ygrid.grid_line_color = None
    wmap.axis.visible = False

    # Add countries patch renderer.
    countries = wmap.patches('xs','ys', source = worldgeosource,
        fill_color = {'field': view,'transform': color_mapper},
        line_color = 'gray',
        line_width = 0.4,
        fill_alpha = 1)

    # Add hover tool
    tooltips = open(join(dirname(__file__), "tooltips.html"), "r")
    wmap.add_tools(HoverTool(renderers = [countries],
        tooltips = tooltips.read()))
    tooltips.close()

    # When ever a country is selected, run update_bottom() to update graph and table
    worldgeosource.selected.on_change('indices', update_graph_table)

    return wmap

### Graph
# Main update function for any clicks on countries. Uses taptool from wmap
def update_graph_table(attr, old, new):
    # Show world (all) if nothing selected, make list of selected countries if something is selected
    if not new:
        countries = ['World']
    else:
        countries = [str(world['country'].iat[i]) for i in new]
    #print(countries)
    
    # Update graph and table with seq data based on selected countries from wmap
    dashboard.children[4].children[0] = update_graph(countries)
    dashboard.children[4].children[1] = update_table(countries)

# Main graph draw function. 
def update_graph(countries):
    graph_palette = brewer['RdYlGn'][9]
    graph = figure(plot_height = 400,
            plot_width = 600,
            x_axis_type='datetime',
            toolbar_location = None,
            tools = 'pan, wheel_zoom, box_zoom, reset')
    graph.xaxis.formatter=DatetimeTickFormatter(
            hours=["%d %B %Y"],
            days=["%d %B %Y"],
            months=["%d %B %Y"],
            years=["%d %B %Y"],)
    graph.xaxis.major_label_orientation = pi/4
    graph.yaxis.formatter.use_scientific = False
    graph.yaxis.formatter=NumeralTickFormatter(format="0 a")
    #graph.legend.location = (100,100)
    if len(countries) == 1:
        graph.title.text = "Covid19 statistics for: {}".format(", ".join(countries))
    else:
        graph.title.text = "Covid19 statistics for: {} selected countries".format(str(len(countries)))
    
    # If more than one country
    data = ''
    data = stats[countries[0]]
    if countries[1:]:
        for country in countries[1:]:
            data['confirmed'] += stats[country]['confirmed']
            data['deaths'] += stats[country]['deaths']
            data['recovered'] += stats[country]['recovered']
    # Plot summed counts
    data = ColumnDataSource(data)
    for line, color in zip(['confirmed', 'deaths', 'recovered'],[graph_palette[4], graph_palette[8], graph_palette[1]]):
        graph.circle(x='date', y=line, source=data, legend=str(line).title(), color=color)
    graph.legend.location = "top_left"
    graph_tooltips = [
            ('Confirmed','@confirmed'),
            ('Recovered', '@recovered'),
            ('Dead','@deaths')]
    graph.add_tools(HoverTool(tooltips=graph_tooltips))
    return graph

# Create view table
def update_table(countries):
    # If not all (world), filter entries based on current country selection
    if 'World' not in countries:
        table_data = metadata[metadata.isolation_country.str.contains('|'.join(countries))]
    else:
        table_data = metadata
    # Max rows (so that height of table looks ok)
    table_data = table_data.sort_values('isolation_country')

    table_columns = [
            TableColumn(field="cdb_id", title="CoronaDB ID"),
            TableColumn(field="isolation_country", title="Country"),
            TableColumn(field="genbank_accession", title="Genbank Accession"),
            ]

    table_datasource = ColumnDataSource(table_data)
    annotation_table = DataTable(source=table_datasource, columns=table_columns, width=600)
    
    # Whenever something is clicked, run callbackfunction to navigate to external pages++ etc.
    cb = CustomJS(args=dict(source=table_datasource), code="""
        var cdbentry = source.data['cdb_id'][cb_obj.indices[0]];
        var url = 'https://covid19.sfb.uit.no/corona-db/#/records/'.concat(cdbentry);
        window.open(url,"_blank");
    """)
    table_datasource.selected.js_on_change('indices', cb)
    # Download buttons (Options: ‘default’, ‘primary’, ‘success’, ‘warning’, ‘danger’, ‘link’)
    #dlselbutton = Button(label="Download metadata (tsv)", button_type="primary")
    #dlselbutton.on_click(lol)
    #dlselbutton.js_on_click(CustomJS(args=dict(source=table_datasource.data),code=open(join(dirname(__file__), "download_tsv.js")).read()))
    #funcbutton2 = Button(label="Download sequences (Nuc, fasta)", button_type="success", disabled=True)
    #funcbutton3 = Button(label="Download sequences (Prot, fasta)", button_type="success")
    #funcbutton3.callback = CustomJS(args=dict(source=csv_download.data, seqs=seqs),code=open(join(dirname(__file__), "download_protseq.js")).read())
    #funcbuttons = row(funcbutton1, funcbutton2, funcbutton3)
    #return column([dlselbutton, annotation_table])
    return annotation_table

### Header html
header = Div(text=open(join(dirname(__file__), "header.html")).read(), width=1200, sizing_mode="stretch_width")

### Divider html (Below wmap, above graph and table)
divider = Div(text=open(join(dirname(__file__), "divider.html")).read(), width=1200, sizing_mode="stretch_width")

### Radiobuttons
buttons = RadioButtonGroup(
        labels=["Color by Confirmed Infections", "Color by Recoveries", "Color by Deaths", "Color by Available Datasets"],
        active=0)

buttons.on_click(update_radio_buttons)

######## Put it all together
dashboard = layout(children=[
    [header],
    [buttons],
    [draw_wmap("confirmed", "Confirmed Infections", "Oranges")],
    [divider],
    [update_graph(['World']), update_table(['World'])]],
    sizing_mode='fixed',
    )

curdoc().add_root(dashboard)
curdoc().theme = 'dark_minimal'
#curdoc().theme = 'caliber'
curdoc().title = "CoronaDB"

