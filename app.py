# Import dependencies
import streamlit as st
import streamlit.components.v1 as components
import xarray as xr
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import sys
from utils.read_data_utils import load_data_from_aws
from utils.plotting_utils import get_plot_settings_by_var

# Plotting dependencies 
import cartopy.crs as ccrs
import hvplot.xarray
import holoviews as hv
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

# Helps avoid some weird issues with the polar projection 
from cartopy.mpl.geoaxes import GeoAxes
GeoAxes._pcolormesh_patched = Axes.pcolormesh

# Silence warnings
import logging
logging.getLogger("param").setLevel(logging.CRITICAL)

# -------------- SET UP THE APP --------------

# Set page configuration
app_title = "ICESat-2 data dashboard"
st.set_page_config(
    page_title = app_title, # This will appear on the tab  
    page_icon = ":penguin:", 
    layout = "wide"
)
# Title the app
# I think this looks kind of ugly so I left it out 
# It's quite large 
# st.title(app_title)

def make_map_bokeh(data, variable="ice_thickness", time="Jan-01 2019", dynamic=False): 
    """Make a basic map of the data 
    
    Args: 
        data (xr.Dataset): data with all variables and timesteps
        variable (str, optional): valid variable (default to "ice_thickness")
        time (datetime or string, optional): valid time selection (default to Jan-01 2019)
        dynamic (boolean, option): return plot that dynamically updates? (default to False)
    Regards: 
        arctic_map (Holomap): map 
        
    """
    sys.stdout.write("\nMaking Arctic map...")

    # Get data for just the input variable 
    to_plot = data[variable]

    # Get colorbar limits, cmap, and clabel 
    # This is a helper function in plotting_utils.py 
    clim, cmap, clabel = get_plot_settings_by_var(variable, to_plot)

    # Get data for input time 
    # The plot will be displayed even if there's no data for that month 
    # This makes it so the time slider works 
    # If no data for that month, all values are replaced with nan and an empty map is shown
    if time != "no data": 
        to_plot = to_plot.sel(time=time)
    else: 
        to_plot = to_plot.isel(time=0)
        to_plot = to_plot.where(to_plot == -9999.) # Replace all values with nan  
    
    # Set a descriptive title
    title = "time: {0}; variable: {1}".format(time, to_plot.long_name)

    # Make map with inputs 
    arctic_map = to_plot.hvplot.quadmesh(
        y="latitude", x="longitude", 
        clim=clim, clabel=clabel, 
        projection=ccrs.NorthPolarStereo(central_longitude=-45),
        features=["coastline"], 
        cmap=cmap,
        project=True, 
        ylim=(60,90),
        dynamic=dynamic, 
        title=title,
    )
    sys.stdout.write("complete!")
    return arctic_map

def main(is2_ds): 
    """Main function to create the app 

    Args: 
        is2_ds (xr.Dataset): preloaded input data 
    Return: 
        streamlit app generated 
    """

    # -------- SIDEBAR INFORMATION --------
    st.sidebar.markdown("Choose your date and variable of interest, and the map will automatically update.")

    # -------- USER OPTIONS FOR TIME --------
    # Valid time options loaded from the dataset, then converted from string to datetime object
    time_options = pd.to_datetime(is2_ds.time.values).to_pydatetime()

    # Make the time slider in the streamlit sidebar 
    # Every month of the year is shown even though there's no summer data 
    # This has to be done in an unintuitive way because of a lack of flexibility from streamlit 
    # streamlit only accepts datetime objects for min_value and max_value and timedelta objects for step
    chosen_time = st.sidebar.slider(
        "Time",
        min_value=time_options[0], 
        max_value=time_options[-1],
        step=timedelta(days=31), # Approximately 1 month. timedelta object has no option for month
        format="MMM YYYY" # Only month and year are shown to the user 
    ).strftime("%b %Y")

    # Input time to feed to the mapping function 
    # Will be set to "no data" if a month is chosen on the time slider that there is no data for 
    # i.e June will be set to "no data"
    map_input_time = chosen_time if pd.to_datetime(chosen_time) in time_options else "no data"

    # -------- USER OPTIONS FOR VARIABLE --------
    # A subset of the total variable options.
    # I just picked variables I thought users might be interested in seeing
    var_options = [
        'freeboard','freeboard_int','ice_thickness',
        'ice_thickness_int','ice_thickness_unc','ice_type','mean_day_of_month',
        'num_segments','sea_ice_conc','snow_depth','snow_depth_int'
    ]

    # Descriptive long names for each of the variable options 
    # i.e "sea ice thickness uncertainty" (long_name) is shown as an option instead of "ice_thickness_unc" 
    # I did this instead of using the shorter variable string since its more user-friendly 
    var_options_long_name = [
        is2_ds[var].long_name for var in var_options
    ] 

    # Dict of long name : variable name to make accessing easier
    var_dict = dict(zip(var_options_long_name, var_options))

    # Show variable  options in streamlit sidebar 
    chosen_var = st.sidebar.selectbox("Variable", var_options_long_name)

    # Input variable sent to the mapping function is the variable name, not the long name 
    # i.e "ice_thickness_unc" instead of "ice thickness uncertainty"
    map_input_var = var_dict[chosen_var]

    # Lastly, the longer description of the variable is shown below the selected variable 
    # I thought this was nice since it gives users a better idea of the variable 
    var_description = st.sidebar.markdown(is2_ds[map_input_var].description)

    # -------- WITH THE SELECTED OPTIONS, MAKE THE ARCTIC MAP --------
    arctic_map = make_map_bokeh(
        data=is2_ds, # All the data 
        variable=map_input_var, # User-selected variable
        time=map_input_time, # User-selected time
        dynamic=False # Do not dynamically update the map 
    )

    # Display map in app
    # Render to bokeh
    arctic_map = hv.render(arctic_map, backend="bokeh")
    st.bokeh_chart(arctic_map, use_container_width=False)

if __name__ == '__main__':
    # This is run each time the app is spun up 
    # The data is cached so that it isn't reloaded any time the user changes the variable/time
    is2_ds = load_data_from_aws()
    main(is2_ds)