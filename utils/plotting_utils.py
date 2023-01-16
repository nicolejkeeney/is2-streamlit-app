import numpy as np

def compute_vmin_vmax(da): 
    """
    Used to find the 1st and 99th percentile of values for an input DataArray
    Makes it so the colorbar is standardized across timesteps 
    """
    vmin = np.nanpercentile(da.values, 1)
    vmax = np.nanpercentile(da.values, 99)
    return vmin, vmax 

def get_plot_settings_by_var(variable, xr_da):
    """Set colobar boundaries, colormap, and colorbar label depending on variable
    Args: 
        variable (str): valid variable name 
        xr_da (xr.DataArray): data corresponding to the input variable (not a Dataset of all variables!)
    Returns: 
        clim (tuple): colorbar limits
        cmap (str): colormap 
        clabel (str): variable long name and units 
    """
    if variable in ["ice_thickness","ice_thickness_int"]: 
        clim = (0,4)
        cmap = "viridis"
    elif variable in ["freeboard","freeboard_int"]: 
        clim = (0,0.8)
        cmap = "YlOrRd"
    elif variable in ["ice_type"]: 
        clim = (0,1)
        cmap = "YlOrRd"
    elif variable in ["snow_depth","snow_depth_int"]: 
        clim = (0,0.5)
        cmap = "inferno"
    elif variable in ["snow_density"]: 
        clim = (240,330)
        cmap = "GnBu"
    elif variable in ["sea_ice_conc"]: 
        clim = (0,1)
        cmap = "Blues_r"
    else: # Manually compute colorbar limits using vmin and vmax 
        vmin, vmax = compute_vmin_vmax(xr_da)
        clim = (vmin,vmax)
        cmap = "viridis"

    # Set colorbar label 
    if variable == "ice_type": 
        # Long name and units are really long for this variable 
        # Set them here to be shorter and look nicer in the plot 
        clabel = "Sea ice type (0 = FYI, 1 = MYI)" 
    else: 
        # Otherwise make the label say "variable longname (units)"
        clabel = xr_da.long_name + " (" + xr_da.units + ")"
    return clim, cmap, clabel