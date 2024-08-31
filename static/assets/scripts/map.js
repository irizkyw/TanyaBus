(function () {
  window.createCustomMap = function (
    mapContainerId,
    lat,
    lng,
    destLat = null,
    destLng = null,
    busData = null,
    updateInterval = 10000,
    busDataUrl = null,
    kmlUrl = null,
  ) {
    const mapElement = document.getElementById(mapContainerId);
    if (!mapElement) {
      console.error(`Element with id ${mapContainerId} not found.`);
      return;
    }

    console.log(`Initializing map with ID: ${mapContainerId}`);
    console.log(`Latitude: ${lat}, Longitude: ${lng}`);

    const mapLocation = { lat: lat, lng: lng };

    const grayscaleStyle = [
      // Your grayscale style settings
    ];

    const mapInstance = new google.maps.Map(mapElement, {
      zoom: 12,
      center: mapLocation,
      gestureHandling: "auto",
      disableDefaultUI: true,
      styles: grayscaleStyle,
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

      const directionsService = new google.maps.DirectionsService();
      const directionsRenderer = new google.maps.DirectionsRenderer();
      directionsRenderer.setMap(mapInstance);

      const request = {
        origin: mapLocation,
        destination: destinationLocation,
        travelMode: google.maps.TravelMode.TRANSIT,
      };

      directionsService.route(request, (result, status) => {
        if (status === google.maps.DirectionsStatus.OK) {
          directionsRenderer.setDirections(result);
        } else {
          console.error("Directions request failed due to " + status);
        }
      });
    } else {
      console.log("Single location provided. Showing only this location.");
    }

    const transitLayer = new google.maps.TransitLayer();
    transitLayer.setMap(mapInstance);

    // Uncomment and implement bus data functionality if needed
    // function addBusMarkers(busData) { /* Your existing code */ }
    // if (busData) { addBusMarkers(busData); }
    // if (busDataUrl) {
    //   setInterval(async () => {
    //     try {
    //       const response = await fetch(busDataUrl);
    //       if (!response.ok) { throw new Error("Network response was not ok"); }
    //       const newBusData = await response.json();
    //       addBusMarkers(newBusData);
    //     } catch (error) {
    //       console.error("Error fetching bus data:", error);
    //     }
    //   }, updateInterval);
    // }
  };
})();
