(function () {
  window.createCustomMap = function (
    mapContainerId,
    lat,
    lng,
    destLat = null,
    destLng = null,
  ) {
    const mapElement = document.getElementById(mapContainerId);
    if (!mapElement) {
      console.error(`Element with id ${mapContainerId} not found.`);
      return;
    }

    console.log(`Initializing map with ID: ${mapContainerId}`);
    console.log(`Latitude: ${lat}, Longitude: ${lng}`);

    const mapLocation = { lat: lat, lng: lng };

    const mapInstance = new google.maps.Map(mapElement, {
      zoom: 12,
      center: mapLocation,
      gestureHandling: "auto",
    });

    new google.maps.Marker({
      position: mapLocation,
      map: mapInstance,
      title: "Your Location",
    });

    if (destLat !== null && destLng !== null) {
      console.log(
        `Destination Latitude: ${destLat}, Destination Longitude: ${destLng}`,
      );
      const destinationLocation = { lat: destLat, lng: destLng };

      new google.maps.Marker({
        position: destinationLocation,
        map: mapInstance,
        title: "Destination",
      });

      const line = new google.maps.Polyline({
        path: [mapLocation, destinationLocation],
        geodesic: true,
        strokeColor: "#FF0000",
        strokeOpacity: 1.0,
        strokeWeight: 2,
      });

      line.setMap(mapInstance);

      const transitLayer = new google.maps.TransitLayer();
      transitLayer.setMap(mapInstance);
    } else {
      console.log("Single location provided. Showing only this location.");
    }
  };
})();
