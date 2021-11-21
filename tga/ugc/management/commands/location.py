from geopy import distance
from ugc.models import Warehouses


def get_distance_buttons(coordinates):
    coordinates = [coordinates["latitude"], coordinates["longitude"]]
    warehouses = Warehouses.objects.all()
    warehouse_buttons = []
    for warehouse in warehouses:
        warehouse_coordinates = [warehouse.lat, warehouse.lon]
        warehouse_distance = round(
            distance.distance(coordinates, warehouse_coordinates[::-1]).km, 1)
        warehouse_buttons.append(f"{warehouse.name} {warehouse_distance} km.")
    return warehouse_buttons
