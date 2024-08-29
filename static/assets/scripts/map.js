(function () {
  window.createCustomMap = function (mapContainerId, lat, lng) {
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
    });

    const transitLayer = new google.maps.TransitLayer();
    transitLayer.setMap(mapInstance);
  };
})();
