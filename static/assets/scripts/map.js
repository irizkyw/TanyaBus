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

    // TODO: data buss
    // function addBusMarkers(busData) {
    //   if (busData && Array.isArray(busData)) {
    //     console.log(`Adding ${busData.length} bus markers to the map.`);
    //     busData.forEach((bus) => {
    //       const busPosition = {
    //         lat: parseFloat(bus.gps_position.lat),
    //         lng: parseFloat(bus.gps_position.lng),
    //       };

    //       const busMarker = new google.maps.Marker({
    //         position: busPosition,
    //         map: mapInstance,
    //         title: bus.vehicle_no,
    //         icon: {
    //           url: "bus-icon.png",
    //           scaledSize: new google.maps.Size(32, 32),
    //         },
    //       });

    //       const infoWindow = new google.maps.InfoWindow({
    //         content: `
    //           <div>
    //             <h4>${bus.vehicle_no}</h4>
    //             <p>Speed: ${bus.gps_position.speed} km/h</p>
    //             <p>Odometer: ${
    //               bus.gps_position.sensors.find((s) => s.name === "odometer")
    //                 .value
    //             }</p>
    //             <p>Driver: ${
    //               bus.gps_position.sensors.find((s) => s.name === "driver")
    //                 .value
    //             }</p>
    //           </div>
    //         `,
    //       });

    //       busMarker.addListener("click", () => {
    //         infoWindow.open(mapInstance, busMarker);
    //       });
    //     });
    //   } else {
    //     console.log("No bus data provided.");
    //   }
    // }

    // if (busData) {
    //   addBusMarkers(busData);
    // }

    // if (busDataUrl) {
    //   setInterval(async () => {
    //     try {
    //       const response = await fetch(busDataUrl);
    //       if (!response.ok) {
    //         throw new Error("Network response was not ok");
    //       }
    //       const newBusData = await response.json();
    //       addBusMarkers(newBusData);
    //     } catch (error) {
    //       console.error("Error fetching bus data:", error);
    //     }
    //   }, updateInterval);
    // }
  };
})();
