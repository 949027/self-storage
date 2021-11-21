from geopy import distance
from ugc.models import Warehouses


def get_distance_buttons(coordinates):
    coordinates = [coordinates["longitude"], coordinates["latitude"]]
    warehouses = Warehouses.objects.all()
    warehouse_buttons = []
    for warehouse in warehouses:
        warehouse_coordinates = [warehouse.lon, warehouse.lat]
        warehouse_distance = round(
            distance.distance(coordinates, warehouse_coordinates).km, 1)
        warehouse_buttons.append(f"{warehouse.name} {warehouse_distance} km.")
    return warehouse_buttons
