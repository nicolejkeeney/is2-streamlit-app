# Import dependencies
import streamlit as st
import streamlit.components.v1 as components
import xarray as xr
import pandas as pd
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

def make_map_html(data, variable): 
    """Make a basic map of the data 
    
    Args: 
        data (xr.Dataset): data with all variables and timesteps
        variable (str): variable to plot 
    Regards: 
        arctic_map (Holomap): map 
        
    """
    sys.stdout.write("\nMaking Arctic map...")

    to_plot = data[variable]
    # When developing sometimes I just limit the number of timesteps 
    # Very slow to load with all timesteps 
    to_plot = to_plot.isel(time=[0,1,2,3,4,5,6])
    clim, cmap, clabel = get_plot_settings_by_var(variable, to_plot)

    # Make map with inputs 
    arctic_map = to_plot.hvplot.quadmesh(
        y="latitude", x="longitude", 
        clim=clim, clabel=clabel, 
        projection=ccrs.NorthPolarStereo(central_longitude=-45),
        features=["coastline"], 
        cmap=cmap,
        project=True, 
        ylim=(60,90),
    )
    hv.output(widget_location="bottom") # Put time slider below the map 
    sys.stdout.write("complete!")
    
    return arctic_map

def main(is2_ds): 
    """Main function to create the app 

    Args: 
        is2_ds (xr.Dataset): preloaded input data 
    Return: 
        streamlit app generated 
    """

    # Copied from app.py
    # See app.py for more documentation on this part  
    st.sidebar.markdown("Choose your date and variable of interest, and the map will automatically update.")
    var_options = [
        'freeboard','freeboard_int','ice_thickness',
        'ice_thickness_int','ice_thickness_unc','ice_type','mean_day_of_month',
        'num_segments','sea_ice_conc','snow_depth','snow_depth_int'
    ]
    var_options_long_name = [
        is2_ds[var].long_name for var in var_options
    ] 
    var_dict = dict(zip(var_options_long_name, var_options))
    chosen_var = st.sidebar.selectbox("Variable", var_options_long_name)
    map_input_var = var_dict[chosen_var]
    var_description = st.sidebar.markdown(is2_ds[map_input_var].description)

    # -------- WITH THE SELECTED OPTIONS, MAKE THE ARCTIC MAP --------
    arctic_map = make_map_html(
        data=is2_ds,
        variable=map_input_var
    )

    # Display map in app
    # Render to html
    renderer = hv.renderer('bokeh')
    html = renderer.static_html(arctic_map)
    components.html(html, height=600)

if __name__ == '__main__':
    # This is run each time the app is spun up 
    # The data is cached so that it isn't reloaded any time the user changes the variable/time
    is2_ds = load_data_from_aws()
    main(is2_ds)