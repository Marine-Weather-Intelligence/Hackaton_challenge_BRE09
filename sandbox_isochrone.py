import datetime
 
import pandas as pd
import plotly.express as px
import requests
 
 
# Coordinates are provided as ``[latitude, longitude]`` pairs.
departure = [47.817, -4.065]
destination = [47.82, -4.16]
 
current_time = datetime.datetime.now()
# ``hours=0`` keeps the reference time explicit and easy to adjust for quick tests.
future_time = current_time + datetime.timedelta(hours=0)
timestamp = int(future_time.timestamp())
waypoints = []
# Example waypoint syntax:
# waypoints = [{'coord': [-20.5785, 55.1069], 'contourner': True, 'tribord': False}]
search_type = "global"  # ``global`` explores broadly; ``focus`` concentrates near the goal.
hours=24*7
 
def get_isochrone_route(departure, destination, wind_max, wave_max, motor_speed,
                        display, timestamp, waypoints, search_type):
  """Trigger a routing computation and optionally visualize the resulting isochrone.
 
  Args:
      url (str): Base host (without protocol) of the routing service instance to query.
      departure (list[float]): Latitude/longitude pair describing the starting point.
      destination (list[float]): Latitude/longitude pair describing the arrival point.
      wind_max (float): Maximum allowed true wind speed in knots.
      wave_max (float): Maximum significant wave height accepted for the route.
      motor_speed (float): Speed in knots when the engine is engaged.
      display (bool): If ``True`` render an interactive Plotly map, else return raw JSON.
      timestamp (int): UNIX timestamp of the desired departure time.
      waypoints (list[dict]): Optional intermediate waypoints with avoidance instructions.
      search_type (str): Either ``global`` or ``focus`` to control the solver behaviour.
 
  Returns:
      list[dict] | None: Isochrone point collection from the API when ``display`` is ``False``;
          otherwise ``None`` after showing the figure.
  """
 
  url_routing = 'https://weatherapitest-routing-api-zsdgpk-d50cd1-79-137-100-249.traefik.me/routing/call_MWI_routing'
 
  # Translate human-friendly search types to API-specific keywords.
  if search_type == "global":
    search_type = "std"
  elif search_type == "focus":
    search_type = "bary"
 
  # Compose the routing request combining route, boat, and weather constraints.
  form_data = {
    'route_parameters': {
                          'timestamp': timestamp,
                          'departure': departure,
                          'destination': destination,
                          'waypoints': waypoints
                        },
    'boat_parameters':  {
                          'id_boat': 8,
                          'TWA_max': 180,
                          'TWA_min': 45,
                          'TWS_upwind_max': wind_max,
                          'TWS_downwind_max': wind_max,
                          'swh_max': wave_max,
                          'gust_max': wind_max,
                          'engine': {'enabled': True, 'activation_threshold': 1, 'motor_speed': motor_speed},
                          'boat_type_general': 1
                        },
    'weather_parameters': {
                            'wind_model': 'AROME_0_01',
                            'wave_model': 'EWAM'
                          },
    'Supplier': 'MWI',
    'fillup': 0,
    'usecurrent': 'false',
    'tack_penalty': 0,
    'timestep': 600}
 
  # Kick off the heavy routing computation and surface HTTP errors immediately.
  response_routing = requests.post(url_routing, json=form_data, verify=False)
  response_routing.raise_for_status()
 
  url_isochrone = f'https://weatherapitest-routing-api-zsdgpk-d50cd1-79-137-100-249.traefik.me/routing/get_iso_std?method={search_type}'
 
  # Retrieve the generated isochrone once the routing job is scheduled server-side.
  response_isochrone = requests.get(url_isochrone, verify=False)
  response_isochrone.raise_for_status()
 
  if display:
    df = pd.DataFrame(response_isochrone.json())
 
    fig = px.scatter_mapbox(
        df,
        lat="Lat",
        lon="Lon",
        color="Layer",  # Distinguish isochrone layers visually.
        hover_data=["speed", "zone", "windModel", "waveModel"],
        color_continuous_scale="Viridis",
        zoom=8,
        height=600
    )
 
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0}, title="Isochrone points on map")
 
    fig.show()
 
  return response_isochrone.json()
 
 
if __name__ == "__main__":
  # Execute an example local request when the module is run directly.
  iso=get_isochrone_route(departure, destination, 50, 10, 3, True, timestamp, waypoints, search_type)
  print(iso)